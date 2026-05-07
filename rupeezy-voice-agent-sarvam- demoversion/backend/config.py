import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env", override=False)
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
AGENT_NAME: str = os.getenv("AGENT_NAME", "Rupeezy AI Agent") or "Rupeezy AI Agent"
SESSION_TTL_MINUTES: int = int(os.getenv("SESSION_TTL_MINUTES", "30"))
FRONTEND_ORIGINS_RAW: str = os.getenv("FRONTEND_ORIGINS", os.getenv("FRONTEND_ORIGIN", ""))
FRONTEND_ORIGINS: list[str] = [
    origin.strip().rstrip("/")
    for origin in FRONTEND_ORIGINS_RAW.split(",")
    if origin.strip()
]
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
SARVAM_TTS_STREAM_URL = "https://api.sarvam.ai/text-to-speech/stream"
SARVAM_TTS_MODEL = "bulbul:v3"
SARVAM_TTS_SPEAKER = os.getenv("SARVAM_SPEAKER", "shubh") or "shubh"
SARVAM_TTS_LANGUAGE = "en-IN"
SARVAM_TTS_PACE_HINDI: float = float(os.getenv("SARVAM_TTS_PACE_HINDI", "0.92"))
SARVAM_TTS_PACE_HINGLISH: float = float(os.getenv("SARVAM_TTS_PACE_HINGLISH", "0.94"))
SARVAM_TTS_PACE_KANNADA: float = float(os.getenv("SARVAM_TTS_PACE_KANNADA", "0.88"))
SARVAM_TTS_PACE_TAMIL: float = float(os.getenv("SARVAM_TTS_PACE_TAMIL", "0.94"))
SARVAM_TTS_PACE_TELUGU: float = float(os.getenv("SARVAM_TTS_PACE_TELUGU", "0.94"))
SARVAM_TTS_PACE_ENGLISH: float = float(os.getenv("SARVAM_TTS_PACE_ENGLISH", "1.0"))
SARVAM_TTS_PACE_DEFAULT: float = float(os.getenv("SARVAM_TTS_PACE_DEFAULT", "1.0"))
SARVAM_TTS_TEMPERATURE: float = float(os.getenv("SARVAM_TTS_TEMPERATURE", "0.55"))
SARVAM_SPEAKER_HINDI: str = os.getenv("SARVAM_SPEAKER_HINDI", "dev") or "dev"
SARVAM_SPEAKER_HINGLISH: str = os.getenv("SARVAM_SPEAKER_HINGLISH", "dev") or "dev"
SARVAM_SPEAKER_KANNADA: str = os.getenv("SARVAM_SPEAKER_KANNADA", "rahul") or "rahul"
SARVAM_SPEAKER_TAMIL: str = os.getenv("SARVAM_SPEAKER_TAMIL", "rahul") or "rahul"
SARVAM_SPEAKER_TELUGU: str = os.getenv("SARVAM_SPEAKER_TELUGU", "rahul") or "rahul"
SARVAM_SPEAKER_ENGLISH: str = os.getenv("SARVAM_SPEAKER_ENGLISH", "dev") or "dev"
DEMO_WHATSAPP_NUMBER = os.getenv("DEMO_WHATSAPP_NUMBER", "")
MAX_MESSAGES_PER_SESSION = 20
EXTERNAL_API_TIMEOUT_SECONDS = 30


def _key_status(value: str) -> str:
    if not value:
        return "missing"
    if value.startswith("your_"):
        return "placeholder"
    return f"loaded ({len(value)} chars)"


print(f"[Env] GROQ_API_KEY: {_key_status(GROQ_API_KEY)}")
print(f"[Env] SARVAM_API_KEY: {_key_status(SARVAM_API_KEY)}")
print(f"[Env] SARVAM_SPEAKER: {SARVAM_TTS_SPEAKER}")
print(f"[Env] SARVAM_TTS_PACE_HINDI: {SARVAM_TTS_PACE_HINDI}")
print(f"[Env] AGENT_NAME: {AGENT_NAME}")
print(f"[Env] Groq base URL: {GROQ_BASE_URL}")
print(f"[Env] Groq model: {GROQ_MODEL}")
