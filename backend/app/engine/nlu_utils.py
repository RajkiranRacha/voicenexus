"""
Shared trilingual affirmative/negative detection used by the goal-directed
subflows (engine/flows/*.py) for confirm-before-commit prompts. Consolidates
word lists that were previously redeclared per-flow.
"""

AFFIRMATIVE_WORDS = [
    "yes", "yeah", "yep", "yup", "sure", "correct", "confirm", "go ahead", "sounds good",
    "that's right", "i agree", "affirmative", "absolutely", "ok", "okay", "please",
    "book", "schedule", "tomorrow", "pay", "charge", "perfect",
    "sí", "si", "correcto", "de acuerdo", "confirmo", "adelante", "por favor", "claro",
    "pagar", "perfecto", "vale", "mañana",
    "haan", "ha", "theek hai", "thik hai", "sahi hai", "karo", "kal",
]

NEGATIVE_WORDS = [
    "no", "nope", "nah", "cancel", "negative", "wrong", "don't", "dont", "stop", "change",
    "no thanks", "no thank you",
    "cancelar", "incorrecto", "parar", "cambiar",
    "nahi", "nahin", "na", "mat karo", "rad karo",
]


def is_affirmative(text: str, lang: str = "en-US") -> bool:
    lowered = text.lower()
    return any(term in lowered for term in AFFIRMATIVE_WORDS)


def is_negative(text: str, lang: str = "en-US") -> bool:
    lowered = text.lower()
    return any(term in lowered for term in NEGATIVE_WORDS)
