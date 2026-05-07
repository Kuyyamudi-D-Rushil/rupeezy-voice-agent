from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import base64
from time import time
from uuid import uuid4
from services.language import detect_language
from services.memory import get_active_language, get_history, add_message, delete_session, set_active_language
from services.llm import analyze_lead, get_llm_response, post_process_agent_response
from services.leads import build_lead_from_conversation, fallback_analysis, save_lead
from services.tts import stream_speech, synthesize_speech

router = APIRouter()
_STREAM_AUDIO_CACHE: dict[str, dict] = {}
STREAM_AUDIO_TTL_SECONDS = 120


class ChatRequest(BaseModel):
    session_id: str
    message: str
    language: str | None = "auto"


class ChatResponse(BaseModel):
    response: str
    audio_url: str | None
    audio_stream_url: str | None = None
    audio_base64: str | None = None
    audio_mime_type: str | None = None
    tts_error: str | None = None
    session_id: str
    active_language: str = "hinglish"


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, background_tasks: BackgroundTasks):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session_id = req.session_id.strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")

    # Retrieve history, append user message
    history = get_history(session_id)
    add_message(session_id, "user", req.message)
    history.append({"role": "user", "content": req.message})

    requested_language = (req.language or "auto").strip().lower()
    previous_language = get_active_language(session_id)
    active_language = detect_language(req.message, requested_language, previous_language)
    set_active_language(session_id, active_language)

    try:
        assistant_text = post_process_agent_response(
            get_llm_response(history, active_language),
            max_sentences=2,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    add_message(session_id, "assistant", assistant_text)
    full_history = get_history(session_id)
    background_tasks.add_task(save_lead_analysis, session_id, full_history)

    audio_base64 = None
    audio_mime_type = None
    tts_error = None
    audio_id = uuid4().hex
    _cleanup_stream_cache()
    _STREAM_AUDIO_CACHE[audio_id] = {
        "text": assistant_text,
        "language": active_language,
        "created_at": time(),
    }

    return ChatResponse(
        response=assistant_text,
        audio_url=None,
        audio_stream_url=f"/tts/stream/{audio_id}",
        audio_base64=audio_base64,
        audio_mime_type=audio_mime_type,
        tts_error=tts_error,
        session_id=session_id,
        active_language=active_language,
    )


@router.get("/tts/stream/{audio_id}")
async def tts_stream(audio_id: str):
    item = _STREAM_AUDIO_CACHE.get(audio_id)
    if not item:
        raise HTTPException(status_code=404, detail="Audio stream expired.")

    def audio_generator():
        try:
            yield from stream_speech(item["text"], item["language"])
        finally:
            _STREAM_AUDIO_CACHE.pop(audio_id, None)

    return StreamingResponse(audio_generator(), media_type="audio/mpeg")


@router.post("/tts/fallback", response_model=ChatResponse)
async def tts_fallback(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    selected_language = detect_language(
        req.message,
        (req.language or "auto").strip().lower(),
        get_active_language(req.session_id),
    )
    audio_base64 = None
    audio_mime_type = None
    tts_error = None
    try:
        audio_bytes = synthesize_speech(req.message, selected_language)
        audio_base64 = base64.b64encode(audio_bytes).decode("ascii")
        audio_mime_type = "audio/wav"
    except RuntimeError as exc:
        tts_error = str(exc)
    return ChatResponse(
        response=req.message,
        audio_url=None,
        audio_stream_url=None,
        audio_base64=audio_base64,
        audio_mime_type=audio_mime_type,
        tts_error=tts_error,
        session_id=req.session_id,
        active_language=selected_language,
    )


def save_lead_analysis(session_id: str, full_history: list[dict]) -> None:
    try:
        analysis = analyze_lead(full_history)
    except RuntimeError:
        analysis = fallback_analysis(full_history)

    try:
        save_lead(build_lead_from_conversation(session_id, full_history, analysis))
    except Exception as exc:
        print(f"[Leads] Could not save lead: {exc}")


def _cleanup_stream_cache() -> None:
    cutoff = time() - STREAM_AUDIO_TTL_SECONDS
    expired = [
        audio_id
        for audio_id, item in _STREAM_AUDIO_CACHE.items()
        if item.get("created_at", 0) < cutoff
    ]
    for audio_id in expired:
        _STREAM_AUDIO_CACHE.pop(audio_id, None)


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    deleted = delete_session(session_id)
    if deleted:
        return {"status": "ok", "message": f"Session {session_id} cleared."}
    raise HTTPException(status_code=404, detail="Session not found.")
