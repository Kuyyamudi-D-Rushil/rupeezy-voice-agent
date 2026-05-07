import os
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def test_groq() -> None:
    key = os.getenv("GROQ_API_KEY", "")
    if not key or key.startswith("your_"):
        print("[FAIL] GROQ_API_KEY is missing or a placeholder.")
        return

    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {key}"}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            print("[OK] GROQ_API_KEY is valid.")
        else:
            print(f"[FAIL] GROQ_API_KEY error: {response.status_code} - {response.text}")
    except Exception as exc:
        print(f"[FAIL] Groq connection error: {exc}")


def test_sarvam() -> None:
    key = os.getenv("SARVAM_API_KEY", "")
    if not key or key.startswith("your_"):
        print("[FAIL] SARVAM_API_KEY is missing or a placeholder.")
        return

    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": key,
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": ["Rupeezy voice test."],
        "target_language_code": "en-IN",
        "speaker": os.getenv("SARVAM_SPEAKER", "shubh") or "shubh",
        "model": "bulbul:v3",
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            audios = response.json().get("audios", [])
            if audios:
                print("[OK] SARVAM_API_KEY is valid and Sarvam TTS returned audio.")
            else:
                print("[FAIL] Sarvam TTS response did not include audio.")
        else:
            print(f"[FAIL] SARVAM_API_KEY or TTS error: {response.status_code} - {response.text}")
    except Exception as exc:
        print(f"[FAIL] Sarvam connection error: {exc}")


if __name__ == "__main__":
    print("--- Testing API Keys ---")
    test_groq()
    test_sarvam()
