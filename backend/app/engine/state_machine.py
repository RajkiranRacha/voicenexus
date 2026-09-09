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
from app.i18n import t
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
        self.pending_intent: Optional[IntentEnum] = None
        self.flow_context: Dict[str, Any] = {}
        self.consecutive_unrecognized: int = 0
        self.turns: list[DialogueTurn] = []
        self.start_time = datetime.now()
        self.escalation_payload: Optional[EscalationPayload] = None
        self.account: Optional[SubscriberAccount] = None
        self.language: str = config.LANGUAGE

        # Execute Tier 1 Passive ANI Verification
        auth_status, acc = identity_service.verify_ani(ani)
        self.account = acc

    def get_greeting(self) -> str:
        self.state = CallState.GREETING
        prefix = ""
        if config.REGULATORY_DISCLOSURE_ENABLED:
            prefix = f"{config.REGULATORY_DISCLOSURE_PROMPT} "

        if self.account:
            return t(
                "greeting.known_account", self.language,
                prefix=prefix, operator_name=config.OPERATOR_NAME, customer_name=self.account.customer_name
            )

        # PRD VN-3: Caller ANI not matched in BSS -> Challenge for KBA
        self.state = CallState.AUTH_CHALLENGE
        return t("greeting.unknown_ani", self.language, prefix=prefix, operator_name=config.OPERATOR_NAME)

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

        # 2. Check for Language Switch (VN-7)
        if intent == IntentEnum.LANGUAGE_SELECT:
            if any(w in lowered for w in ["spanish", "español"]):
                self.language = "es-US"
                return (
                    "He cambiado el idioma a español. ¿En qué le puedo ayudar hoy con su servicio de fibra?",
                    CallState.INTENT_ROUTING,
                    None
                )
            elif any(w in lowered for w in ["hindi", "हिंदी", "हिन्दी"]):
                self.language = "hi-IN"
                return (
                    "मैंने भाषा को हिंदी में बदल दिया है। मैं आज आपकी क्या सहायता कर सकता हूँ?",
                    CallState.INTENT_ROUTING,
                    None
                )
            else:
                self.language = "en-US"
                return (
                    "I have switched your language preference to English. How can I help you today?",
                    CallState.INTENT_ROUTING,
                    None
                )

        # 3. Handle Identity Verification / Auth Challenge (VN-3)
        if self.state == CallState.AUTH_CHALLENGE:
            # Check for Knowledge-Based Auth (Account Number or Zip Code)
            acc = identity_service.verify_knowledge_based(user_text)
            if acc:
                self.account = acc
                self.state = CallState.INTENT_ROUTING
                if self.pending_intent:
                    pending = self.pending_intent
                    self.pending_intent = None
                    return self._route_intent(pending, user_text)
                return (
                    f"Thank you, {acc.customer_name}! I have verified your account with billing address at {acc.address}. "
                    "How can I help you today? You can ask about your bill, current plan, or check for area outages.",
                    self.state,
                    None
                )

            # Check for 4-digit Step-Up OTP
            digits = "".join(filter(str.isdigit, user_text))
            phone_to_check = self.account.phone_number if self.account else self.ani
            if digits and identity_service.verify_step_up_otp(phone_to_check, digits):
                self.state = CallState.INTENT_ROUTING
                if not self.account:
                    self.account = bss_service.get_account_by_phone(phone_to_check)
                if self.pending_intent:
                    pending = self.pending_intent
                    self.pending_intent = None
                    return self._route_intent(pending, user_text)
                return (
                    "Thank you, your verification code has been confirmed. How can I help you today?",
                    self.state,
                    None
                )

            # Explicit request for a texted verification code (step-up OTP, VN-3)
            if any(w in lowered for w in ["text me a code", "send me a code", "send a code", "text code", "verification code", "enviar código", "mandar código"]):
                phone_to_text = self.account.phone_number if self.account else self.ani
                identity_service.issue_step_up_otp(phone_to_text)
                return (
                    "I've sent a 4-digit verification code by text message to the phone number on file. "
                    "Please read that code back to me now.",
                    self.state,
                    None
                )

            # If not matched
            return (
                "I couldn't locate an account with that information. Please speak or enter your 6-digit account number, "
                "your 5-digit billing ZIP code, say 'text me a code' to receive a verification code by SMS, "
                "or say 'agent' to speak with customer care.",
                self.state,
                None
            )

        # 4. If in active subflow execution, continue that subflow
        if self.state in [CallState.SUBFLOW_EXECUTION, CallState.CONFIRMATION_PENDING]:
            return self._continue_subflow(user_text, intent)

        # 5. Handle Conversational Responses (Gratitude, Acknowledgement, Confirmation, Rejection)
        if intent == IntentEnum.GRATITUDE:
            self.consecutive_unrecognized = 0
            if any(phrase in lowered for phrase in [
                "good", "fine", "nothing", "that's all", "thats all", "all set",
                "no need", "bien", "nada más", "nada mas", "kuch nahi", "sab theek", "sab thik",
                "goodbye", "good bye", "bye", "adios", "adiós", "hasta luego", "alvida", "अलविदा", "see you", "have a"
            ]):
                return t("gratitude.closing", self.language), CallState.RESOLVED_CONTAINED, None
            return t("gratitude.continue", self.language), CallState.INTENT_ROUTING, None

        if intent == IntentEnum.ACKNOWLEDGEMENT:
            self.consecutive_unrecognized = 0
            return t("acknowledgement.continue", self.language), CallState.INTENT_ROUTING, None

        if intent in [IntentEnum.CONFIRMATION, IntentEnum.CONFIRMATION_YES]:
            self.consecutive_unrecognized = 0
            return t("confirmation.continue", self.language), CallState.INTENT_ROUTING, None

        if intent in [IntentEnum.REJECTION, IntentEnum.CONFIRMATION_NO]:
            self.consecutive_unrecognized = 0
            return t("rejection.closing", self.language), CallState.RESOLVED_CONTAINED, None

        # 6. Intent Routing Phase
        if intent in [
            IntentEnum.BILLING_INQUIRY,
            IntentEnum.PAY_BILL_NOW,
            IntentEnum.PAYMENT_PROMISE,
            IntentEnum.OUTAGE_TRIAGE,
            IntentEnum.PLAN_INQUIRY,
            IntentEnum.PLAN_UPGRADE,
            IntentEnum.CALLBACK_SCHEDULE
        ]:
            return self._route_intent(intent, user_text)

        # 7. Handle Unrecognized Utterance
        self.consecutive_unrecognized += 1
        if self.consecutive_unrecognized >= config.MAX_UNRECOGNIZED_TURNS:
            return self._trigger_escalation(
                reason="EXCEEDED_MAX_UNRECOGNIZED_TURNS",
                notes=f"Caller intent not recognized after {self.consecutive_unrecognized} attempts. Last utterance: '{user_text}'"
            )

        return t("unrecognized.retry", self.language), CallState.INTENT_ROUTING, None

    def _route_intent(self, intent: IntentEnum, user_text: str) -> Tuple[str, CallState, Optional[EscalationPayload]]:
        self.current_intent = intent
        self.state = CallState.SUBFLOW_EXECUTION
        self.consecutive_unrecognized = 0

        # Gate sensitive billing / plan actions behind authentication
        if intent in [IntentEnum.BILLING_INQUIRY, IntentEnum.PAY_BILL_NOW, IntentEnum.PAYMENT_PROMISE, IntentEnum.PLAN_UPGRADE]:
            if not self.account:
                self.state = CallState.AUTH_CHALLENGE
                self.pending_intent = intent
                return (
                    "To access your billing details and account transactions, I first need to locate your account. "
                    "Please state your account number or billing ZIP code.",
                    self.state,
                    None
                )

        if intent in [IntentEnum.BILLING_INQUIRY, IntentEnum.PAY_BILL_NOW, IntentEnum.PAYMENT_PROMISE]:
            return self._execute_billing_turn(user_text)
        elif intent == IntentEnum.OUTAGE_TRIAGE:
            return self._execute_outage_turn(user_text)
        elif intent in [IntentEnum.PLAN_INQUIRY, IntentEnum.PLAN_UPGRADE]:
            return self._execute_plan_turn(user_text)
        elif intent == IntentEnum.CALLBACK_SCHEDULE:
            return self._execute_callback_turn(user_text)

        return "How else may I help you?", CallState.INTENT_ROUTING, None

    def _continue_subflow(self, user_text: str, intent: IntentEnum) -> Tuple[str, CallState, Optional[EscalationPayload]]:
        if self.current_intent in [IntentEnum.BILLING_INQUIRY, IntentEnum.PAY_BILL_NOW, IntentEnum.PAYMENT_PROMISE]:
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
        acc = self.account or bss_service.get_account_by_phone(config.DEFAULT_DEMO_ANI)
        response, is_resolved, should_escalate, updated_ctx = BillingFlow.handle_turn(
            user_text, acc, self.flow_context, language=self.language
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
        acc = self.account or bss_service.get_account_by_phone(config.DEFAULT_OUTAGE_DEMO_ANI)
        response, is_resolved, should_escalate, updated_ctx = OutageTriageFlow.handle_turn(
            user_text, acc, self.flow_context, language=self.language
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
        acc = self.account or bss_service.get_account_by_phone(config.DEFAULT_DEMO_ANI)
        response, is_resolved, should_escalate, updated_ctx = PlanFlow.handle_turn(
            user_text, acc, self.flow_context, language=self.language
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
        acc = self.account or bss_service.get_account_by_phone(config.DEFAULT_DEMO_ANI)
        response, is_resolved, should_escalate, updated_ctx = CallbackFlow.handle_turn(
            user_text, acc, self.flow_context, language=self.language
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

        prompt = (
            t("escalation.prompt", self.language)
            if self.language != "en-US"
            else config.ESCALATION_PROMPT
        )
        return prompt, self.state, self.escalation_payload
