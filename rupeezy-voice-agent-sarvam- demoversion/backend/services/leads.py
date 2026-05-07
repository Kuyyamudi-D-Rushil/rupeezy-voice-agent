import json
import re
from datetime import datetime, timezone
from threading import Lock

from config import BASE_DIR

DATA_DIR = BASE_DIR / "data"
LEADS_FILE = DATA_DIR / "leads.json"
_lock = Lock()


DEMO_LEAD = {
    "id": "demo-rahul-sharma",
    "name": "Rahul Sharma",
    "phone": "9876543210",
    "language_detected": "Hinglish",
    "lead_score": 82,
    "lead_status": "Hot",
    "main_objection": "Already with another broker",
    "conversation_summary": "Lead asked about brokerage sharing and daily payouts. Agent explained zero joining fee, 100% brokerage share, and RISE Portal payouts.",
    "next_action": "RM should call within 30 minutes and share AP onboarding link.",
    "handoff_status": "Ready for RM handoff",
    "transcript": "User: Mera naam Rahul Sharma hai, main financial advisor hoon. Already ek broker ke saath kaam karta hoon. Assistant: Rupeezy zero joining fee, dedicated RM support aur fast onboarding provide karta hai.",
    "timestamp": "2026-05-06T10:00:00Z",
}


def ensure_leads_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not LEADS_FILE.exists():
        LEADS_FILE.write_text("[]", encoding="utf-8")


def read_leads() -> list[dict]:
    with _lock:
        ensure_leads_file()
        try:
            data = json.loads(LEADS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = []
        return data if isinstance(data, list) else []


def write_leads(leads: list[dict]) -> None:
    with _lock:
        ensure_leads_file()
        LEADS_FILE.write_text(json.dumps(leads, indent=2, ensure_ascii=False), encoding="utf-8")


def save_lead(record: dict) -> dict:
    leads = read_leads()
    lead = normalize_lead(record)
    existing_index = next((i for i, item in enumerate(leads) if item.get("id") == lead["id"]), None)
    if existing_index is None:
        leads.append(lead)
        saved = lead
    else:
        leads[existing_index] = merge_lead(leads[existing_index], lead)
        saved = leads[existing_index]
    write_leads(leads)
    return saved


def seed_demo_lead() -> dict:
    return save_lead(DEMO_LEAD)


def build_lead_from_conversation(session_id: str, history: list[dict], analysis: dict) -> dict:
    transcript = format_transcript(history)
    return normalize_lead(
        {
            "id": session_id,
            "name": extract_name(transcript),
            "phone": extract_phone(transcript),
            "transcript": transcript,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **analysis,
        }
    )


def fallback_analysis(history: list[dict]) -> dict:
    transcript = format_transcript(history)
    summary = "Conversation captured, but AI lead analysis failed. RM should review transcript before follow-up."
    if transcript:
        summary = f"Conversation captured for RM review. Latest context: {transcript[-220:]}"
    return {
        "lead_score": 55,
        "lead_status": "Warm",
        "language_detected": "Hinglish",
        "main_objection": "Needs manual review",
        "conversation_summary": summary,
        "next_action": "RM should review transcript and call the lead for qualification.",
        "handoff_status": "Needs RM review",
    }


def normalize_lead(record: dict) -> dict:
    score = _to_int(record.get("lead_score"), 55)
    score = max(0, min(100, score))
    status = _status_for_score(score)
    return {
        "id": str(record.get("id") or f"lead_{int(datetime.now(timezone.utc).timestamp() * 1000)}"),
        "name": str(record.get("name") or "Unknown Lead"),
        "phone": str(record.get("phone") or "Not captured"),
        "language_detected": str(record.get("language_detected") or "Unknown"),
        "lead_score": score,
        "lead_status": status,
        "main_objection": str(record.get("main_objection") or "Not captured"),
        "conversation_summary": str(record.get("conversation_summary") or "No summary available."),
        "next_action": str(record.get("next_action") or "RM should review and follow up."),
        "handoff_status": str(record.get("handoff_status") or "Needs RM review"),
        "transcript": str(record.get("transcript") or ""),
        "timestamp": str(record.get("timestamp") or datetime.now(timezone.utc).isoformat()),
    }


def merge_lead(existing: dict, incoming: dict) -> dict:
    merged = {**existing, **incoming}
    if _is_unknown_name(incoming.get("name")) and not _is_unknown_name(existing.get("name")):
        merged["name"] = existing["name"]
    if _is_unknown_phone(incoming.get("phone")) and not _is_unknown_phone(existing.get("phone")):
        merged["phone"] = existing["phone"]
    return merged


def format_transcript(history: list[dict]) -> str:
    lines = []
    for item in history:
        role = "RM Agent" if item.get("role") == "assistant" else "Lead"
        content = str(item.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def extract_phone(text: str) -> str:
    match = re.search(r"(?:\+91[\s-]?)?[6-9][\d\s-]{9,12}", text)
    if not match:
        return "Not captured"
    digits = re.sub(r"\D", "", match.group(0))
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    return digits if len(digits) == 10 else "Not captured"


def extract_name(text: str) -> str:
    patterns = [
        r"\b(?:mera naam|my name is|i am|i'm|this is)\s+([a-zA-Z][a-zA-Z.'-]*(?:\s+[a-zA-Z][a-zA-Z.'-]*){0,2})",
        r"\b(?:naam hai|name is)\s+([a-zA-Z][a-zA-Z.'-]*(?:\s+[a-zA-Z][a-zA-Z.'-]*){0,2})",
        r"\bmain\s+([a-zA-Z][a-zA-Z.'-]*(?:\s+[a-zA-Z][a-zA-Z.'-]*){0,2})\s+(?:hoon|hu|hun)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            name = _clean_name(match.group(1))
            if name:
                return name
    return "Unknown Lead"


def _clean_name(value: str) -> str:
    stop_words = {
        "and",
        "aur",
        "from",
        "se",
        "hai",
        "hoon",
        "hu",
        "hun",
        "main",
        "financial",
        "advisor",
        "mfd",
    }
    parts = []
    for word in re.findall(r"[a-zA-Z][a-zA-Z.'-]*", value):
        if word.lower() in stop_words:
            break
        parts.append(word)
    return " ".join(parts).strip().title()


def _is_unknown_name(value) -> bool:
    return not value or str(value).strip().lower() == "unknown lead"


def _is_unknown_phone(value) -> bool:
    return not value or str(value).strip().lower() == "not captured"


def _to_int(value, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _status_for_score(score: int) -> str:
    if score >= 75:
        return "Hot"
    if score >= 40:
        return "Warm"
    return "Cold"
