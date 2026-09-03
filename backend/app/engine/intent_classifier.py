import re
from typing import Tuple, Dict, Any
from app.models.schemas import IntentEnum

class IntentClassifier:
    """
    NLU Intent Classification Engine (VN-1).
    Classifies free-form caller speech into goal-directed care intents.
    Operates with deterministic sub-millisecond local matcher.
    """

    PATTERNS = {
        IntentEnum.AGENT_ESCALATION: [
            r"\b(agent|representative|human|operator|real person|someone else|speak to a person|transfer me|supervisor|representante|agente|operador|persona real|humano)\b"
        ],
        IntentEnum.LANGUAGE_SELECT: [
            r"\b(spanish|español|habla español|en español|switch to spanish|cambiar a español|english|inglés|switch to english|idioma español|hindi|हिंदी|हिन्दी|switch to hindi|hindi mein|hindi me|hindi bolo)\b"
        ],
        IntentEnum.PAY_BILL_NOW: [
            r"\b(pay now|pay bill now|pay my bill|make a payment|pay the balance|charge my card|pay balance|process payment|pay it|pagar ahora|pagar mi factura|hacer un pago)\b"
        ],
        IntentEnum.PAYMENT_PROMISE: [
            r"\b(pay later|payment arrangement|payment promise|extension|need more time to pay|promise to pay|schedule a payment|pay next week|promesa de pago|acuerdo de pago|pagar la próxima semana)\b"
        ],
        IntentEnum.BILLING_INQUIRY: [
            r"\b(bill|balance|how much do i owe|charges|amount due|statement|payment due|due date|invoice|split payment|two cards|two credit cards|factura|saldo|cuánto debo|estado de cuenta|recibo)\b",
            r"\b(pay|payment|pago)\b"
        ],
        IntentEnum.OUTAGE_TRIAGE: [
            r"\b(outage|wifi not working|no connection|offline|blinking red|lost connection|slow internet|broadband down|troubleshoot|sin internet|no hay internet|se cayó el internet|no funciona el wifi|corte de servicio|avería)\b",
            r"\b(internet|wifi|broadband|connection|fiber|red)\b.*\b(down|out|off|slow|broken|dead|unreachable|caído|lento|apagado)\b",
            r"\b(down|outage|caído)\b.*\b(internet|wifi|broadband|connection|red)\b"
        ],
        IntentEnum.PLAN_INQUIRY: [
            r"\b(what plan am i on|current plan|plan details|data limit|my package|qué plan tengo|detalles de mi plan)\b"
        ],
        IntentEnum.PLAN_UPGRADE: [
            r"\b(upgrade|faster speed|gigabit|switch plan|change plan|more bandwidth|mejorar plan|más velocidad|cambiar de plan)\b"
        ],
        IntentEnum.CALLBACK_SCHEDULE: [
            r"\b(call me back|callback|schedule a call|ring me later|llámame más tarde|devolver llamada|programar llamada)\b"
        ],
        IntentEnum.GRATITUDE: [
            r"\b(thank you|thanks|thank you so much|thanks a lot|many thanks|appreciate it|i appreciate it|much appreciated)\b",
            r"\b(i am good|i'm good|im good|all good|doing good|we are good|we're good|nothing else|that's all|thats all|that is all)\b",
            r"\b(gracias|muchas gracias|mil gracias|te agradezco|estoy bien gracias|todo bien gracias)\b",
            r"\b(dhanyavaad|dhanyawad|shukriya|bahut dhanyavaad)\b"
        ],
        IntentEnum.ACKNOWLEDGEMENT: [
            r"\b(okay|ok|alright|all right|got it|understood|sure thing)\b",
            r"\b(de acuerdo|vale|entendido|está bien)\b",
            r"\b(theek hai|thik hai|accha|achha|samajh gaya)\b"
        ],
        IntentEnum.CONFIRMATION_YES: [
            r"\b(yes|yeah|yep|yup|sure|correct|confirm|go ahead|sounds good|that's right|i agree|affirmative|absolutely|sí|si|correcto|de acuerdo|confirmo|adelante|haan|ha|sahi hai)\b"
        ],
        IntentEnum.CONFIRMATION_NO: [
            r"\b(no|nope|nah|cancel|negative|wrong|don't|stop|cancelar|incorrecto|parar|nahi|nahin|na|mat karo)\b",
            r"\b(no thanks|no thank you)\b"
        ]
    }

    def classify(self, text: str) -> Tuple[IntentEnum, float, Dict[str, Any]]:
        lowered = text.lower().strip()
        cleaned = re.sub(r"[^\w\s\-\']", " ", lowered)
        cleaned = " ".join(cleaned.split())
        
        # Priority 1: Direct agent escalation request
        for pattern in self.PATTERNS[IntentEnum.AGENT_ESCALATION]:
            if re.search(pattern, cleaned) and not re.search(r"\b(no|don\'t|dont|not)\s+(want|need)?\s*(an?\s+)?(agent|representative|human|operator)\b", cleaned):
                return IntentEnum.AGENT_ESCALATION, 0.98, {"trigger": "explicit_agent_keyword"}

        # Priority 2: Payment promise specific phrase
        for pattern in self.PATTERNS[IntentEnum.PAYMENT_PROMISE]:
            if re.search(pattern, cleaned):
                return IntentEnum.PAYMENT_PROMISE, 0.95, {}

        # Priority 3: Outage / Broadband triage
        for pattern in self.PATTERNS[IntentEnum.OUTAGE_TRIAGE]:
            if re.search(pattern, cleaned):
                return IntentEnum.OUTAGE_TRIAGE, 0.94, {}

        # Priority 4: Gratitude / Conversational polite response
        for pattern in self.PATTERNS[IntentEnum.GRATITUDE]:
            if re.search(pattern, cleaned):
                return IntentEnum.GRATITUDE, 0.95, {}

        # Priority 5: Acknowledgement
        for pattern in self.PATTERNS[IntentEnum.ACKNOWLEDGEMENT]:
            if re.search(pattern, cleaned):
                return IntentEnum.ACKNOWLEDGEMENT, 0.93, {}

        # Check other intent patterns
        for intent, patterns in self.PATTERNS.items():
            if intent in [
                IntentEnum.AGENT_ESCALATION,
                IntentEnum.PAYMENT_PROMISE,
                IntentEnum.OUTAGE_TRIAGE,
                IntentEnum.GRATITUDE,
                IntentEnum.ACKNOWLEDGEMENT
            ]:
                continue
            for pattern in patterns:
                if re.search(pattern, cleaned):
                    return intent, 0.92, {}

        return IntentEnum.UNKNOWN, 0.30, {}

    @staticmethod
    def get_intent_category(intent: IntentEnum) -> str:
        mapping = {
            IntentEnum.CONFIRMATION_YES: "Confirmation",
            IntentEnum.CONFIRMATION_NO: "Rejection",
            IntentEnum.GRATITUDE: "Gratitude",
            IntentEnum.ACKNOWLEDGEMENT: "Acknowledgement",
            IntentEnum.BILLING_INQUIRY: "Billing Inquiry",
            IntentEnum.PAY_BILL_NOW: "Pay Bill Now",
            IntentEnum.PAYMENT_PROMISE: "Payment Promise",
            IntentEnum.OUTAGE_TRIAGE: "Outage Triage",
            IntentEnum.PLAN_INQUIRY: "Plan Inquiry",
            IntentEnum.PLAN_UPGRADE: "Plan Upgrade",
            IntentEnum.CALLBACK_SCHEDULE: "Callback Schedule",
            IntentEnum.AGENT_ESCALATION: "Agent Escalation",
            IntentEnum.LANGUAGE_SELECT: "Language Select",
            IntentEnum.UNKNOWN: "Unknown"
        }
        return mapping.get(intent, intent.value)

intent_classifier = IntentClassifier()
