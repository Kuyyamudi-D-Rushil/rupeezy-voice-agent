import base64
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env", override=False)

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"

SAMPLES = {
    "hinglish": {
        "text": "Achha sir, main simple way mein explain karta hoon.",
        "code": "hi-IN",
        "speaker": os.getenv("SARVAM_SPEAKER_HINGLISH", "dev"),
        "pace": float(os.getenv("SARVAM_TTS_PACE_HINGLISH", "0.94")),
    },
    "hindi": {
        "text": "अच्छा सर, मैं आसान तरीके से समझाता हूँ।",
        "code": "hi-IN",
        "speaker": os.getenv("SARVAM_SPEAKER_HINDI", "dev"),
        "pace": float(os.getenv("SARVAM_TTS_PACE_HINDI", "0.92")),
    },
    "kannada": {
        "text": "ನಮಸ್ಕಾರ, ನಾನು Rupeezy ಇಂದ ಮಾತಾಡ್ತಿದ್ದೀನಿ.",
        "code": "kn-IN",
        "speaker": os.getenv("SARVAM_SPEAKER_KANNADA", "rahul"),
        "pace": float(os.getenv("SARVAM_TTS_PACE_KANNADA", "0.88")),
    },
    "tamil": {
        "text": "வணக்கம், நான் Rupeezyல இருந்து பேசுறேன்.",
        "code": "ta-IN",
        "speaker": os.getenv("SARVAM_SPEAKER_TAMIL", "rahul"),
        "pace": float(os.getenv("SARVAM_TTS_PACE_TAMIL", "0.94")),
    },
    "telugu": {
        "text": "నమస్తే, నేను Rupeezy నుంచి మాట్లాడుతున్నాను.",
        "code": "te-IN",
        "speaker": os.getenv("SARVAM_SPEAKER_TELUGU", "rahul"),
        "pace": float(os.getenv("SARVAM_TTS_PACE_TELUGU", "0.94")),
    },
    "english": {
        "text": "Sure, I will explain it simply.",
        "code": "en-IN",
        "speaker": os.getenv("SARVAM_SPEAKER_ENGLISH", "dev"),
        "pace": float(os.getenv("SARVAM_TTS_PACE_ENGLISH", "1.0")),
    },
}


def main() -> None:
    if not SARVAM_API_KEY or SARVAM_API_KEY.startswith("your_"):
        raise SystemExit("SARVAM_API_KEY is missing. Add it to backend/.env first.")

    output_dir = BASE_DIR / "multilingual_samples"
    output_dir.mkdir(exist_ok=True)

    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    }

    for language, config in SAMPLES.items():
        payload = {
            "inputs": [config["text"]],
            "target_language_code": config["code"],
            "speaker": config["speaker"],
            "model": "bulbul:v3",
            "pace": config["pace"],
            "temperature": float(os.getenv("SARVAM_TTS_TEMPERATURE", "0.55")),
        }
        started = time.perf_counter()
        response = requests.post(SARVAM_TTS_URL, headers=headers, json=payload, timeout=30)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        response.raise_for_status()
        audio = base64.b64decode(response.json()["audios"][0])
        output_path = output_dir / f"{language}.wav"
        output_path.write_bytes(audio)
        print(f"{language}: {elapsed_ms} ms, {config['speaker']}, saved {output_path}")


if __name__ == "__main__":
    main()
