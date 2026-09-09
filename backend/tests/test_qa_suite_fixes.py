import pytest
from app.models.schemas import CallState, IntentEnum, AuthStatus, EscalationPayload
from app.engine.state_machine import CallSessionStateMachine
from app.engine.orchestrator import DialogueOrchestrator
from app.services.agent_hub import agent_hub
from app.services.telemetry import telemetry_service
from app.engine.nlu_utils import is_affirmative, is_negative
from app.engine.intent_classifier import intent_classifier


def test_plan_flow_details_provided_to_upgrade_transition():
    session = CallSessionStateMachine(session_id="test-plan-details-upgrade", ani="+15550192834")
    session.get_greeting()

    # Turn 1: Inquire plan details
    resp1, state1, esc1 = session.process_turn("What plan am I on?")
    assert state1 == CallState.SUBFLOW_EXECUTION
    assert "GigaFiber 500 Ultra" in resp1 or "plan" in resp1.lower()
    assert esc1 is None

    # Turn 2: Ask for speed upgrade after hearing details
    resp2, state2, esc2 = session.process_turn("Can I upgrade to gigabit speed?")
    assert state2 == CallState.SUBFLOW_EXECUTION
    assert "Gigabit Pro 1000" in resp2
    assert esc2 is None

    # Turn 3: Express interest in upgrade
    resp3, state3, esc3 = session.process_turn("Yes, I want to upgrade")
    assert "authorizing an upgrade" in resp3.lower() or "$110.00" in resp3
    assert esc3 is None

    # Turn 4: Authorize and complete
    resp4, state4, esc4 = session.process_turn("Yes, I agree to this change")
    assert state4 == CallState.RESOLVED_CONTAINED
    assert "upgraded to Gigabit Pro 1000" in resp4
    assert esc4 is None


def test_plan_flow_details_provided_to_decline():
    session = CallSessionStateMachine(session_id="test-plan-details-decline", ani="+15550192834")
    session.get_greeting()

    # Turn 1: Inquire plan details
    resp1, state1, esc1 = session.process_turn("What plan am I on?")
    assert state1 == CallState.SUBFLOW_EXECUTION

    # Turn 2: Decline further changes
    resp2, state2, esc2 = session.process_turn("No, that's all, thank you")
    assert state2 == CallState.RESOLVED_CONTAINED
    assert "No changes have been made" in resp2 or "anything else" in resp2.lower()
    assert esc2 is None


def test_goodbye_closes_call_without_escalating():
    # English parting
    session_en = CallSessionStateMachine(session_id="test-bye-en", ani="+15550192834")
    session_en.get_greeting()
    resp_en, state_en, esc_en = session_en.process_turn("Goodbye")
    assert state_en == CallState.RESOLVED_CONTAINED
    assert esc_en is None
    assert session_en.consecutive_unrecognized == 0
    assert "wonderful day" in resp_en.lower() or "great day" in resp_en.lower()

    # Spanish parting
    session_es = CallSessionStateMachine(session_id="test-bye-es", ani="+15550192834")
    session_es.get_greeting()
    session_es.process_turn("Quiero hablar en español")
    resp_es, state_es, esc_es = session_es.process_turn("Adiós, muchas gracias")
    assert state_es == CallState.RESOLVED_CONTAINED
    assert esc_es is None
    assert session_en.consecutive_unrecognized == 0
    assert "excelente día" in resp_es.lower() or "gracias" in resp_es.lower()

    # Hindi parting
    session_hi = CallSessionStateMachine(session_id="test-bye-hi", ani="+15550192834")
    session_hi.get_greeting()
    session_hi.process_turn("Switch to Hindi")
    resp_hi, state_hi, esc_hi = session_hi.process_turn("अलविदा, धन्यवाद")
    assert state_hi == CallState.RESOLVED_CONTAINED
    assert esc_hi is None
    assert session_hi.consecutive_unrecognized == 0


def test_dtmf_1_and_2_confirmation_support():
    assert is_affirmative("1")
    assert is_negative("2")

    # Verify DTMF '1' confirms billing payment (using Marcus Brody who has a balance)
    session_dtmf_yes = CallSessionStateMachine(session_id="test-dtmf-yes", ani="+15550173399")
    session_dtmf_yes.get_greeting()
    resp_init, _, _ = session_dtmf_yes.process_turn("Pay bill now")
    assert "card ending in" in resp_init
    resp_confirm, state_confirm, _ = session_dtmf_yes.process_turn("1")
    assert state_confirm == CallState.RESOLVED_CONTAINED
    assert "Success" in resp_confirm or "TXN-" in resp_confirm

    # Verify DTMF '2' declines billing payment (reset Marcus balance or use another state machine with balance)
    from app.services.bss_oss import bss_service
    brody = bss_service.get_account_by_phone("+15550173399")
    if brody:
        brody.current_balance = 220.00
    session_dtmf_no = CallSessionStateMachine(session_id="test-dtmf-no", ani="+15550173399")
    session_dtmf_no.get_greeting()
    resp_init2, _, _ = session_dtmf_no.process_turn("Pay bill now")
    assert "card ending in" in resp_init2
    resp_declined, state_declined, _ = session_dtmf_no.process_turn("2")
    assert "no payment was processed" in resp_declined.lower()


def test_multilingual_escalation_prompt_spanish_and_hindi():
    # Spanish escalation
    session_es = CallSessionStateMachine(session_id="test-esc-es", ani="+15550192834")
    session_es.get_greeting()
    session_es.process_turn("Quiero hablar en español")
    resp_es, state_es, esc_es = session_es.process_turn("Quiero hablar con un representante")
    assert state_es == CallState.ESCALATING_TO_AGENT
    assert esc_es is not None
    assert "le estoy transfiriendo" in resp_es.lower() or "especialistas de atención" in resp_es.lower()
    assert "i am transferring you" not in resp_es.lower()

    # Hindi escalation
    session_hi = CallSessionStateMachine(session_id="test-esc-hi", ani="+15550192834")
    session_hi.get_greeting()
    session_hi.process_turn("Switch to Hindi")
    resp_hi, state_hi, esc_hi = session_hi.process_turn("मुझे एजेंट से बात करनी है")
    assert state_hi == CallState.ESCALATING_TO_AGENT
    assert esc_hi is not None
    assert "विशेषज्ञ" in resp_hi or "सहायता" in resp_hi
    assert "transferring" not in resp_hi.lower()


def test_telemetry_deduplication_on_repeated_resolutions():
    test_session = "session-dedup-qa-test"
    initial_count = len(telemetry_service._records)

    # First completion record
    telemetry_service.record_completed_call(
        session_id=test_session,
        ani="+15550192834",
        account_number="ACC-992014-X",
        customer_name="Jordan Rivera",
        intent="BILLING_INQUIRY",
        duration_sec=30,
        final_state="RESOLVED_CONTAINED"
    )
    assert len(telemetry_service._records) == initial_count + 1

    # Attach CSAT
    telemetry_service.record_csat(test_session, 5)
    matching = [r for r in telemetry_service._records if r["session_id"] == test_session]
    assert len(matching) == 1
    assert matching[0]["csat_rating"] == 5

    # Subsequent completion record on same session (e.g. parting turn before hangup)
    telemetry_service.record_completed_call(
        session_id=test_session,
        ani="+15550192834",
        account_number="ACC-992014-X",
        customer_name="Jordan Rivera",
        intent="BILLING_INQUIRY",
        duration_sec=35,
        final_state="RESOLVED_CONTAINED"
    )
    # Must update in place, NOT insert a duplicate row
    matching_after = [r for r in telemetry_service._records if r["session_id"] == test_session]
    assert len(matching_after) == 1
    assert matching_after[0]["duration_sec"] == 35
    assert matching_after[0]["csat_rating"] == 5
    assert len(telemetry_service._records) == initial_count + 1


def test_agent_hub_unregister_removes_pending_escalation():
    test_session = "session-hub-abandon-test"
    dummy_payload = EscalationPayload(
        session_id=test_session,
        ani="+15550192834",
        customer_profile={"customer_name": "Jordan Rivera"},
        call_context={"primary_intent": "AGENT_ESCALATION"},
        resolution_summary={"failure_or_escalation_reason": "EXPLICIT_AGENT_REQUEST"},
        recommended_agent_queue="GENERAL_CARE_TIER1",
        transcript_snippet=[]
    )
    agent_hub._pending_escalations[test_session] = dummy_payload
    assert test_session in agent_hub._pending_escalations

    # Caller disconnects and unregisters
    agent_hub.unregister_caller(test_session)
    assert test_session not in agent_hub._pending_escalations


@pytest.mark.asyncio
async def test_turn_response_contains_language_and_caller_account():
    # 1. Test language returned in TURN_RESPONSE on mid-call switch
    orch = DialogueOrchestrator("session-orch-test-1", "+15550192834")
    await orch.start_session()
    resp_lang = await orch.process_caller_utterance("Quiero hablar en español")
    assert resp_lang["type"] == "TURN_RESPONSE"
    assert resp_lang["language"] == "es-US"

    # 2. Test caller_account returned in TURN_RESPONSE on KBA verification
    orch_unreg = DialogueOrchestrator("session-orch-test-2", "+15559990000")
    await orch_unreg.start_session()
    resp_kba = await orch_unreg.process_caller_utterance("My zip code is 94107")
    assert resp_kba["type"] == "TURN_RESPONSE"
    assert resp_kba["caller_account"] is not None
    assert resp_kba["caller_account"]["customer_name"] == "Jordan Rivera"
    assert resp_kba["caller_account"]["auth_status"] == AuthStatus.KBA_VERIFIED.value
