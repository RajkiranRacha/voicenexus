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
