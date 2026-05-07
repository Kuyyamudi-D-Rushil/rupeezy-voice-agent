import re


SUPPORTED_LANGUAGES = {"hinglish", "hindi", "kannada", "tamil", "telugu", "english"}
UI_LANGUAGE_MAP = {
    "auto": "auto",
    "hinglish": "hinglish",
    "hindi": "hindi",
    "kannada": "kannada",
    "tamil": "tamil",
    "telugu": "telugu",
    "english": "english",
}

SCRIPT_PATTERNS = {
    "hindi": re.compile(r"[\u0900-\u097F]"),
    "kannada": re.compile(r"[\u0C80-\u0CFF]"),
    "tamil": re.compile(r"[\u0B80-\u0BFF]"),
    "telugu": re.compile(r"[\u0C00-\u0C7F]"),
}

ROMAN_LANGUAGE_HINTS = {
    "kannada": {
        "namaskara", "nanu", "naanu", "maatad", "maatadthiddini", "heli", "sari",
        "swalpa", "nimma", "neevu", "ideya", "beku", "illa", "gothu", "bengaluru",
        "kannada",
    },
    "tamil": {
        "vanakkam", "naan", "pesuren", "pesunga", "sollunga", "seri", "konjam",
        "unga", "neenga", "irukka", "venum", "illa", "theriyum", "chennai", "tamil",
    },
    "telugu": {
        "nenu", "matladutunna", "cheppandi", "sare", "konchem",
        "mee", "meeru", "unda", "kavali", "ledu", "telusu", "hyderabad", "telugu",
    },
    "hinglish": {
        "haan", "achha", "accha", "theek", "thik", "kya", "kaam", "karte", "karta",
        "hoon", "hun", "hai", "nahi", "nahin", "batao", "samajh", "chahiye",
        "paisa", "investment", "interest", "sir", "madam",
    },
}

ENGLISH_HINTS = {
    "hello", "hi", "thanks", "thank", "please", "interested", "investment", "finance",
    "advisor", "student", "career", "business", "english",
}


def normalize_language(language: str | None) -> str:
    value = (language or "auto").strip().lower()
    return UI_LANGUAGE_MAP.get(value, "auto")


def detect_language(message: str, requested_language: str = "auto", previous_language: str = "hinglish") -> str:
    requested = normalize_language(requested_language)
    if requested != "auto":
        return requested

    text = (message or "").strip()
    if not text:
        return previous_language if previous_language in SUPPORTED_LANGUAGES else "hinglish"

    for language, pattern in SCRIPT_PATTERNS.items():
        if pattern.search(text):
            return language

    lowered = re.sub(r"[^a-zA-Z\s]", " ", text).lower()
    words = set(lowered.split())
    scores = {
        language: len(words & hints)
        for language, hints in ROMAN_LANGUAGE_HINTS.items()
    }
    if scores:
        best_language, best_score = max(scores.items(), key=lambda item: item[1])
        if best_score >= 1:
            return best_language

    if len(words & ENGLISH_HINTS) >= 1 and not re.search(r"\b(kya|hai|hoon|hun|nahi|nahin|kaam)\b", lowered):
        return "english"

    return previous_language if previous_language in SUPPORTED_LANGUAGES else "hinglish"
