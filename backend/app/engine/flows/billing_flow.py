import uuid
import re
from typing import Dict, Any, Tuple
from app.models.schemas import SubscriberAccount, AuthStatus
from app.services.bss_oss import bss_service
from app.engine.nlu_utils import is_affirmative, is_negative
from app.i18n import t

class BillingFlow:
    """
    Subflow for Billing Inquiries and Payment Promise Arrangements (VN-2, VN-4).
    Implements confirm-before-commit and detects out-of-scope conditions cleanly.
    """

    @staticmethod
    def handle_turn(
        user_text: str,
        account: SubscriberAccount,
        flow_context: Dict[str, Any],
        language: str = "en-US"
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
            return t("billing.out_of_scope", language), False, True, flow_context

        # Step 1: Initial balance inquiry, direct payment, or payment arrangement intent
        if step == "INITIAL":
            # Check if caller wants to pay directly now
            if any(term in lowered for term in ["pay now", "pay bill now", "make a payment", "charge my card", "pay my bill", "pay balance", "pay it",
                                                  "pagar ahora", "pagar mi factura", "hacer un pago",
                                                  "abhi bhugtan", "payment karo", "abhi pay"]):
                if account.current_balance <= 0:
                    flow_context["step"] = "COMPLETED"
                    return t("billing.zero_balance", language), True, False, flow_context

                flow_context["step"] = "CONFIRM_DIRECT_PAYMENT"
                flow_context["attempted_action"] = "DIRECT_CARD_PAYMENT"
                flow_context["payment_amount"] = account.current_balance
                response = t(
                    "billing.confirm_direct_payment", language,
                    balance=account.current_balance, due_date=account.due_date, card_last4=account.payment_card_last4
                )
                return response, False, False, flow_context

            # Check if caller wants statement emailed
            if any(term in lowered for term in ["email statement", "send bill", "copy of bill", "email bill", "send statement",
                                                  "enviar factura", "copia de factura", "enviar estado",
                                                  "bill bhejo", "statement bhejo"]):
                flow_context["step"] = "COMPLETED"
                response = t("billing.email_statement_sent", language, email=account.email)
                return response, True, False, flow_context

            # Check if caller wants to schedule a payment arrangement
            if any(term in lowered for term in ["pay later", "payment arrangement", "promise", "next week", "friday", "extension", "delay",
                                                  "promesa de pago", "acuerdo de pago", "próxima semana", "extensión",
                                                  "baad mein bhugtan", "agle hafte", "kist"]):
                flow_context["step"] = "AWAITING_PAYMENT_DATE"
                flow_context["attempted_action"] = "PAYMENT_ARRANGEMENT"
                response = t(
                    "billing.payment_arrangement_offer", language,
                    balance=account.current_balance, due_date=account.due_date
                )
                return response, False, False, flow_context
            else:
                # Standard balance reading
                flow_context["step"] = "BALANCE_RECITED"
                flow_context["attempted_action"] = "BALANCE_INQUIRY"
                response = t(
                    "billing.balance_recited", language,
                    balance=account.current_balance, due_date=account.due_date
                )
                return response, False, False, flow_context

        # Step: Direct Payment Confirmation
        elif step == "CONFIRM_DIRECT_PAYMENT":
            if is_affirmative(user_text, language):
                idempotency_key = flow_context.get("idempotency_key", str(uuid.uuid4()))
                amt = flow_context.get("payment_amount", account.current_balance)
                result = bss_service.process_card_payment(
                    account_number=account.account_number,
                    amount=amt,
                    card_last4=account.payment_card_last4,
                    idempotency_key=idempotency_key
                )
                flow_context["transaction_id"] = result["transaction_id"]
                flow_context["step"] = "COMPLETED"
                response = t(
                    "billing.direct_payment_success", language,
                    amount=amt, card_last4=account.payment_card_last4, transaction_id=result["transaction_id"]
                )
                return response, True, False, flow_context
            elif is_negative(user_text, language):
                flow_context["step"] = "BALANCE_RECITED"
                return t("billing.direct_payment_declined", language), False, False, flow_context
            else:
                response = t(
                    "billing.direct_payment_confirm_retry", language,
                    balance=account.current_balance, card_last4=account.payment_card_last4
                )
                return response, False, False, flow_context

        # Step 2: Date given for payment arrangement
        elif step == "AWAITING_PAYMENT_DATE":
            # Extract date or use provided phrase
            date_match = re.search(r'(next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|(?:september|october|november|december)\s+\d{1,2}|\d{4}-\d{2}-\d{2}|\d{1,2}(?:st|nd|rd|th)?)', lowered)
            chosen_date = date_match.group(0) if date_match else t("billing.default_next_friday", language)
            flow_context["proposed_payment_date"] = chosen_date
            flow_context["step"] = "CONFIRMATION_PENDING"

            # PRD Principle: Confirm before committing irreversible action!
            response = t(
                "billing.confirm_payment_date", language,
                balance=account.current_balance, chosen_date=chosen_date
            )
            return response, False, False, flow_context

        # Step 3: Confirmation verification
        elif step == "CONFIRMATION_PENDING":
            if is_affirmative(user_text, language):
                idempotency_key = flow_context.get("idempotency_key", str(uuid.uuid4()))
                proposed_date = flow_context.get("proposed_payment_date", t("billing.default_next_friday", language))

                result = bss_service.record_payment_promise(
                    account_number=account.account_number,
                    amount=account.current_balance,
                    promise_date=proposed_date,
                    idempotency_key=idempotency_key
                )
                flow_context["confirmation_code"] = result["confirmation_code"]
                flow_context["step"] = "COMPLETED"
                response = t(
                    "billing.payment_promise_confirmed", language,
                    balance=account.current_balance, proposed_date=proposed_date, confirmation_code=result["confirmation_code"]
                )
                return response, True, False, flow_context

            elif is_negative(user_text, language):
                flow_context["step"] = "AWAITING_PAYMENT_DATE"
                return t("billing.adjust_payment_date", language), False, False, flow_context
            else:
                return t("billing.confirm_payment_date_retry", language), False, False, flow_context

        # Step 4: After balance recited or completed
        elif step in ["BALANCE_RECITED", "COMPLETED"]:
            if any(term in lowered for term in ["no", "that's all", "nothing else", "goodbye", "done", "bye",
                                                  "nada más", "adiós", "listo",
                                                  "bas", "kuch nahi", "bye"]):
                return t("billing.closing_thanks", language), True, False, flow_context
            elif any(term in lowered for term in ["payment", "arrangement", "promise", "pay later",
                                                    "pago", "acuerdo", "promesa",
                                                    "bhugtan", "kist"]):
                flow_context["step"] = "AWAITING_PAYMENT_DATE"
                return t("billing.ask_payment_date", language), False, False, flow_context

        return t("billing.fallback", language), False, False, flow_context
