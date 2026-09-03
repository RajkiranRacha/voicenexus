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
            r"\b(agent|representative|human|operator|real person|someone else|speak to a person|transfer me|supervisor)\b"
        ],
        IntentEnum.PAYMENT_PROMISE: [
            r"\b(pay later|payment arrangement|payment promise|extension|need more time to pay|promise to pay|schedule a payment|pay next week)\b"
        ],
        IntentEnum.BILLING_INQUIRY: [
            r"\b(bill|balance|how much do i owe|charges|amount due|statement|payment due|due date|invoice|split payment|two cards|two credit cards)\b",
            r"\b(pay|payment)\b"
        ],
        IntentEnum.OUTAGE_TRIAGE: [
            r"\b(outage|wifi not working|no connection|offline|blinking red|lost connection|slow internet|broadband down|troubleshoot)\b",
            r"\b(internet|wifi|broadband|connection|fiber)\b.*\b(down|out|off|slow|broken|dead|unreachable)\b",
            r"\b(down|outage)\b.*\b(internet|wifi|broadband|connection)\b"
        ],
        IntentEnum.PLAN_INQUIRY: [
            r"\b(what plan am i on|current plan|plan details|data limit|my package)\b"
        ],
        IntentEnum.PLAN_UPGRADE: [
            r"\b(upgrade|faster speed|gigabit|switch plan|change plan|more bandwidth)\b"
        ],
        IntentEnum.CALLBACK_SCHEDULE: [
            r"\b(call me back|callback|schedule a call|ring me later)\b"
        ],
        IntentEnum.CONFIRMATION_YES: [
            r"\b(yes|yeah|yep|sure|correct|confirm|go ahead|sounds good|that's right|i agree)\b"
        ],
        IntentEnum.CONFIRMATION_NO: [
            r"\b(no|nope|cancel|negative|wrong|don't|stop)\b"
        ]
    }

    def classify(self, text: str) -> Tuple[IntentEnum, float, Dict[str, Any]]:
        lowered = text.lower().strip()
        
        # Priority 1: Direct agent escalation request
        for pattern in self.PATTERNS[IntentEnum.AGENT_ESCALATION]:
            if re.search(pattern, lowered):
                return IntentEnum.AGENT_ESCALATION, 0.98, {"trigger": "explicit_agent_keyword"}

        # Priority 2: Payment promise specific phrase
        for pattern in self.PATTERNS[IntentEnum.PAYMENT_PROMISE]:
            if re.search(pattern, lowered):
                return IntentEnum.PAYMENT_PROMISE, 0.95, {}

        # Priority 3: Outage / Broadband triage
        for pattern in self.PATTERNS[IntentEnum.OUTAGE_TRIAGE]:
            if re.search(pattern, lowered):
                return IntentEnum.OUTAGE_TRIAGE, 0.94, {}

        # Check other intent patterns
        for intent, patterns in self.PATTERNS.items():
            if intent in [IntentEnum.AGENT_ESCALATION, IntentEnum.PAYMENT_PROMISE, IntentEnum.OUTAGE_TRIAGE]:
                continue
            for pattern in patterns:
                if re.search(pattern, lowered):
                    return intent, 0.92, {}

        return IntentEnum.UNKNOWN, 0.30, {}

intent_classifier = IntentClassifier()
