import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import db
from app.services.agent_hub import agent_hub
from app.services.bss_oss import bss_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db_state():
    """Ensure clean test data before each test."""
    db.reseed_defaults(force=True)
    bss_service.reload_from_db()
    yield


def test_e2e_inbound_registered_ani_balance_inquiry():
    """
    E2E Flow 1: Caller dials from registered mobile number (+15550192834).
    The assistant identifies Jordan Rivera, resolves balance inquiry via self-service,
    and logs an accurate CDR to SQLite.
    """
    call_id = "e2e-reg-ani-01"
    session_id = f"vapi-{call_id}"
    customer_ani = "+15550192834"

    # 1. Call initiated (status update)
    res_status = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "status-update",
            "status": "in-progress",
            "call": {"id": call_id, "customer": {"number": customer_ani}}
        }
    })
    assert res_status.status_code == 200

    # 2. Tool call: Assistant looks up account using caller's phone or account number 1001
    res_tool = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "tool-calls",
            "call": {"id": call_id, "customer": {"number": customer_ani}},
            "toolCallList": [
                {
                    "id": "tc-balance-1",
                    "type": "function",
                    "function": {
                        "name": "lookup_account",
                        "arguments": {"account_number": "1001"}
                    }
                }
            ]
        }
    })
    assert res_tool.status_code == 200
    res_data = res_tool.json()["results"][0]["result"]
    assert "Account Found" in res_data
    assert "Jordan Rivera" in res_data
    assert "#1001" in res_data
    assert "$142.50" in res_data

    # 3. Live transcript turn streaming
    res_trans = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "transcript",
            "transcriptType": "final",
            "role": "assistant",
            "transcript": "Your current balance is $142.50 due on September 20th.",
            "timestamp": "1789566000000",
            "call": {"id": call_id, "customer": {"number": customer_ani}}
        }
    })
    assert res_trans.status_code == 200

    # 4. End of call report
    res_end = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "end-of-call-report",
            "call": {"id": call_id, "customer": {"number": customer_ani}},
            "durationSeconds": 42,
            "transcript": "Caller checked their account balance. Assistant provided $142.50.",
            "summary": "Balance inquiry resolved."
        }
    })
    assert res_end.status_code == 200

    # 5. Verify CDR in SQLite
    cdrs = db.get_recent_cdrs(10)
    cdr = next((c for c in cdrs if c["session_id"] == session_id), None)
    assert cdr is not None
    assert cdr["account_number"] == "1001"
    assert cdr["customer_name"] == "Jordan Rivera"
    assert cdr["final_state"] == "RESOLVED_CONTAINED"
    assert cdr["escalation_reason"] is None


def test_e2e_inbound_unknown_mobile_with_spoken_account():
    """
    E2E Flow 2: Caller dials from unlinked personal mobile (+19349437428).
    Assistant asks for account number, user speaks "1004" (Sam Taylor).
    Assistant looks up account and resolves inquiry.
    """
    call_id = "e2e-unlinked-ani-02"
    session_id = f"vapi-{call_id}"
    customer_ani = "+19349437428"

    res_tool = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "tool-calls",
            "call": {"id": call_id, "customer": {"number": customer_ani}},
            "toolCallList": [
                {
                    "id": "tc-lookup-1004",
                    "type": "function",
                    "function": {
                        "name": "lookup_account",
                        "arguments": {"account_number": "1004"}
                    }
                }
            ]
        }
    })
    assert res_tool.status_code == 200
    res_data = res_tool.json()["results"][0]["result"]
    assert "Sam Taylor" in res_data
    assert "#1004" in res_data
    assert "$45.00" in res_data

    # End of call report should link to Sam Taylor (1004) even though caller ANI was unlinked
    res_end = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "end-of-call-report",
            "call": {"id": call_id, "customer": {"number": customer_ani}},
            "durationSeconds": 55,
            "transcript": "Caller verified account 1004.",
            "summary": "Account balance checked."
        }
    })
    assert res_end.status_code == 200

    cdrs = db.get_recent_cdrs(10)
    cdr = next((c for c in cdrs if c["session_id"] == session_id), None)
    assert cdr is not None
    assert cdr["account_number"] == "1004"
    assert cdr["customer_name"] == "Sam Taylor"
    assert cdr["final_state"] == "RESOLVED_CONTAINED"


def test_e2e_self_service_bill_payment_flow():
    """
    E2E Flow 3: Caller looks up account 1004 ($45 balance) and pays $45.
    Verifies that session context automatically supplies account number to process_bill_payment,
    and updates balance in database to 0.00.
    """
    call_id = "e2e-pay-03"
    session_id = f"vapi-{call_id}"
    customer_ani = "+15550101001"

    # Step 1: Look up account
    client.post("/api/vapi/webhook", json={
        "message": {
            "type": "tool-calls",
            "call": {"id": call_id, "customer": {"number": customer_ani}},
            "toolCallList": [
                {
                    "id": "tc-look-3",
                    "type": "function",
                    "function": {
                        "name": "lookup_account",
                        "arguments": {"account_number": "1004"}
                    }
                }
            ]
        }
    })

    # Step 2: Pay full balance (omit account_number to verify session inheritance)
    res_pay = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "tool-calls",
            "call": {"id": call_id, "customer": {"number": customer_ani}},
            "toolCallList": [
                {
                    "id": "tc-pay-3",
                    "type": "function",
                    "function": {
                        "name": "process_bill_payment",
                        "arguments": {"amount": 45.0}
                    }
                }
            ]
        }
    })
    assert res_pay.status_code == 200
    pay_data = res_pay.json()["results"][0]["result"]
    assert "Payment successful" in pay_data
    assert "$45.00" in pay_data

    # Verify balance updated in BSS / SQLite
    acc = db.get_subscriber_by_account("1004")
    assert acc["current_balance"] == 0.0


def test_e2e_router_diagnostics_and_reset():
    """
    E2E Flow 4: Caller with degraded line requests router reboot.
    Assistant executes diagnose_and_reboot_router.
    """
    call_id = "e2e-reboot-04"
    res = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "tool-calls",
            "call": {"id": call_id, "customer": {"number": "+15550173399"}},
            "toolCallList": [
                {
                    "id": "tc-reboot-4",
                    "type": "function",
                    "function": {
                        "name": "diagnose_and_reboot_router",
                        "arguments": {"account_number": "1003"}
                    }
                }
            ]
        }
    })
    assert res.status_code == 200
    res_data = res.json()["results"][0]["result"]
    assert "Router reset signal sent" in res_data
    assert "ONLINE_RESTORED" in res_data


def test_e2e_network_outage_triage():
    """
    E2E Flow 5: Outage checks for affected area (98101) vs normal area (94107).
    """
    call_id = "e2e-outage-05"

    # Outage area
    res_outage = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "tool-calls",
            "call": {"id": call_id, "customer": {}},
            "toolCallList": [
                {
                    "id": "tc-outage-5a",
                    "type": "function",
                    "function": {
                        "name": "check_network_outage",
                        "arguments": {"zip_code": "98101"}
                    }
                }
            ]
        }
    })
    assert "Active outage in Downtown Seattle Metro" in res_outage.json()["results"][0]["result"]

    # Normal area
    res_normal = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "tool-calls",
            "call": {"id": call_id, "customer": {}},
            "toolCallList": [
                {
                    "id": "tc-outage-5b",
                    "type": "function",
                    "function": {
                        "name": "check_network_outage",
                        "arguments": {"zip_code": "94107"}
                    }
                }
            ]
        }
    })
    assert "operating normally" in res_normal.json()["results"][0]["result"]


def test_e2e_knowledge_base_esim_inquiry():
    """
    E2E Flow 6: Telecom knowledge base lookup for eSIM activation.
    """
    call_id = "e2e-kb-06"
    res = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "tool-calls",
            "call": {"id": call_id, "customer": {}},
            "toolCallList": [
                {
                    "id": "tc-kb-6",
                    "type": "function",
                    "function": {
                        "name": "search_telecom_knowledge",
                        "arguments": {"query": "how do I activate my eSIM QR code?"}
                    }
                }
            ]
        }
    })
    assert res.status_code == 200
    res_text = res.json()["results"][0]["result"]
    assert "eSIM" in res_text


def test_e2e_out_of_scope_escalation_to_human_agent():
    """
    E2E Flow 7: Issue is out of scope / customer requests human representative.
    Assistant executes transfer_to_agent:
    - Passes verified account details & escalation reason
    - agent_hub receives escalation payload with full customer context
    - End-of-call report records ESCALATED_TO_AGENT with accurate reason
    """
    call_id = "e2e-esc-07"
    session_id = f"vapi-{call_id}"
    customer_ani = "+19349437428"  # Mobile phone

    # Step 1: Caller identified as Elena Vance (1002)
    client.post("/api/vapi/webhook", json={
        "message": {
            "type": "tool-calls",
            "call": {"id": call_id, "customer": {"number": customer_ani}},
            "toolCallList": [
                {
                    "id": "tc-lookup-7",
                    "type": "function",
                    "function": {
                        "name": "lookup_account",
                        "arguments": {"account_number": "1002"}
                    }
                }
            ]
        }
    })

    # Step 2: Complex dispute cannot be resolved by AI -> transfer to agent
    res_esc = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "tool-calls",
            "call": {"id": call_id, "customer": {"number": customer_ani}},
            "toolCallList": [
                {
                    "id": "tc-esc-7",
                    "type": "function",
                    "function": {
                        "name": "transfer_to_agent",
                        "arguments": {
                            "reason": "Dispute over unbilled international roaming charges exceeding credit limit",
                            "account_number": "1002"
                        }
                    }
                }
            ]
        }
    })
    assert res_esc.status_code == 200
    assert "specialist" in res_esc.json()["results"][0]["result"]

    # Step 3: Verify agent_hub queued the escalation with complete profile
    pending = agent_hub.get_pending()
    esc = next((p for p in pending if session_id in p["session_id"]), None)
    assert esc is not None
    assert esc["customer_profile"]["account_number"] == "1002"
    assert esc["customer_profile"]["customer_name"] == "Elena Vance"
    assert "roaming" in esc["resolution_summary"]["failure_or_escalation_reason"]

    # Step 4: End-of-call report logs ESCALATED_TO_AGENT
    res_end = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "end-of-call-report",
            "call": {"id": call_id, "customer": {"number": customer_ani}},
            "durationSeconds": 85,
            "transcript": "Caller disputed charges and was transferred to human specialist.",
            "summary": "Escalated billing dispute."
        }
    })
    assert res_end.status_code == 200

    cdrs = db.get_recent_cdrs(10)
    cdr = next((c for c in cdrs if c["session_id"] == session_id), None)
    assert cdr is not None
    assert cdr["account_number"] == "1002"
    assert cdr["customer_name"] == "Elena Vance"
    assert cdr["final_state"] == "ESCALATED_TO_AGENT"
    assert "roaming" in cdr["escalation_reason"]

    # Clean up agent_hub singleton queue
    agent_hub._pending_escalations.pop(session_id, None)


@pytest.mark.asyncio
async def test_e2e_vapi_voice_exchange_bridge():
    """
    E2E Flow 8: User calls from an Indian mobile phone (+917661881708) to Vapi AI number.
    Transfers call to agent. Agent accepts on laptop portal and full two-way voice
    exchange operates:
    1. Vapi sends monitor.controlUrl in webhook.
    2. VapiCallerAdapter is registered in agent_hub.
    3. Agent accepts call -> Vapi receives 'say' announcement.
    4. Agent sends live speech -> Vapi receives 'say' to speak into phone ear.
    5. Caller speaks -> Server synthesizes TTS audio and relays CALLER_LIVE_SPEECH to agent.
    6. Agent bridges to physical phone -> Vapi receives 'transfer' command.
    7. Agent ends call -> Vapi receives 'say' goodbye and terminates call.
    """
    import asyncio
    from unittest.mock import AsyncMock, patch
    from app.services.vapi_adapter import VapiCallerAdapter

    call_id = "vapi-call-indian-mobile-99"
    session_id = f"vapi-{call_id}"
    customer_ani = "+917661881708"
    mock_control_url = "https://phone-call-websocket.vapi.ai/mock/control"

    # 1. Inbound call initiated with monitor.controlUrl
    res_status = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "status-update",
            "status": "in-progress",
            "call": {
                "id": call_id,
                "customer": {"number": customer_ani},
                "monitor": {
                    "controlUrl": mock_control_url,
                    "listenUrl": "wss://phone-call-websocket.vapi.ai/mock/listen"
                }
            }
        }
    })
    assert res_status.status_code == 200

    # Verify adapter was registered in agent_hub
    adapter = agent_hub._caller_websockets.get(session_id)
    assert adapter is not None
    assert isinstance(adapter, VapiCallerAdapter)
    assert adapter.control_url == mock_control_url

    # 2. Caller asks to transfer to human agent
    res_esc = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "tool-calls",
            "call": {
                "id": call_id,
                "customer": {"number": customer_ani},
                "monitor": {"controlUrl": mock_control_url}
            },
            "toolCallList": [
                {
                    "id": "tc-esc-mob-1",
                    "type": "function",
                    "function": {
                        "name": "transfer_to_agent",
                        "arguments": {"reason": "Customer requested human specialist from mobile phone"}
                    }
                }
            ]
        }
    })
    assert res_esc.status_code == 200
    assert "specialist" in res_esc.json()["results"][0]["result"].lower()

    # 3. Agent desktop receives pop-up and accepts call
    control_calls = []

    async def mock_post_control(payload):
        control_calls.append(payload)
        return True

    adapter.post_control = mock_post_control

    accept_res = client.post("/api/agent/accept", json={
        "session_id": session_id,
        "agent_id": "agent-sarah-j"
    })
    assert accept_res.status_code == 200
    assert accept_res.json()["success"] is True

    # Check agent announcement was sent to Vapi controlUrl
    assert len(control_calls) >= 1
    announcement = control_calls[0]
    assert announcement["type"] == "say"
    assert "Sarah J" in announcement["content"]
    assert announcement["endCallAfterSpoken"] is False

    # 4. Agent speaks to caller via live speech (mic or quick responses)
    await agent_hub.relay_agent_to_caller(session_id, {
        "type": "AGENT_LIVE_SPEECH",
        "session_id": session_id,
        "text": "Hello, this is Sarah from NexusFiber. I see your account details here. How can I help?"
    })
    assert len(control_calls) >= 2
    agent_msg = control_calls[1]
    assert agent_msg["type"] == "say"
    assert "Sarah from NexusFiber" in agent_msg["content"]

    # 5. Mobile caller speaks on their phone -> Vapi sends transcript
    relayed_messages = []

    class MockAgentWS:
        async def send_text(self, text):
            relayed_messages.append(json.loads(text))

    mock_agent_conn = MockAgentWS()
    agent_hub._active_connections.append(mock_agent_conn)

    try:
        res_trans = client.post("/api/vapi/webhook", json={
            "message": {
                "type": "transcript",
                "transcriptType": "final",
                "role": "user",
                "transcript": "My gigabit fiber has no internet connection.",
                "timestamp": 1700000000000,
                "call": {
                    "id": call_id,
                    "customer": {"number": customer_ani},
                    "monitor": {"controlUrl": mock_control_url}
                }
            }
        })
        assert res_trans.status_code == 200

        # Verify CALLER_LIVE_SPEECH was relayed to agent desktop with audio
        speech_events = [m for m in relayed_messages if m.get("type") == "CALLER_LIVE_SPEECH"]
        assert len(speech_events) > 0
        speech_ev = speech_events[0]
        assert speech_ev["text"] == "My gigabit fiber has no internet connection."
        assert speech_ev["caller_ani"] == customer_ani
        assert speech_ev.get("audio_base64") is not None  # TTS voice synthesized for agent speakers

    finally:
        if mock_agent_conn in agent_hub._active_connections:
            agent_hub._active_connections.remove(mock_agent_conn)

    # 6. Agent clicks "Bridge to Physical Phone"
    await agent_hub.relay_agent_to_caller(session_id, {
        "type": "AGENT_TRANSFER_PHONE",
        "session_id": session_id,
        "phone_number": "+917661881708"
    })
    transfer_cmds = [c for c in control_calls if c.get("type") == "transfer"]
    assert len(transfer_cmds) == 1
    assert transfer_cmds[0]["destination"]["number"] == "+917661881708"

    # 7. Agent ends the call
    await agent_hub.relay_agent_to_caller(session_id, {
        "type": "AGENT_DISCONNECT",
        "session_id": session_id
    })
    bye_cmds = [c for c in control_calls if c.get("type") == "say" and "ended this session" in c.get("content", "")]
    assert len(bye_cmds) == 1
    assert bye_cmds[0]["endCallAfterSpoken"] is True

    # 8. Call concludes cleanly
    res_end = client.post("/api/vapi/webhook", json={
        "message": {
            "type": "end-of-call-report",
            "call": {"id": call_id, "customer": {"number": customer_ani}},
            "durationSeconds": 120,
            "transcript": "Mobile call completed with live agent Sarah J.",
            "summary": "Live agent resolution via Vapi bridge."
        }
    })
    assert res_end.status_code == 200

    # Verify adapter was unregistered upon call completion
    assert session_id not in agent_hub._caller_websockets
    agent_hub.unregister_caller(session_id)
