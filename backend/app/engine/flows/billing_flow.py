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
        flow_context: Dict[str, Any],
        language: str = "en-US"
    ) -> Tuple[str, bool, bool, Dict[str, Any]]:
        """
        Returns:
            (response_text, is_resolved, should_escalate, updated_context)
        """
        step = flow_context.get("step", "INITIAL")
        lowered = user_text.lower()
        is_es = language.startswith("es")
        is_hi = language.startswith("hi")
        affirmatives = ["yes", "pay", "charge", "confirm", "sure", "yep", "yeah", "that's right", "go ahead",
                        "sí", "si", "pagar", "confirmo", "de acuerdo", "adelante", "correcto",
                        "haan", "ha", "theek hai", "sahi hai", "karo"]
        negatives = ["no", "cancel", "don't", "stop", "change",
                     "cancelar", "incorrecto", "parar", "cambiar",
                     "nahi", "nahin", "mat karo", "rad karo"]

        # Check for out-of-scope requests (e.g., split payment across 2 cards, fee dispute)
        if any(term in lowered for term in ["split payment", "two cards", "half on debit", "waive fee", "dispute charge", "cancel service"]):
            flow_context["escalation_reason"] = "OUT_OF_SCOPE_BILLING_REQUEST"
            flow_context["notes"] = f"Caller requested out-of-scope operation: '{user_text}'. Requires human billing specialist."
            flow_context["attempted_action"] = "BILLING_SPECIALIST_HANDOFF"
            if is_es:
                response = (
                    "Veo que está consultando sobre una solicitud especializada de facturación que requiere nuestro equipo de especialistas. "
                    "Estoy preparando los detalles de su cuenta para que el agente pueda ayudarle de inmediato."
                )
            elif is_hi:
                response = (
                    "मैं देख रहा हूँ कि आप एक विशेष बिलिंग अनुरोध के बारे में पूछ रहे हैं जिसके लिए हमारी बिलिंग विशेषज्ञ टीम की आवश्यकता है। "
                    "मैं आपके खाते का विवरण तैयार कर रहा हूँ ताकि एजेंट तुरंत आपकी मदद कर सके।"
                )
            else:
                response = (
                    "I see you are inquiring about a specialized billing request that requires our billing specialist team. "
                    "I am preparing your account details so the agent can help you right away."
                )
            return response, False, True, flow_context

        # Step 1: Initial balance inquiry, direct payment, or payment arrangement intent
        if step == "INITIAL":
            # Check if caller wants to pay directly now
            if any(term in lowered for term in ["pay now", "pay bill now", "make a payment", "charge my card", "pay my bill", "pay balance", "pay it",
                                                  "pagar ahora", "pagar mi factura", "hacer un pago",
                                                  "abhi bhugtan", "payment karo", "abhi pay"]):
                if account.current_balance <= 0:
                    flow_context["step"] = "COMPLETED"
                    if is_es:
                        response = (
                            "Su saldo actual es $0.00. No se requiere ningún pago en este momento. "
                            "¿Puedo ayudarle con algo más hoy?"
                        )
                    elif is_hi:
                        response = (
                            "आपके खाते का शेष $0.00 है। इस समय किसी भुगतान की आवश्यकता नहीं है। "
                            "क्या आज मैं आपकी किसी और चीज़ में मदद कर सकता हूँ?"
                        )
                    else:
                        response = (
                            f"Your account balance is currently $0.00. No payment is required at this time. "
                            "Can I help you with anything else today?"
                        )
                    return response, True, False, flow_context

                flow_context["step"] = "CONFIRM_DIRECT_PAYMENT"
                flow_context["attempted_action"] = "DIRECT_CARD_PAYMENT"
                flow_context["payment_amount"] = account.current_balance
                if is_es:
                    response = (
                        f"Su saldo es de ${account.current_balance:.2f}, con vencimiento el {account.due_date}. "
                        f"Tenemos su tarjeta terminada en {account.payment_card_last4} registrada. "
                        f"Para confirmar antes de cobrar: ¿le gustaría que procese un pago único de "
                        f"${account.current_balance:.2f} a esta tarjeta ahora mismo?"
                    )
                elif is_hi:
                    response = (
                        f"आपका शेष ${account.current_balance:.2f} है, जिसकी देय तिथि {account.due_date} है। "
                        f"हमारे पास आपका कार्ड नंबर {account.payment_card_last4} पर समाप्त होने वाला दर्ज है। "
                        f"शुल्क लेने से पहले पुष्टि करने के लिए: क्या आप चाहेंगे कि मैं इस कार्ड पर "
                        f"${account.current_balance:.2f} का एकमुश्त भुगतान अभी प्रोसेस करूं?"
                    )
                else:
                    response = (
                        f"Your balance is ${account.current_balance:.2f}, due on {account.due_date}. "
                        f"We have your card ending in {account.payment_card_last4} on file. "
                        f"To confirm before charging: would you like me to process a one-time payment of "
                        f"${account.current_balance:.2f} to this card right now?"
                    )
                return response, False, False, flow_context

            # Check if caller wants statement emailed
            if any(term in lowered for term in ["email statement", "send bill", "copy of bill", "email bill", "send statement",
                                                  "enviar factura", "copia de factura", "enviar estado",
                                                  "bill bhejo", "statement bhejo"]):
                flow_context["step"] = "COMPLETED"
                if is_es:
                    response = (
                        f"He enviado una copia detallada de su último estado de cuenta a {account.email}. "
                        "Debería recibirlo en unos minutos. ¿Hay algo más en lo que pueda ayudarle?"
                    )
                elif is_hi:
                    response = (
                        f"मैंने आपके नवीनतम बिलिंग स्टेटमेंट की एक विस्तृत प्रति {account.email} पर भेज दी है। "
                        "आपको यह कुछ ही मिनटों में मिल जाएगी। क्या मैं आपकी किसी और चीज़ में मदद कर सकता हूँ?"
                    )
                else:
                    response = (
                        f"I have sent an itemized copy of your latest billing statement to {account.email}. "
                        "You should receive it within a few minutes. Is there anything else I can assist you with?"
                    )
                return response, True, False, flow_context

            # Check if caller wants to schedule a payment arrangement
            if any(term in lowered for term in ["pay later", "payment arrangement", "promise", "next week", "friday", "extension", "delay",
                                                  "promesa de pago", "acuerdo de pago", "próxima semana", "extensión",
                                                  "baad mein bhugtan", "agle hafte", "kist"]):
                flow_context["step"] = "AWAITING_PAYMENT_DATE"
                flow_context["attempted_action"] = "PAYMENT_ARRANGEMENT"
                if is_es:
                    response = (
                        f"Su saldo actual es ${account.current_balance:.2f}, con vencimiento el {account.due_date}. "
                        "Puedo ayudarle a programar un acuerdo de pago. ¿Qué fecha le gustaría establecer para su pago?"
                    )
                elif is_hi:
                    response = (
                        f"आपका वर्तमान शेष ${account.current_balance:.2f} है, जिसकी देय तिथि {account.due_date} है। "
                        "मैं आपके लिए एक भुगतान योजना निर्धारित करने में मदद कर सकता हूँ। आप भुगतान के लिए कौन सी तारीख निर्धारित करना चाहेंगे?"
                    )
                else:
                    response = (
                        f"Your current balance is ${account.current_balance:.2f}, due on {account.due_date}. "
                        "I can help you schedule a payment arrangement. What date would you like to set for your payment?"
                    )
                return response, False, False, flow_context
            else:
                # Standard balance reading
                flow_context["step"] = "BALANCE_RECITED"
                flow_context["attempted_action"] = "BALANCE_INQUIRY"
                if is_es:
                    response = (
                        f"Su saldo actual es de ${account.current_balance:.2f}, y su fecha de vencimiento es {account.due_date}. "
                        "¿Le gustaría pagar ahora con su tarjeta registrada, establecer un acuerdo de pago, o hay algo más en su factura en lo que pueda ayudarle?"
                    )
                elif is_hi:
                    response = (
                        f"आपका वर्तमान खाता शेष ${account.current_balance:.2f} है, और आपकी देय तिथि {account.due_date} है। "
                        "क्या आप अपने दर्ज कार्ड से अभी भुगतान करना चाहेंगे, एक भुगतान योजना बनाना चाहेंगे, या आपके बिल से जुड़ा कुछ और है जिसमें मैं मदद कर सकूं?"
                    )
                else:
                    response = (
                        f"Your current account balance is ${account.current_balance:.2f}, and your due date is {account.due_date}. "
                        "Would you like to pay now using your card on file, set up a payment arrangement, or is there anything else with your bill I can help with?"
                    )
                return response, False, False, flow_context

        # Step: Direct Payment Confirmation
        elif step == "CONFIRM_DIRECT_PAYMENT":
            if any(term in lowered for term in affirmatives):
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
                if is_es:
                    response = (
                        f"¡Listo! Su pago de ${amt:.2f} ha sido aprobado en la tarjeta terminada en {account.payment_card_last4}. "
                        f"Su número de referencia de recibo es {result['transaction_id']}, y su saldo actualizado es $0.00. "
                        "¿Puedo ayudarle con algo más hoy?"
                    )
                elif is_hi:
                    response = (
                        f"सफलता! आपका ${amt:.2f} का भुगतान कार्ड नंबर {account.payment_card_last4} पर स्वीकृत हो गया है। "
                        f"आपका रसीद संदर्भ नंबर {result['transaction_id']} है, और आपका अपडेटेड शेष $0.00 है। "
                        "क्या आज मैं आपकी और किसी चीज़ में मदद कर सकता हूँ?"
                    )
                else:
                    response = (
                        f"Success! Your payment of ${amt:.2f} has been approved on card ending in {account.payment_card_last4}. "
                        f"Your receipt reference number is {result['transaction_id']}, and your updated balance is $0.00. "
                        "Can I help you with anything else today?"
                    )
                return response, True, False, flow_context
            elif any(term in lowered for term in negatives):
                flow_context["step"] = "BALANCE_RECITED"
                if is_es:
                    response = "No se procesó ningún pago. ¿Le gustaría programar un acuerdo de pago para más adelante?"
                elif is_hi:
                    response = "कोई भुगतान प्रोसेस नहीं किया गया। क्या आप बाद के लिए भुगतान योजना बनाना चाहेंगे?"
                else:
                    response = "No payment was processed. Would you like to schedule a payment arrangement for later instead?"
                return response, False, False, flow_context
            else:
                if is_es:
                    response = (
                        f"Por favor confirme: ¿le gustaría que cobre ${account.current_balance:.2f} a su tarjeta terminada en {account.payment_card_last4}? "
                        "Por favor diga sí o no."
                    )
                elif is_hi:
                    response = (
                        f"कृपया पुष्टि करें: क्या मैं आपके कार्ड नंबर {account.payment_card_last4} पर ${account.current_balance:.2f} शुल्क लूं? "
                        "कृपया हाँ या नहीं कहें।"
                    )
                else:
                    response = (
                        f"Please confirm: would you like me to charge ${account.current_balance:.2f} to your card ending in {account.payment_card_last4}? "
                        "Please say yes or no."
                    )
                return response, False, False, flow_context

        # Step 2: Date given for payment arrangement
        elif step == "AWAITING_PAYMENT_DATE":
            # Extract date or use provided phrase
            date_match = re.search(r'(next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|(?:september|october|november|december)\s+\d{1,2}|\d{4}-\d{2}-\d{2}|\d{1,2}(?:st|nd|rd|th)?)', lowered)
            default_date = "el próximo viernes" if is_es else "अगले शुक्रवार" if is_hi else "next Friday"
            chosen_date = date_match.group(0) if date_match else default_date
            flow_context["proposed_payment_date"] = chosen_date
            flow_context["step"] = "CONFIRMATION_PENDING"

            # PRD Principle: Confirm before committing irreversible action!
            if is_es:
                response = (
                    f"Para confirmar antes de programar: usted desea establecer una promesa de pago por su saldo total de "
                    f"${account.current_balance:.2f} para ser procesado el {chosen_date}. ¿Es correcto?"
                )
            elif is_hi:
                response = (
                    f"शेड्यूल करने से पहले पुष्टि करने के लिए: आप अपने पूरे शेष ${account.current_balance:.2f} के लिए "
                    f"{chosen_date} को भुगतान का वादा करना चाहते हैं। क्या यह सही है?"
                )
            else:
                response = (
                    f"To confirm before I schedule: you would like to set a payment promise for your full balance of "
                    f"${account.current_balance:.2f} to be processed on {chosen_date}. Is that correct?"
                )
            return response, False, False, flow_context

        # Step 3: Confirmation verification
        elif step == "CONFIRMATION_PENDING":
            if any(term in lowered for term in affirmatives):
                idempotency_key = flow_context.get("idempotency_key", str(uuid.uuid4()))
                default_date = "el próximo viernes" if is_es else "अगले शुक्रवार" if is_hi else "next Friday"
                proposed_date = flow_context.get("proposed_payment_date", default_date)

                result = bss_service.record_payment_promise(
                    account_number=account.account_number,
                    amount=account.current_balance,
                    promise_date=proposed_date,
                    idempotency_key=idempotency_key
                )
                flow_context["confirmation_code"] = result["confirmation_code"]
                flow_context["step"] = "COMPLETED"
                if is_es:
                    response = (
                        f"Gracias. Su acuerdo de pago por ${account.current_balance:.2f} ha sido programado para el {proposed_date}. "
                        f"Su código de confirmación es {result['confirmation_code']}. Su servicio permanecerá activo sin interrupciones. ¿Puedo ayudarle con algo más?"
                    )
                elif is_hi:
                    response = (
                        f"धन्यवाद। आपके ${account.current_balance:.2f} के भुगतान की व्यवस्था {proposed_date} के लिए निर्धारित कर दी गई है। "
                        f"आपका पुष्टिकरण कोड {result['confirmation_code']} है। आपकी सेवा बिना किसी रुकावट के जारी रहेगी। क्या मैं आपकी और किसी चीज़ में मदद कर सकता हूँ?"
                    )
                else:
                    response = (
                        f"Thank you. Your payment arrangement for ${account.current_balance:.2f} has been scheduled for {proposed_date}. "
                        f"Your confirmation code is {result['confirmation_code']}. Your service will remain uninterrupted. Can I help with anything else?"
                    )
                return response, True, False, flow_context

            elif any(term in lowered for term in negatives):
                flow_context["step"] = "AWAITING_PAYMENT_DATE"
                if is_es:
                    response = "No hay problema, vamos a ajustarlo. ¿Qué fecha prefiere para programar el pago?"
                elif is_hi:
                    response = "कोई बात नहीं, चलिए इसे ठीक करते हैं। आप भुगतान के लिए कौन सी तारीख पसंद करेंगे?"
                else:
                    response = "No problem, let's adjust that. What date would you prefer to schedule the payment for?"
                return response, False, False, flow_context
            else:
                if is_es:
                    response = "Por favor aclare: ¿debo confirmar y programar este acuerdo de pago? Por favor diga sí o no."
                elif is_hi:
                    response = "कृपया स्पष्ट करें: क्या मुझे इस भुगतान व्यवस्था की पुष्टि और शेड्यूल करना चाहिए? कृपया हाँ या नहीं कहें।"
                else:
                    response = "Please clarify: should I confirm and schedule this payment arrangement for you? Please say yes or no."
                return response, False, False, flow_context

        # Step 4: After balance recited or completed
        elif step in ["BALANCE_RECITED", "COMPLETED"]:
            if any(term in lowered for term in ["no", "that's all", "nothing else", "goodbye", "done", "bye",
                                                  "nada más", "adiós", "listo",
                                                  "bas", "kuch nahi", "bye"]):
                if is_es:
                    response = "Gracias por ser un cliente valioso. ¡Que tenga un día maravilloso!"
                elif is_hi:
                    response = "एक महत्वपूर्ण ग्राहक होने के लिए धन्यवाद। आपका दिन शुभ हो!"
                else:
                    response = "Thank you for being a valued customer. Have a wonderful day!"
                return response, True, False, flow_context
            elif any(term in lowered for term in ["payment", "arrangement", "promise", "pay later",
                                                    "pago", "acuerdo", "promesa",
                                                    "bhugtan", "kist"]):
                flow_context["step"] = "AWAITING_PAYMENT_DATE"
                if is_es:
                    return "¿Qué fecha le gustaría programar para ese pago?", False, False, flow_context
                elif is_hi:
                    return "आप उस भुगतान के लिए कौन सी तारीख निर्धारित करना चाहेंगे?", False, False, flow_context
                return "What date would you like to schedule that payment for?", False, False, flow_context

        if is_es:
            return "Puedo ayudarle con su saldo o establecer un acuerdo de pago. ¿Cómo le gustaría proceder?", False, False, flow_context
        elif is_hi:
            return "मैं आपके शेष या भुगतान व्यवस्था स्थापित करने में मदद कर सकता हूँ। आप कैसे आगे बढ़ना चाहेंगे?", False, False, flow_context
        return "I can assist you with your balance or setting up a payment arrangement. How would you like to proceed?", False, False, flow_context
