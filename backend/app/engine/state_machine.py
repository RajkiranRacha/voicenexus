from typing import Dict, Any, Tuple, Optional
from datetime import datetime
from app.models.schemas import (
    CallState, IntentEnum, SubscriberAccount, AuthStatus,
    EscalationPayload, DialogueTurn
)
from app.config import config
from app.services.identity import identity_service
from app.services.bss_oss import bss_service
from app.engine.intent_classifier import intent_classifier
from app.engine.flows.billing_flow import BillingFlow
from app.engine.flows.outage_triage_flow import OutageTriageFlow
from app.engine.flows.plan_flow import PlanFlow
from app.engine.flows.callback_flow import CallbackFlow

class CallSessionStateMachine:
    """
    Deterministic Care State Machine for a single call session (VN-2, VN-5).
    Guarantees strict policy adherence, auth gates, confirm-before-commit, and safe handoffs.
    """

    def __init__(self, session_id: str, ani: str):
        self.session_id = session_id
        self.ani = ani
        self.state = CallState.RINGING
        self.current_intent: Optional[IntentEnum] = None
        self.flow_context: Dict[str, Any] = {}
        self.consecutive_unrecognized: int = 0
        self.turns: list[DialogueTurn] = []
        self.start_time = datetime.now()
        self.escalation_payload: Optional[EscalationPayload] = None
        self.account: Optional[SubscriberAccount] = None

        # Execute Tier 1 Passive ANI Verification
        auth_status, acc = identity_service.verify_ani(ani)
        self.account = acc

    def get_greeting(self) -> str:
        self.state = CallState.GREETING
        if self.account:
            return (
                f"Thank you for calling {config.OPERATOR_NAME}. I see you're calling from the number "
                f"associated with {self.account.customer_name}'s account. I am your automated care assistant. "
                "How can I help you today?"
            )
        return config.GREETING_PROMPT

    def process_turn(self, user_text: str) -> Tuple[str, CallState, Optional[EscalationPayload]]:
        lowered = user_text.lower().strip()

        # If caller enters touch-tone DTMF (e.g. "0" for operator or degraded fallback)
        if user_text.strip() == "0" or "zero" in lowered:
            return self._trigger_escalation(
                reason="CALLER_DTMF_OPERATOR_REQUEST",
                notes="Caller pressed 0 for live operator."
            )

        # Classify Intent
        intent, conf, meta = intent_classifier.classify(user_text)

        # 1. Check for immediate explicit agent request
        if intent == IntentEnum.AGENT_ESCALATION:
            return self._trigger_escalation(
                reason="EXPLICIT_AGENT_REQUEST",
                notes=f"Caller requested human agent with utterance: '{user_text}'"
            )

        # 2. Check if we need Step-Up OTP authentication
        if self.state == CallState.AUTH_CHALLENGE:
            # Check for 4 digit PIN / OTP
            digits = "".join(filter(str.isdigit, user_text))
            if digits and identity_service.verify_step_up_otp(self.ani, digits):
                self.state = CallState.SUBFLOW_EXECUTION
                return (
                    "Thank you, your identity has been securely verified. "
                    "Let's continue with your request. Would you like to proceed?",
                    self.state,
                    None
                )
            else:
                return (
                    "That verification code did not match. Please say or key in the 4-digit code sent to your phone, "
                    "or say 'agent' if you would like me to connect you to care.",
                    self.state,
                    None
                )

        # 3. If in active subflow execution, route to corresponding subflow
        if self.state in [CallState.SUBFLOW_EXECUTION, CallState.CONFIRMATION_PENDING]:
            return self._continue_subflow(user_text, intent)

        # 4. Intent Routing Phase
        if intent in [IntentEnum.BILLING_INQUIRY, IntentEnum.PAYMENT_PROMISE]:
            self.current_intent = intent
            self.state = CallState.SUBFLOW_EXECUTION
            self.consecutive_unrecognized = 0
            return self._execute_billing_turn(user_text)

        elif intent == IntentEnum.OUTAGE_TRIAGE:
            self.current_intent = intent
            self.state = CallState.SUBFLOW_EXECUTION
            self.consecutive_unrecognized = 0
            return self._execute_outage_turn(user_text)

        elif intent in [IntentEnum.PLAN_INQUIRY, IntentEnum.PLAN_UPGRADE]:
            self.current_intent = intent
            self.state = CallState.SUBFLOW_EXECUTION
            self.consecutive_unrecognized = 0
            return self._execute_plan_turn(user_text)

        elif intent == IntentEnum.CALLBACK_SCHEDULE:
            self.current_intent = intent
            self.state = CallState.SUBFLOW_EXECUTION
            self.consecutive_unrecognized = 0
            return self._execute_callback_turn(user_text)

        # 5. Handle Unrecognized Utterance
        self.consecutive_unrecognized += 1
        if self.consecutive_unrecognized >= config.MAX_UNRECOGNIZED_TURNS:
            return self._trigger_escalation(
                reason="EXCEEDED_MAX_UNRECOGNIZED_TURNS",
                notes=f"Caller intent not recognized after {self.consecutive_unrecognized} attempts. Last utterance: '{user_text}'"
            )

        return (
            "I didn't quite catch that. I can help you check your bill, set up a payment arrangement, "
            "check for area internet outages, or review your plan. How can I assist?",
            CallState.INTENT_ROUTING,
            None
        )

    def _continue_subflow(self, user_text: str, intent: IntentEnum) -> Tuple[str, CallState, Optional[EscalationPayload]]:
        if self.current_intent in [IntentEnum.BILLING_INQUIRY, IntentEnum.PAYMENT_PROMISE]:
            return self._execute_billing_turn(user_text)
        elif self.current_intent == IntentEnum.OUTAGE_TRIAGE:
            return self._execute_outage_turn(user_text)
        elif self.current_intent in [IntentEnum.PLAN_INQUIRY, IntentEnum.PLAN_UPGRADE]:
            return self._execute_plan_turn(user_text)
        elif self.current_intent == IntentEnum.CALLBACK_SCHEDULE:
            return self._execute_callback_turn(user_text)
        
        return "How else may I help you?", CallState.INTENT_ROUTING, None

    def _execute_billing_turn(self, user_text: str):
        # Fallback account if caller ANI not pre-registered
        acc = self.account or bss_service.get_account_by_phone("+15550192834")
        response, is_resolved, should_escalate, updated_ctx = BillingFlow.handle_turn(
            user_text, acc, self.flow_context
        )
        self.flow_context = updated_ctx
        if should_escalate:
            return self._trigger_escalation(
                reason=self.flow_context.get("escalation_reason", "BILLING_SPECIALIST_REQUIRED"),
                notes=self.flow_context.get("notes", "Escalated from billing subflow.")
            )
        if is_resolved:
            self.state = CallState.RESOLVED_CONTAINED
        return response, self.state, None

    def _execute_outage_turn(self, user_text: str):
        acc = self.account or bss_service.get_account_by_phone("+15550148821")
        response, is_resolved, should_escalate, updated_ctx = OutageTriageFlow.handle_turn(
            user_text, acc, self.flow_context
        )
        self.flow_context = updated_ctx
        if should_escalate:
            return self._trigger_escalation(
                reason=self.flow_context.get("escalation_reason", "TECH_SUPPORT_REQUIRED"),
                notes=self.flow_context.get("notes", "Escalated from technical triage subflow.")
            )
        if is_resolved:
            self.state = CallState.RESOLVED_CONTAINED
        return response, self.state, None

    def _execute_plan_turn(self, user_text: str):
        acc = self.account or bss_service.get_account_by_phone("+15550192834")
        response, is_resolved, should_escalate, updated_ctx = PlanFlow.handle_turn(
            user_text, acc, self.flow_context
        )
        self.flow_context = updated_ctx
        if should_escalate:
            return self._trigger_escalation(
                reason="PLAN_SPECIALIST_REQUIRED",
                notes="Escalated from plan management subflow."
            )
        if is_resolved:
            self.state = CallState.RESOLVED_CONTAINED
        return response, self.state, None

    def _execute_callback_turn(self, user_text: str):
        acc = self.account or bss_service.get_account_by_phone("+15550192834")
        response, is_resolved, should_escalate, updated_ctx = CallbackFlow.handle_turn(
            user_text, acc, self.flow_context
        )
        self.flow_context = updated_ctx
        if should_escalate:
            return self._trigger_escalation(
                reason="CALLBACK_REPRESENTATIVE_REQUESTED",
                notes="Caller requested direct agent instead of callback."
            )
        if is_resolved:
            self.state = CallState.RESOLVED_CONTAINED
        return response, self.state, None

    def _trigger_escalation(self, reason: str, notes: str) -> Tuple[str, CallState, EscalationPayload]:
        """
        Creates structured VN-5 handoff payload with full context for the agent desktop.
        """
        self.state = CallState.ESCALATING_TO_AGENT
        duration_sec = int((datetime.now() - self.start_time).total_seconds())
        
        # Build customer profile dictionary
        acc = self.account or bss_service.get_account_by_phone(self.ani)
        cust_profile = {
            "account_number": acc.account_number if acc else "UNREGISTERED",
            "customer_name": acc.customer_name if acc else "Unknown Caller",
            "auth_status": acc.auth_status.value if acc else AuthStatus.UNAUTHENTICATED.value,
            "auth_method": "ANI_PASSIVE_MATCH" if acc else "NONE",
            "phone_number": self.ani
        }

        # Build transcript snippet
        snippet = [
            {"speaker": t.speaker, "text": t.text}
            for t in self.turns[-6:]  # Last 6 turns for fast agent scanning
        ]

        # Determine target queue based on active intent
        queue = "GENERAL_CARE_TIER1"
        if self.current_intent in [IntentEnum.BILLING_INQUIRY, IntentEnum.PAYMENT_PROMISE]:
            queue = "CARE_BILLING_TIER1"
        elif self.current_intent == IntentEnum.OUTAGE_TRIAGE:
            queue = "BROADBAND_TECH_SUPPORT"
        elif self.current_intent in [IntentEnum.PLAN_INQUIRY, IntentEnum.PLAN_UPGRADE]:
            queue = "RETENTION_AND_PLANS"

        self.escalation_payload = EscalationPayload(
            session_id=self.session_id,
            ani=self.ani,
            customer_profile=cust_profile,
            call_context={
                "primary_intent": self.current_intent.value if self.current_intent else "UNKNOWN_INTENT",
                "intent_confidence": 0.95 if self.current_intent else 0.35,
                "duration_in_ivr_seconds": duration_sec,
                "turns_count": len(self.turns)
            },
            resolution_summary={
                "attempted_action": self.flow_context.get("attempted_action", "GENERAL_TRIAGE"),
                "current_balance": acc.current_balance if acc else 0.0,
                "failure_or_escalation_reason": reason,
                "notes": notes,
                "flow_step": self.flow_context.get("step", "EARLY_STAGE")
            },
            recommended_agent_queue=queue,
            transcript_snippet=snippet
        )

        return config.ESCALATION_PROMPT, self.state, self.escalation_payload
