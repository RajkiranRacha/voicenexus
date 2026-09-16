import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import db

client = TestClient(app)

def test_vapi_tool_calls_lookup_account():
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "call-vapi-test-1", "customer": {"number": "+15550192834"}},
            "toolCallList": [
                {
                    "id": "tc-101",
                    "type": "function",
                    "function": {
                        "name": "lookup_account",
                        "arguments": {"account_number": "ACC-992014-X"}
                    }
                }
            ]
        }
    }
    response = client.post("/api/vapi/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["toolCallId"] == "tc-101"
    assert "Jordan Rivera" in data["results"][0]["result"]
    assert "Current Balance:" in data["results"][0]["result"]

def test_vapi_tool_calls_process_payment():
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "call-vapi-test-2", "customer": {"number": "+15550192834"}},
            "toolCallList": [
                {
                    "id": "tc-102",
                    "type": "function",
                    "function": {
                        "name": "process_bill_payment",
                        "arguments": {"account_number": "ACC-992014-X", "amount": 20.0}
                    }
                }
            ]
        }
    }
    response = client.post("/api/vapi/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "Payment successful" in data["results"][0]["result"]

def test_vapi_tool_calls_telecom_knowledge():
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "call-vapi-test-3", "customer": {"number": "+15550192834"}},
            "toolCallList": [
                {
                    "id": "tc-103",
                    "type": "function",
                    "function": {
                        "name": "search_telecom_knowledge",
                        "arguments": {"query": "how to activate esim"}
                    }
                }
            ]
        }
    }
    response = client.post("/api/vapi/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "eSIM" in data["results"][0]["result"]

def test_vapi_end_of_call_report():
    payload = {
        "message": {
            "type": "end-of-call-report",
            "call": {"id": "call-vapi-test-4", "customer": {"number": "+19876543210"}},
            "durationSeconds": 75,
            "transcript": "Caller asked about bill balance and paid 20 dollars.",
            "summary": "Bill paid successfully"
        }
    }
    response = client.post("/api/vapi/webhook", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "completed"}

    # Verify written to SQLite
    cdrs = db.get_recent_cdrs(10)
    found = any("vapi-call-vapi" in c["session_id"] for c in cdrs)
    assert found is True

def test_vapi_spoken_digit_lookup():
    # Test looking up account with spoken word numbers e.g. "nine four one zero seven"
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "call-vapi-spoken-1", "customer": {"number": "+19998887777"}},
            "toolCallList": [
                {
                    "id": "tc-spoken-1",
                    "type": "function",
                    "function": {
                        "name": "lookup_account",
                        "arguments": {"zip_code": "nine four one zero seven"}
                    }
                }
            ]
        }
    }
    response = client.post("/api/vapi/webhook", json=payload)
    assert response.status_code == 200
    res = response.json()["results"][0]["result"]
    assert "Account Found" in res
    assert "Jordan Rivera" in res

def test_vapi_unregistered_caller_guidance():
    # Test unknown caller with no matching account
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "call-vapi-unreg-1", "customer": {"number": "+19990001111"}},
            "toolCallList": [
                {
                    "id": "tc-unreg-1",
                    "type": "function",
                    "function": {
                        "name": "lookup_account",
                        "arguments": {"phone_number": "+19990001111"}
                    }
                }
            ]
        }
    }
    response = client.post("/api/vapi/webhook", json=payload)
    assert response.status_code == 200
    res = response.json()["results"][0]["result"]
    assert "Account not found" in res
    assert "new service" in res

def test_vapi_transfer_to_agent_escalation():
    from app.services.agent_hub import agent_hub
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "call-vapi-esc-1", "customer": {"number": "+15550192834"}},
            "toolCallList": [
                {
                    "id": "tc-esc-1",
                    "type": "function",
                    "function": {
                        "name": "transfer_to_agent",
                        "arguments": {"reason": "Customer needs billing dispute resolution"}
                    }
                }
            ]
        }
    }
    response = client.post("/api/vapi/webhook", json=payload)
    assert response.status_code == 200
    res = response.json()["results"][0]["result"]
    assert "specialist" in res

    # Verify escalation was stored in agent_hub
    pending = agent_hub.get_pending()
    esc_item = next((p for p in pending if "call-vapi-esc-1" in p["session_id"]), None)
    assert esc_item is not None
    assert esc_item["call_context"].get("primary_intent") == "AGENT_ESCALATION"
    assert "customer_name" in esc_item["customer_profile"]
    assert "notes" in esc_item["resolution_summary"]

    # Clean up so singleton state doesn't affect other tests
    agent_hub._pending_escalations.pop("vapi-call-vapi-esc-1", None)

def test_admin_subscriber_crud():
    # 1. Upsert new subscriber
    sub_data = {
        "account_number": "ACC-TEST-99",
        "phone_number": "+15559998888",
        "customer_name": "Test User",
        "zip_code": "90210",
        "plan_name": "GigaFiber 500",
        "current_balance": 50.0
    }
    res = client.post("/api/admin/subscribers", json=sub_data)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 2. Verify in list
    list_res = client.get("/api/admin/subscribers")
    assert any(s["account_number"] == "ACC-TEST-99" for s in list_res.json())

    # 3. Delete subscriber
    del_res = client.delete("/api/admin/subscribers/ACC-TEST-99")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True


def test_vapi_lookup_account_numeric_1001():
    # 1. Pure numeric string "1001"
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "call-vapi-num-1", "customer": {}},
            "toolCallList": [
                {
                    "id": "tc-1001",
                    "type": "function",
                    "function": {
                        "name": "lookup_account",
                        "arguments": {"account_number": "1001"}
                    }
                }
            ]
        }
    }
    response = client.post("/api/vapi/webhook", json=payload)
    assert response.status_code == 200
    res = response.json()["results"][0]["result"]
    assert "Account Found" in res
    assert "Jordan Rivera" in res
    assert "#1001" in res


def test_vapi_lookup_account_aliases_and_types():
    # 2. Integer 1001
    payload_int = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "call-vapi-num-2", "customer": {}},
            "toolCallList": [
                {
                    "id": "tc-int",
                    "type": "function",
                    "function": {
                        "name": "lookup_account",
                        "arguments": {"account_number": 1001}
                    }
                }
            ]
        }
    }
    res_int = client.post("/api/vapi/webhook", json=payload_int)
    assert res_int.status_code == 200
    assert "Jordan Rivera" in res_int.json()["results"][0]["result"]

    # 3. Alias key 'identifier'
    payload_ident = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "call-vapi-num-3", "customer": {}},
            "toolCallList": [
                {
                    "id": "tc-ident",
                    "type": "function",
                    "function": {
                        "name": "lookup_account",
                        "arguments": {"identifier": "1004"}
                    }
                }
            ]
        }
    }
    res_ident = client.post("/api/vapi/webhook", json=payload_ident)
    assert res_ident.status_code == 200
    assert "Sam Taylor" in res_ident.json()["results"][0]["result"]

    # 4. Alias key 'accountNumber'
    payload_camel = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "call-vapi-num-4", "customer": {}},
            "toolCallList": [
                {
                    "id": "tc-camel",
                    "type": "function",
                    "function": {
                        "name": "lookup_account",
                        "arguments": {"accountNumber": "1002"}
                    }
                }
            ]
        }
    }
    res_camel = client.post("/api/vapi/webhook", json=payload_camel)
    assert res_camel.status_code == 200
    assert "Elena Vance" in res_camel.json()["results"][0]["result"]


def test_vapi_root_post_fallback():
    # Test POST directly to "/" (root URL)
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "call-root-test", "customer": {}},
            "toolCallList": [
                {
                    "id": "tc-root",
                    "type": "function",
                    "function": {
                        "name": "lookup_account",
                        "arguments": {"account_number": "1001"}
                    }
                }
            ]
        }
    }
    response = client.post("/", json=payload)
    assert response.status_code == 200
    res = response.json()["results"][0]["result"]
    assert "Account Found" in res
    assert "Jordan Rivera" in res


