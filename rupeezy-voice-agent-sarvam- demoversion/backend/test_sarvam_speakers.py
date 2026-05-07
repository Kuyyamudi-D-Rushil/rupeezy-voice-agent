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
SPEAKERS = ["sunny", "rahul", "dev"]
SAMPLE_TEXT = (
    "Haan Rohini, samajh gaya. Rupeezy ke saath partner banne ke liye "
    "zero investment hai. Aap abhi kya kaam karte hain?"
)


def main() -> None:
    if not SARVAM_API_KEY or SARVAM_API_KEY.startswith("your_"):
        raise SystemExit("SARVAM_API_KEY is missing. Add it to backend/.env first.")

    output_dir = BASE_DIR / "speaker_samples"
    output_dir.mkdir(exist_ok=True)

    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    }

    for speaker in SPEAKERS:
        payload = {
            "inputs": [SAMPLE_TEXT],
            "target_language_code": "hi-IN",
            "speaker": speaker,
            "model": "bulbul:v3",
            "pace": 0.92,
            "temperature": 0.55,
        }
        started = time.perf_counter()
        response = requests.post(SARVAM_TTS_URL, headers=headers, json=payload, timeout=30)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        response.raise_for_status()
        audio = base64.b64decode(response.json()["audios"][0])
        output_path = output_dir / f"{speaker}.wav"
        output_path.write_bytes(audio)
        print(f"{speaker}: {elapsed_ms} ms, saved {output_path}")


if __name__ == "__main__":
    main()
