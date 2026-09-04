import pytest
from app.models.schemas import IntentEnum
from app.engine.intent_classifier import intent_classifier

# Operator-curated benchmark dataset of representative customer utterances
EVAL_DATASET = [
    # BILLING_INQUIRY
    ("How much is my bill this month?", IntentEnum.BILLING_INQUIRY),
    ("What is my current account balance?", IntentEnum.BILLING_INQUIRY),
    ("When is my payment due date?", IntentEnum.BILLING_INQUIRY),
    ("Can I get a copy of my invoice?", IntentEnum.BILLING_INQUIRY),
    ("Why is my statement higher than usual?", IntentEnum.BILLING_INQUIRY),
    ("¿Cuál es el saldo de mi factura?", IntentEnum.BILLING_INQUIRY),
    ("Quiero saber cuánto debo en mi recibo", IntentEnum.BILLING_INQUIRY),

    # PAY_BILL_NOW
    ("I want to pay my bill now using the card on file", IntentEnum.PAY_BILL_NOW),
    ("Pay my balance right now", IntentEnum.PAY_BILL_NOW),
    ("Charge my debit card for the full amount due", IntentEnum.PAY_BILL_NOW),
    ("Make a payment today", IntentEnum.PAY_BILL_NOW),
    ("Can I pay it now?", IntentEnum.PAY_BILL_NOW),
    ("Quiero pagar mi factura ahora", IntentEnum.PAY_BILL_NOW),
    ("Hacer un pago hoy", IntentEnum.PAY_BILL_NOW),

    # PAYMENT_PROMISE
    ("Can I set up a payment arrangement?", IntentEnum.PAYMENT_PROMISE),
    ("I need an extension until next Friday to pay", IntentEnum.PAYMENT_PROMISE),
    ("I want to pay later next week", IntentEnum.PAYMENT_PROMISE),
    ("Promise to pay on the 15th", IntentEnum.PAYMENT_PROMISE),
    ("Can I schedule a payment for next Tuesday?", IntentEnum.PAYMENT_PROMISE),
    ("Necesito un acuerdo de pago para la próxima semana", IntentEnum.PAYMENT_PROMISE),

    # OUTAGE_TRIAGE
    ("My internet is completely down", IntentEnum.OUTAGE_TRIAGE),
    ("Is there an outage in my area?", IntentEnum.OUTAGE_TRIAGE),
    ("The wifi router is blinking red and has no connection", IntentEnum.OUTAGE_TRIAGE),
    ("Our broadband connection died twenty minutes ago", IntentEnum.OUTAGE_TRIAGE),
    ("Why is my fiber internet offline?", IntentEnum.OUTAGE_TRIAGE),
    ("Troubleshoot my broken connection", IntentEnum.OUTAGE_TRIAGE),
    ("No tengo internet en mi casa", IntentEnum.OUTAGE_TRIAGE),
    ("Se cayó el internet de fibra", IntentEnum.OUTAGE_TRIAGE),

    # PLAN_INQUIRY
    ("What plan am I on currently?", IntentEnum.PLAN_INQUIRY),
    ("Can you tell me my current plan details?", IntentEnum.PLAN_INQUIRY),
    ("What is the data limit on my package?", IntentEnum.PLAN_INQUIRY),
    ("¿Qué plan tengo contratado?", IntentEnum.PLAN_INQUIRY),

    # PLAN_UPGRADE
    ("I want to upgrade to faster speed", IntentEnum.PLAN_UPGRADE),
    ("Can I switch plan to gigabit internet?", IntentEnum.PLAN_UPGRADE),
    ("I need more bandwidth for work", IntentEnum.PLAN_UPGRADE),
    ("Upgrade my fiber speed package", IntentEnum.PLAN_UPGRADE),
    ("Quiero más velocidad en mi servicio", IntentEnum.PLAN_UPGRADE),

    # CALLBACK_SCHEDULE
    ("Can someone call me back later today?", IntentEnum.CALLBACK_SCHEDULE),
    ("I don't have time to wait, schedule a callback", IntentEnum.CALLBACK_SCHEDULE),
    ("Ring me later this afternoon", IntentEnum.CALLBACK_SCHEDULE),
    ("Por favor llámame más tarde", IntentEnum.CALLBACK_SCHEDULE),

    # AGENT_ESCALATION
    ("I want to speak with a human representative", IntentEnum.AGENT_ESCALATION),
    ("Transfer me to an operator right away", IntentEnum.AGENT_ESCALATION),
    ("Let me talk to a real person", IntentEnum.AGENT_ESCALATION),
    ("I need a supervisor immediately", IntentEnum.AGENT_ESCALATION),
    ("Quiero hablar con un agente humano", IntentEnum.AGENT_ESCALATION),
    ("Pásame con un representante", IntentEnum.AGENT_ESCALATION),

    # LANGUAGE_SELECT
    ("Can we speak in Spanish?", IntentEnum.LANGUAGE_SELECT),
    ("Quiero hablar en español", IntentEnum.LANGUAGE_SELECT),
    ("Switch language to English please", IntentEnum.LANGUAGE_SELECT),
    ("Cambiar a español", IntentEnum.LANGUAGE_SELECT),

    # CONFIRMATION_YES
    ("Yes, go ahead and confirm", IntentEnum.CONFIRMATION_YES),
    ("Sounds good, I agree", IntentEnum.CONFIRMATION_YES),
    ("That's right, please proceed", IntentEnum.CONFIRMATION_YES),
    ("Sí, de acuerdo", IntentEnum.CONFIRMATION_YES),

    # CONFIRMATION_NO
    ("No, cancel that request", IntentEnum.CONFIRMATION_NO),
    ("Wrong, don't do that", IntentEnum.CONFIRMATION_NO),
    ("No quiero continuar", IntentEnum.CONFIRMATION_NO),

    # UNKNOWN (Out of domain / gibberish)
    ("What is the weather in Honolulu today?", IntentEnum.UNKNOWN),
    ("Tell me a recipe for chocolate chip cookies", IntentEnum.UNKNOWN),
    ("blorp zip zop flim flam", IntentEnum.UNKNOWN),

    # Hindi (hi-IN) — task intents
    ("मेरा बिल कितना है?", IntentEnum.BILLING_INQUIRY),
    ("मेरा बकाया कितना है", IntentEnum.BILLING_INQUIRY),
    ("मुझे अभी अपने कार्ड से भुगतान करना है", IntentEnum.PAY_BILL_NOW),
    ("मुझे बाद में भुगतान करने के लिए समय चाहिए", IntentEnum.PAYMENT_PROMISE),
    ("मेरा इंटरनेट नहीं चल रहा है", IntentEnum.OUTAGE_TRIAGE),
    ("वाईफाई काम नहीं कर रहा", IntentEnum.OUTAGE_TRIAGE),
    ("मेरा प्लान क्या है", IntentEnum.PLAN_INQUIRY),
    ("मुझे तेज़ स्पीड में अपग्रेड करना है", IntentEnum.PLAN_UPGRADE),
    ("मुझे वापस कॉल करें", IntentEnum.CALLBACK_SCHEDULE),
    ("मुझे किसी एजेंट से बात करनी है", IntentEnum.AGENT_ESCALATION),
    ("मुझे एक इंसान से बात करनी है", IntentEnum.AGENT_ESCALATION),
]

def test_intent_classification_f1_benchmark():
    """
    Tests intent classification accuracy against the PRD requirement:
    VN-NonFunctional: 'Intent classification F1 >= 0.90 on operator-curated eval set per supported language.'
    """
    intents = list(IntentEnum)
    tp = {i: 0 for i in intents}
    fp = {i: 0 for i in intents}
    fn = {i: 0 for i in intents}

    total = len(EVAL_DATASET)
    correct = 0

    for text, ground_truth in EVAL_DATASET:
        predicted, conf, _ = intent_classifier.classify(text)
        if predicted == ground_truth:
            correct += 1
            tp[ground_truth] += 1
        else:
            fp[predicted] += 1
            fn[ground_truth] += 1

    accuracy = correct / total

    # Compute F1 per class and macro F1
    f1_scores = []
    classes_tested = set(gt for _, gt in EVAL_DATASET)
    for c in classes_tested:
        precision = tp[c] / (tp[c] + fp[c]) if (tp[c] + fp[c]) > 0 else 0.0
        recall = tp[c] / (tp[c] + fn[c]) if (tp[c] + fn[c]) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        f1_scores.append(f1)

    macro_f1 = sum(f1_scores) / len(f1_scores)

    print(f"\n[BENCHMARK] Total Eval Items: {total}")
    print(f"[BENCHMARK] Overall Accuracy: {accuracy * 100:.2f}% ({correct}/{total})")
    print(f"[BENCHMARK] Macro-Averaged F1: {macro_f1:.4f} (PRD Target: >= 0.90)")

    assert macro_f1 >= 0.90, f"Macro F1 was {macro_f1:.4f}, which is below the required 0.90 threshold!"
    assert accuracy >= 0.90, f"Overall accuracy was {accuracy * 100:.2f}%, below 90%!"
