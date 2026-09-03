import uuid
import re
from typing import Dict, Any, Tuple
from app.models.schemas import SubscriberAccount, AuthStatus
from app.services.bss_oss import bss_service

class BillingFlow:
    """
    Subflow for Billing Inquiries and Payment Promise Arrangements (VN-2, VN-4).
    Implements confirm-before-commit and detects out-of-scope conditions cleanly.
    """

    @staticmethod
    def handle_turn(
        user_text: str,
        account: SubscriberAccount,
        flow_context: Dict[str, Any]
    ) -> Tuple[str, bool, bool, Dict[str, Any]]:
        """
        Returns:
            (response_text, is_resolved, should_escalate, updated_context)
        """
        step = flow_context.get("step", "INITIAL")
        lowered = user_text.lower()

        # Check for out-of-scope requests (e.g., split payment across 2 cards, fee dispute)
        if any(term in lowered for term in ["split payment", "two cards", "half on debit", "waive fee", "dispute charge", "cancel service"]):
            flow_context["escalation_reason"] = "OUT_OF_SCOPE_BILLING_REQUEST"
            flow_context["notes"] = f"Caller requested out-of-scope operation: '{user_text}'. Requires human billing specialist."
            flow_context["attempted_action"] = "BILLING_SPECIALIST_HANDOFF"
            response = (
                "I see you are inquiring about a specialized billing request that requires our billing specialist team. "
                "I am preparing your account details so the agent can help you right away."
            )
            return response, False, True, flow_context

        # Step 1: Initial balance inquiry or payment arrangement intent
        if step == "INITIAL":
            # Check if caller wants to schedule a payment arrangement
            if any(term in lowered for term in ["pay later", "payment arrangement", "promise", "next week", "friday", "extension", "delay"]):
                flow_context["step"] = "AWAITING_PAYMENT_DATE"
                flow_context["attempted_action"] = "PAYMENT_ARRANGEMENT"
                response = (
                    f"Your current balance is ${account.current_balance:.2f}, due on {account.due_date}. "
                    "I can help you schedule a payment arrangement. What date would you like to set for your payment?"
                )
                return response, False, False, flow_context
            else:
                # Standard balance reading
                flow_context["step"] = "BALANCE_RECITED"
                flow_context["attempted_action"] = "BALANCE_INQUIRY"
                response = (
                    f"Your current account balance is ${account.current_balance:.2f}, and your due date is {account.due_date}. "
                    "Would you like to schedule a payment arrangement, or is there anything else with your bill I can help with?"
                )
                return response, False, False, flow_context

        # Step 2: Date given for payment arrangement
        elif step == "AWAITING_PAYMENT_DATE":
            # Extract date or use provided phrase
            date_match = re.search(r'(next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|(?:september|october|november|december)\s+\d{1,2}|\d{4}-\d{2}-\d{2}|\d{1,2}(?:st|nd|rd|th)?)', lowered)
            chosen_date = date_match.group(0) if date_match else "next Friday"
            flow_context["proposed_payment_date"] = chosen_date
            flow_context["step"] = "CONFIRMATION_PENDING"

            # PRD Principle: Confirm before committing irreversible action!
            response = (
                f"To confirm before I schedule: you would like to set a payment promise for your full balance of "
                f"${account.current_balance:.2f} to be processed on {chosen_date}. Is that correct?"
            )
            return response, False, False, flow_context

        # Step 3: Confirmation verification
        elif step == "CONFIRMATION_PENDING":
            if any(term in lowered for term in ["yes", "correct", "yep", "yeah", "confirm", "sure", "that's right"]):
                idempotency_key = flow_context.get("idempotency_key", str(uuid.uuid4()))
                proposed_date = flow_context.get("proposed_payment_date", "next Friday")
                
                result = bss_service.record_payment_promise(
                    account_number=account.account_number,
                    amount=account.current_balance,
                    promise_date=proposed_date,
                    idempotency_key=idempotency_key
                )
                flow_context["confirmation_code"] = result["confirmation_code"]
                flow_context["step"] = "COMPLETED"
                response = (
                    f"Thank you. Your payment arrangement for ${account.current_balance:.2f} has been scheduled for {proposed_date}. "
                    f"Your confirmation code is {result['confirmation_code']}. Your service will remain uninterrupted. Can I help with anything else?"
                )
                return response, True, False, flow_context

            elif any(term in lowered for term in ["no", "cancel", "wrong", "change"]):
                flow_context["step"] = "AWAITING_PAYMENT_DATE"
                response = "No problem, let's adjust that. What date would you prefer to schedule the payment for?"
                return response, False, False, flow_context
            else:
                response = "Please clarify: should I confirm and schedule this payment arrangement for you? Please say yes or no."
                return response, False, False, flow_context

        # Step 4: After balance recited or completed
        elif step in ["BALANCE_RECITED", "COMPLETED"]:
            if any(term in lowered for term in ["no", "that's all", "nothing else", "goodbye", "done", "bye"]):
                response = "Thank you for being a valued customer. Have a wonderful day!"
                return response, True, False, flow_context
            elif any(term in lowered for term in ["payment", "arrangement", "promise", "pay later"]):
                flow_context["step"] = "AWAITING_PAYMENT_DATE"
                return "What date would you like to schedule that payment for?", False, False, flow_context

        return "I can assist you with your balance or setting up a payment arrangement. How would you like to proceed?", False, False, flow_context
