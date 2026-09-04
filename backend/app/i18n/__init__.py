from app.i18n.strings import STRINGS


def resolve_lang(lang: str) -> str:
    """
    Resolves a full language/locale tag (e.g. "es-US", "hi-IN") to the short
    key used in STRINGS ("es", "hi", "en"), reusing the same prefix convention
    already used throughout the engine (lang.startswith("es"/"hi")).
    """
    if lang.startswith("es"):
        return "es"
    if lang.startswith("hi"):
        return "hi"
    return "en"


def t(key: str, lang: str, **kwargs) -> str:
    """
    Looks up a localized message template by key and language, then formats
    it with the given keyword arguments.
    """
    entry = STRINGS[key]
    template = entry.get(resolve_lang(lang), entry.get("en"))
    return template.format(**kwargs) if kwargs else template
