import pytest
from app.models.schemas import CallState, IntentEnum, AuthStatus
from app.engine.state_machine import CallSessionStateMachine
from app.services.identity import identity_service
from app.services.bss_oss import bss_service
from app.services.telemetry import telemetry_service

def test_ani_passive_authentication():
    status, acc = identity_service.verify_ani("+15550192834")
    assert status == AuthStatus.ANI_MATCHED
    assert acc is not None
    assert acc.customer_name == "Jordan Rivera"

def test_billing_payment_promise_flow_with_confirmation():
    session = CallSessionStateMachine(session_id="test-session-1", ani="+15550192834")
    greeting = session.get_greeting()
    assert "Jordan Rivera" in greeting

    # Turn 1: Inquire balance and ask for payment arrangement
    resp1, state1, esc1 = session.process_turn("How much is my bill and can I set up a payment arrangement?")
    assert state1 == CallState.SUBFLOW_EXECUTION
    assert "$142.50" in resp1
    assert "What date" in resp1
    assert esc1 is None

    # Turn 2: State preferred date
    resp2, state2, esc2 = session.process_turn("I want to pay next Friday")
    assert "To confirm before I schedule" in resp2
    assert "next friday" in resp2.lower()
    assert esc2 is None

    # Turn 3: Confirm commitment
    resp3, state3, esc3 = session.process_turn("Yes, confirm that")
    assert state3 == CallState.RESOLVED_CONTAINED
    assert "Your payment arrangement for $142.50 has been scheduled" in resp3
    assert "PP-" in resp3
    assert esc3 is None

def test_out_of_scope_billing_escalation():
    session = CallSessionStateMachine(session_id="test-session-2", ani="+15550192834")
    session.get_greeting()

    # Turn 1: Ask for split payment across two cards (out-of-scope for automated IVR)
    resp, state, esc = session.process_turn("Can I split payment across two different credit cards?")
    assert state == CallState.ESCALATING_TO_AGENT
    assert esc is not None
    assert esc.resolution_summary["failure_or_escalation_reason"] == "OUT_OF_SCOPE_BILLING_REQUEST"
    assert esc.recommended_agent_queue == "CARE_BILLING_TIER1"
    assert esc.customer_profile["customer_name"] == "Jordan Rivera"

def test_outage_triage_flow():
    # +15550148821 is seeded in 98101 where an active outage exists
    session = CallSessionStateMachine(session_id="test-session-3", ani="+15550148821")
    session.get_greeting()

    resp, state, esc = session.process_turn("My internet is completely down")
    assert state == CallState.SUBFLOW_EXECUTION
    assert "confirmed service outage" in resp
    assert "automated text updates" in resp

    # Opt in to SMS alerts
    resp2, state2, esc2 = session.process_turn("Yes please")
    assert state2 == CallState.RESOLVED_CONTAINED
    assert "enrolled in SMS alerts" in resp2

def test_max_unrecognized_turns_triggers_escalation():
    session = CallSessionStateMachine(session_id="test-session-4", ani="+15550192834")
    session.get_greeting()

    # Attempt 1: gibberish
    resp1, state1, esc1 = session.process_turn("flibberty gibbet blorp")
    assert state1 == CallState.INTENT_ROUTING
    assert esc1 is None

    # Attempt 2: second unrecognized turn -> should safely escalate
    resp2, state2, esc2 = session.process_turn("more random nonsense words")
    assert state2 == CallState.ESCALATING_TO_AGENT
    assert esc2 is not None
    assert esc2.resolution_summary["failure_or_escalation_reason"] == "EXCEEDED_MAX_UNRECOGNIZED_TURNS"

def test_telemetry_calculation():
    summary = telemetry_service.get_summary()
    assert summary.total_calls >= 10
    assert summary.containment_rate_pct > 0
    assert summary.transfer_rate_pct > 0
    assert summary.avg_handle_time_automated_sec > 0

def test_unregistered_caller_kba_auth():
    # Calling from an unregistered ANI
    session = CallSessionStateMachine(session_id="test-session-unreg", ani="+15559990000")
    greeting = session.get_greeting()
    assert session.state == CallState.AUTH_CHALLENGE
    assert "don't recognize the phone number" in greeting or "account number or 5-digit billing ZIP" in greeting

    # Provide zip code 94107 (associated with Jordan Rivera)
    resp, state, esc = session.process_turn("My zip code is 94107")
    assert state == CallState.INTENT_ROUTING
    assert session.account is not None
    assert "Jordan Rivera" in resp
    assert session.account.auth_status == AuthStatus.KBA_VERIFIED

def test_direct_card_payment_flow():
    # Pre-registered subscriber Jordan Rivera
    session = CallSessionStateMachine(session_id="test-session-pay", ani="+15550192834")
    session.get_greeting()

    # Inquire and request direct payment
    resp1, state1, esc1 = session.process_turn("I want to pay my bill now with my card on file")
    assert state1 == CallState.SUBFLOW_EXECUTION
    assert "card ending in 4242" in resp1
    assert "To confirm before charging" in resp1

    # Confirm payment
    resp2, state2, esc2 = session.process_turn("Yes, charge my card")
    assert state2 == CallState.RESOLVED_CONTAINED
    assert "Success! Your payment" in resp2
    assert "TXN-" in resp2
    assert "$0.00" in resp2
    assert session.account.current_balance == 0.0

def test_regulatory_disclosure_and_bilingual_switch():
    from app.config import config
    config.REGULATORY_DISCLOSURE_ENABLED = True
    session = CallSessionStateMachine(session_id="test-session-bilingual", ani="+15550192834")
    greeting = session.get_greeting()
    assert config.REGULATORY_DISCLOSURE_PROMPT in greeting

    # Switch to Spanish
    resp, state, esc = session.process_turn("Quiero hablar en español")
    assert "He cambiado el idioma a español" in resp
    assert session.language == "es-US"

def test_pronunciation_overrides():
    from app.services.tts import tts_service
    raw_text = "Your ONT terminal is transmitting 1 Gbps with VoIP enabled via SMS"
    processed = tts_service.apply_pronunciation_overrides(raw_text)
    assert "O-N-T" in processed
    assert "gigabits per second" in processed
    assert "Voice over I-P" in processed
    assert "text message" in processed

