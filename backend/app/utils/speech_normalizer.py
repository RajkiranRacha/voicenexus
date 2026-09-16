import re
from typing import Optional

WORD_TO_DIGIT = {
    "zero": "0", "oh": "0", "o": "0",
    "one": "1", "won": "1",
    "two": "2", "to": "2", "too": "2",
    "three": "3", "tree": "3",
    "four": "4", "for": "4", "fore": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8", "ate": "8",
    "nine": "9", "niner": "9"
}

MULTIPLIERS = {
    "double": 2,
    "triple": 3
}

def normalize_spoken_digits(text: str) -> str:
    """
    Converts spoken word representations of numbers into digits.
    Handles:
      'five five five' -> '555'
      'triple five' -> '555'
      'double two' -> '22'
      'nine four one zero seven' -> '94107'
      'ACC nine nine two zero one four X' -> 'ACC-992014-X'
    """
    if not text:
        return ""

    tokens = re.findall(r"[A-Za-z0-9]+", str(text).lower())
    result = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        # Multiplier check (double five -> 55, triple zero -> 000)
        if token in MULTIPLIERS and i + 1 < len(tokens):
            multiplier = MULTIPLIERS[token]
            next_token = tokens[i + 1]
            if next_token in WORD_TO_DIGIT:
                result.append(WORD_TO_DIGIT[next_token] * multiplier)
                i += 2
                continue
            elif next_token.isdigit() and len(next_token) == 1:
                result.append(next_token * multiplier)
                i += 2
                continue

        if token in WORD_TO_DIGIT:
            result.append(WORD_TO_DIGIT[token])
        elif token.isdigit():
            result.append(token)
        else:
            result.append(token.upper())
        i += 1

    return "".join(result)

def extract_digits(text: str) -> str:
    """Extracts pure digit sequence from text, converting any number words first."""
    normalized = normalize_spoken_digits(text)
    return "".join(filter(str.isdigit, normalized))

def clean_account_number(text: str) -> str:
    """
    Normalizes spoken or typed account numbers into simple numeric format.
    E.g. '1001' -> '1001'
         'acc 1001' -> '1001'
         'ACC-1001' -> '1001'
         'one zero zero one' -> '1001'
    """
    if not text:
        return ""
    digits = extract_digits(text)
    if digits:
        return digits
    normalized = normalize_spoken_digits(text).upper()
    cleaned = re.sub(r"[^A-Z0-9]", "", normalized)
    return cleaned or text.strip().upper()

def clean_zip_code(text: str) -> str:
    """Extracts a 5-digit US zip code from spoken or typed text."""
    digits = extract_digits(text)
    if len(digits) >= 5:
        return digits[:5]
    return digits
