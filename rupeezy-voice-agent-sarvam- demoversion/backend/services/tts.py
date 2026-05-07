import base64
import re

import requests
from config import (
    EXTERNAL_API_TIMEOUT_SECONDS,
    SARVAM_API_KEY,
    SARVAM_SPEAKER_ENGLISH,
    SARVAM_SPEAKER_HINDI,
    SARVAM_SPEAKER_HINGLISH,
    SARVAM_SPEAKER_KANNADA,
    SARVAM_SPEAKER_TAMIL,
    SARVAM_SPEAKER_TELUGU,
    SARVAM_TTS_PACE_DEFAULT,
    SARVAM_TTS_PACE_ENGLISH,
    SARVAM_TTS_PACE_HINDI,
    SARVAM_TTS_PACE_HINGLISH,
    SARVAM_TTS_PACE_KANNADA,
    SARVAM_TTS_PACE_TAMIL,
    SARVAM_TTS_PACE_TELUGU,
    SARVAM_TTS_LANGUAGE,
    SARVAM_TTS_MODEL,
    SARVAM_TTS_SPEAKER,
    SARVAM_TTS_STREAM_URL,
    SARVAM_TTS_TEMPERATURE,
    SARVAM_TTS_URL,
)

LANGUAGE_TO_SARVAM = {
    "hinglish": "hi-IN",
    "english": "en-IN",
    "hindi": "hi-IN",
    "kannada": "kn-IN",
    "tamil": "ta-IN",
    "telugu": "te-IN",
}

LANGUAGE_TTS_PROFILES = {
    "hinglish": {"speaker": SARVAM_SPEAKER_HINGLISH, "pace": SARVAM_TTS_PACE_HINGLISH},
    "hindi": {"speaker": SARVAM_SPEAKER_HINDI, "pace": SARVAM_TTS_PACE_HINDI},
    "kannada": {"speaker": SARVAM_SPEAKER_KANNADA, "pace": SARVAM_TTS_PACE_KANNADA},
    "tamil": {"speaker": SARVAM_SPEAKER_TAMIL, "pace": SARVAM_TTS_PACE_TAMIL},
    "telugu": {"speaker": SARVAM_SPEAKER_TELUGU, "pace": SARVAM_TTS_PACE_TELUGU},
    "english": {"speaker": SARVAM_SPEAKER_ENGLISH, "pace": SARVAM_TTS_PACE_ENGLISH},
}


def clean_tts_text(text: str) -> str:
    cleaned = re.sub(r"[*_`#>\[\]{}]", "", text or "")
    cleaned = re.sub(r"\s*\n+\s*", " ", cleaned)
    cleaned = re.sub(r",{2,}", ",", cleaned)
    cleaned = re.sub(r"\s*,\s*", ", ", cleaned)
    cleaned = re.sub(r"([.!?\u0964\u0965\u3002]){2,}", r"\1", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    sentences = re.findall(r"[^.!?\u0964\u0965\u3002]+[.!?\u0964\u0965\u3002]?", cleaned)
    result = " ".join(sentence.strip() for sentence in sentences[:2] if sentence.strip())
    return result or cleaned


def sarvam_language_for(text: str, selected_language: str = "auto") -> str:
    if selected_language in LANGUAGE_TO_SARVAM:
        return LANGUAGE_TO_SARVAM[selected_language]
    if selected_language == "hinglish":
        return "hi-IN"
    if re.search(r"[\u0C80-\u0CFF]", text):
        return "kn-IN"
    if re.search(r"[\u0B80-\u0BFF]", text):
        return "ta-IN"
    if re.search(r"[\u0C00-\u0C7F]", text):
        return "te-IN"
    if re.search(r"[\u0900-\u097F]", text):
        return "hi-IN"
    if re.search(r"[\u0A80-\u0AFF]", text):
        return "gu-IN"
    if re.search(r"[\u0980-\u09FF]", text):
        return "bn-IN"
    return SARVAM_TTS_LANGUAGE


def pace_for(text: str, selected_language: str = "auto") -> float:
    profile = LANGUAGE_TTS_PROFILES.get(selected_language)
    if profile:
        return profile["pace"]
    return SARVAM_TTS_PACE_DEFAULT


def speaker_for(selected_language: str = "auto", speaker: str | None = None) -> str:
    if speaker:
        return speaker.lower()
    profile = LANGUAGE_TTS_PROFILES.get(selected_language)
    if profile:
        return profile["speaker"].lower()
    return SARVAM_TTS_SPEAKER.lower()


def build_rest_payload(text: str, selected_language: str = "auto", speaker: str | None = None) -> dict:
    tts_text = clean_tts_text(text)
    return {
        "inputs": [tts_text],
        "target_language_code": sarvam_language_for(tts_text, selected_language),
        "speaker": speaker_for(selected_language, speaker),
        "model": SARVAM_TTS_MODEL,
        "pace": pace_for(tts_text, selected_language),
        "temperature": SARVAM_TTS_TEMPERATURE,
    }


def build_stream_payload(text: str, selected_language: str = "auto", speaker: str | None = None) -> dict:
    tts_text = clean_tts_text(text)
    return {
        "text": tts_text,
        "target_language_code": sarvam_language_for(tts_text, selected_language),
        "speaker": speaker_for(selected_language, speaker),
        "model": SARVAM_TTS_MODEL,
        "pace": pace_for(tts_text, selected_language),
        "temperature": SARVAM_TTS_TEMPERATURE,
        "speech_sample_rate": 24000,
        "output_audio_codec": "mp3",
        "output_audio_bitrate": "96k",
    }


def sarvam_headers() -> dict:
    if not SARVAM_API_KEY or SARVAM_API_KEY.startswith("your_"):
        raise RuntimeError("SARVAM_API_KEY is missing or still set to a placeholder.")
    return {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    }


def synthesize_speech(text: str, selected_language: str = "auto") -> bytes:
    """Convert text to audio bytes using Sarvam AI text-to-speech."""
    headers = sarvam_headers()
    payload = build_rest_payload(text, selected_language)

    print("[Sarvam] Request started.")
    try:
        response = requests.post(
            SARVAM_TTS_URL,
            json=payload,
            headers=headers,
            timeout=EXTERNAL_API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        audios = data.get("audios")
        if not isinstance(audios, list) or not audios or not isinstance(audios[0], str):
            raise RuntimeError("Sarvam did not return a valid audios array.")
        try:
            audio_bytes = base64.b64decode(audios[0], validate=True)
        except Exception as exc:
            raise RuntimeError("Sarvam audio decoding failed.") from exc
        if not audio_bytes:
            raise RuntimeError("Sarvam returned empty audio.")
        print(f"[Sarvam] Audio received: {len(audio_bytes)} bytes.")
        return audio_bytes
    except requests.exceptions.Timeout as exc:
        print("[Sarvam] Request timed out.")
        raise RuntimeError("Sarvam request timed out.") from exc
    except requests.exceptions.HTTPError as exc:
        body = exc.response.text[:500] if exc.response is not None else ""
        status = exc.response.status_code if exc.response is not None else "unknown"
        print(f"[Sarvam] HTTP error {status}: {body}")
        raise RuntimeError(f"Sarvam API error {status}: {body}") from exc
    except ValueError as exc:
        print(f"[Sarvam] Invalid JSON response: {exc}")
        raise RuntimeError("Sarvam returned an invalid JSON response.") from exc
    except Exception as exc:
        print(f"[Sarvam] Unexpected error: {exc}")
        raise RuntimeError(f"Sarvam failed: {exc}") from exc


def stream_speech(text: str, selected_language: str = "auto"):
    """Yield MP3 audio bytes from Sarvam streaming TTS."""
    headers = sarvam_headers()
    payload = build_stream_payload(text, selected_language)

    print("[Sarvam] Streaming request started.")
    try:
        with requests.post(
            SARVAM_TTS_STREAM_URL,
            json=payload,
            headers=headers,
            timeout=EXTERNAL_API_TIMEOUT_SECONDS,
            stream=True,
        ) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        print("[Sarvam] Streaming audio finished.")
    except requests.exceptions.Timeout as exc:
        print("[Sarvam] Streaming request timed out.")
        raise RuntimeError("Sarvam streaming request timed out.") from exc
    except requests.exceptions.HTTPError as exc:
        body = exc.response.text[:500] if exc.response is not None else ""
        status = exc.response.status_code if exc.response is not None else "unknown"
        print(f"[Sarvam] Streaming HTTP error {status}: {body}")
        raise RuntimeError(f"Sarvam streaming API error {status}: {body}") from exc
    except Exception as exc:
        print(f"[Sarvam] Streaming unexpected error: {exc}")
        raise RuntimeError(f"Sarvam streaming failed: {exc}") from exc
