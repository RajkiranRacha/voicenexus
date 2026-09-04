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
            r"(?<!\S)(agent|representative|human|operator|real person|someone else|speak to a person|transfer me|supervisor|representante|agente|operador|persona real|humano|एजेंट|प्रतिनिधि|इंसान|व्यक्ति से बात|असली आदमी|सुपरवाइज़र|मानव)(?!\S)"
        ],
        IntentEnum.LANGUAGE_SELECT: [
            r"(?<!\S)(spanish|español|habla español|en español|switch to spanish|cambiar a español|english|inglés|switch to english|idioma español|hindi|हिंदी|हिन्दी|switch to hindi|hindi mein|hindi me|hindi bolo)(?!\S)"
        ],
        IntentEnum.PAY_BILL_NOW: [
            r"(?<!\S)(pay now|pay bill now|pay my bill|pay my balance|make a payment|pay the balance|charge my card|pay balance|process payment|pay it|pagar ahora|pagar mi factura|hacer un pago|अभी भुगतान|बिल का भुगतान अभी|पेमेंट करो|अभी पे करना है|कार्ड से भुगतान)(?!\S)",
            r"(?<!\S)pay(\s+\S+){0,3}\s+(now|right now|today)(?!\S)",
            r"(?<!\S)charge\s+my(\s+\S+){0,2}\s+card(?!\S)"
        ],
        IntentEnum.PAYMENT_PROMISE: [
            r"(?<!\S)(pay later|payment arrangement|payment promise|extension|need more time to pay|promise to pay|schedule a payment|pay next week|promesa de pago|acuerdo de pago|pagar la próxima semana|बाद में भुगतान|पेमेंट प्लान|समय चाहिए|अगले हफ्ते भुगतान|किस्तों में भुगतान)(?!\S)"
        ],
        IntentEnum.BILLING_INQUIRY: [
            r"(?<!\S)(bill|balance|how much do i owe|charges|amount due|statement|payment due|due date|invoice|split payment|two cards|two credit cards|factura|saldo|cuánto debo|estado de cuenta|recibo|बिल|बकाया|कितना बकाया है|मेरा बिल कितना|भुगतान की तारीख|खाते का विवरण)(?!\S)",
            r"(?<!\S)(pay|payment|pago|भुगतान|पेमेंट)(?!\S)"
        ],
        IntentEnum.OUTAGE_TRIAGE: [
            r"(?<!\S)(outage|wifi not working|no connection|offline|blinking red|lost connection|slow internet|broadband down|troubleshoot|sin internet|no hay internet|no tengo internet|no tengo wifi|no tengo señal|se cayó el internet|no funciona el wifi|corte de servicio|avería|इंटरनेट नहीं चल रहा|वाईफाई काम नहीं|कनेक्शन नहीं|इंटरनेट बंद|नेटवर्क खराब|इंटरनेट धीमा)(?!\S)",
            r"(?<!\S)(internet|wifi|broadband|connection|fiber|red|इंटरनेट|वाईफाई)(?!\S).*(?<!\S)(down|out|off|slow|broken|dead|die[ds]?|unreachable|caído|murió|lento|apagado|बंद|खराब|नहीं)(?!\S)",
            r"(?<!\S)(down|outage|caído|बंद|खराब)(?!\S).*(?<!\S)(internet|wifi|broadband|connection|red|इंटरनेट|वाईफाई)(?!\S)"
        ],
        IntentEnum.PLAN_INQUIRY: [
            r"(?<!\S)(what plan am i on|current plan|plan details|data limit|my package|qué plan tengo|detalles de mi plan|मेरा प्लान क्या है|कौन सा प्लान|प्लान की जानकारी|डेटा लिमिट)(?!\S)"
        ],
        IntentEnum.PLAN_UPGRADE: [
            r"(?<!\S)(upgrade|faster speed|gigabit|switch plan|change plan|more bandwidth|mejorar plan|más velocidad|cambiar de plan|अपग्रेड|तेज़ स्पीड|प्लान बदलना|ज़्यादा स्पीड|गीगाबिट)(?!\S)"
        ],
        IntentEnum.CALLBACK_SCHEDULE: [
            r"(?<!\S)(call me back|callback|schedule a call|ring me later|llámame más tarde|devolver llamada|programar llamada|मुझे वापस कॉल करें|कॉलबैक|बाद में कॉल करें|फिर से कॉल)(?!\S)"
        ],
        IntentEnum.GRATITUDE: [
            r"(?<!\S)(thank you|thanks|thank you so much|thanks a lot|many thanks|appreciate it|i appreciate it|much appreciated)(?!\S)",
            r"(?<!\S)(i am good|i'm good|im good|all good|doing good|we are good|we're good|nothing else|that's all|thats all|that is all)(?!\S)",
            r"(?<!\S)(gracias|muchas gracias|mil gracias|te agradezco|estoy bien gracias|todo bien gracias)(?!\S)",
            r"(?<!\S)(dhanyavaad|dhanyawad|shukriya|bahut dhanyavaad)(?!\S)"
        ],
        IntentEnum.ACKNOWLEDGEMENT: [
            r"(?<!\S)(okay|ok|alright|all right|got it|understood|sure thing)(?!\S)",
            r"(?<!\S)(vale|entendido|está bien)(?!\S)",
            r"(?<!\S)(theek hai|thik hai|accha|achha|samajh gaya)(?!\S)"
        ],
        IntentEnum.CONFIRMATION_YES: [
            r"(?<!\S)(yes|yeah|yep|yup|sure|correct|confirm|go ahead|sounds good|that's right|i agree|affirmative|absolutely|sí|si|correcto|de acuerdo|confirmo|adelante|haan|ha|sahi hai)(?!\S)"
        ],
        IntentEnum.CONFIRMATION_NO: [
            r"(?<!\S)(no|nope|nah|cancel|negative|wrong|don't|stop|cancelar|incorrecto|parar|nahi|nahin|na|mat karo)(?!\S)",
            r"(?<!\S)(no thanks|no thank you)(?!\S)"
        ]
    }

    def classify(self, text: str) -> Tuple[IntentEnum, float, Dict[str, Any]]:
        lowered = text.lower().strip()
        # NOTE: \w alone does not cover Devanagari combining marks (matras, virama,
        # anusvara/visarga -- Unicode category Mn/Mc), so a plain [^\w\s...] filter
        # silently mangles Hindi words (e.g. "है" -> "ह"). Explicitly keep the full
        # Devanagari block (U+0900-U+097F) alongside \w so Hindi utterances survive
        # this normalization pass intact.
        cleaned = re.sub(r"[^\w\s\-\'ऀ-ॿ]", " ", lowered)
        cleaned = " ".join(cleaned.split())
        
        # Priority 1: Direct agent escalation request
        for pattern in self.PATTERNS[IntentEnum.AGENT_ESCALATION]:
            if re.search(pattern, cleaned) and not re.search(r"(?<!\S)(no|don\'t|dont|not)\s+(want|need)?\s*(an?\s+)?(agent|representative|human|operator)(?!\S)", cleaned):
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
