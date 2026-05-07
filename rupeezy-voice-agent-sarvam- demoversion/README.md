# Rupeezy Voice Agent

Local voice sales agent demo using a static HTML/CSS/JS dashboard served by Vite and a FastAPI backend. Groq is used for the LLM and Sarvam AI is used for text-to-speech.

## Project Structure

```text
frontend/   Static dashboard and voice agent UI
backend/    FastAPI API, lead scoring, Groq, and Sarvam integration
```

This is not a React app. Vite is used as the local frontend dev server so the app opens on a proper development port instead of showing a directory listing.

Do not use VS Code Live Server or `localhost:5500` for this app.

## Requirements

- Node.js 18 or newer
- Python 3.10 or newer
- Groq API key
- Sarvam API key

## Environment Setup

From the real project root, create your local environment file:

```powershell
copy .env.example .env
```

Fill these values in `.env`:

```env
GROQ_API_KEY=your_groq_api_key
SARVAM_API_KEY=your_sarvam_api_key
SARVAM_SPEAKER=shubh
SARVAM_SPEAKER_HINDI=dev
SARVAM_SPEAKER_HINGLISH=dev
SARVAM_SPEAKER_KANNADA=rahul
SARVAM_SPEAKER_TAMIL=rahul
SARVAM_SPEAKER_TELUGU=rahul
SARVAM_SPEAKER_ENGLISH=dev
SARVAM_TTS_PACE_HINDI=0.92
SARVAM_TTS_PACE_HINGLISH=0.94
SARVAM_TTS_PACE_KANNADA=0.88
SARVAM_TTS_PACE_TAMIL=0.94
SARVAM_TTS_PACE_TELUGU=0.94
SARVAM_TTS_PACE_ENGLISH=1.0
SARVAM_TTS_PACE_DEFAULT=1.0
SARVAM_TTS_TEMPERATURE=0.55
AGENT_NAME=Rupeezy AI Agent
DEMO_WHATSAPP_NUMBER=
SESSION_TTL_MINUTES=30
FRONTEND_ORIGIN=http://localhost:5173
API_HOST=127.0.0.1
API_PORT=8000
```

`SARVAM_SPEAKER` is the global fallback. Each supported language can use its own Sarvam speaker and pace. Hindi/Hinglish default to `dev`, Kannada/Tamil/Telugu default to `rahul`, and Hindi/Kannada are slightly slower for clarity.

Set `DEMO_WHATSAPP_NUMBER` to your own test number with country code, for example `919876543210`. The dashboard uses it only when a lead phone is missing.

The frontend calls the backend at:

```text
http://localhost:8000
```

## Install And Run

Use the nested project folder that contains `frontend/`, `backend/`, `.env.example`, and `package.json`:

```powershell
cd "C:\Users\Rohini\Downloads\rupeezy-voice-agent-sarvam- demoversion\rupeezy-voice-agent-sarvam- demoversion"
npm install
npm run dev
```

`npm install` installs the frontend dev tools and also installs Python backend packages from `backend/requirements.txt`.

`npm run dev` starts both services:

```text
Frontend dashboard: http://localhost:5173
Backend API:        http://127.0.0.1:8000
```

Open the voice agent:

```text
http://localhost:5173
```

Open the RM dashboard:

```text
http://localhost:5173/dashboard.html
```

Use Chrome or Edge for microphone speech recognition. If speech-to-text is unavailable, use the text box.

## Individual Commands

Run only the frontend:

```powershell
npm run dev:frontend
```

Run only the backend:

```powershell
npm run dev:backend
```

## Verify

Check backend health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Check API keys:

```powershell
cd backend
python test_keys.py
```

Compare Hindi/Hinglish Sarvam speakers:

```powershell
npm run test:speakers
```

This generates `backend/speaker_samples/sunny.wav`, `rahul.wav`, and `dev.wav` and prints latency for each voice.

Generate voice samples for every supported language:

```powershell
npm run test:multilingual-tts
```

This generates WAV files in `backend/multilingual_samples/` for Hinglish, Hindi, Kannada, Tamil, Telugu, and English.

Check full Groq plus Sarvam flow:

```powershell
$body = @{ session_id = "manual-test"; message = "Mera naam Rahul hai, main financial advisor hoon" } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/chat -Method Post -ContentType "application/json" -Body $body
```

The response should include:

- `response`: fresh Groq-generated text.
- `audio_stream_url`: streamed Sarvam MP3 audio for faster playback.
- `audio_base64`: fallback WAV audio when streaming fails.
- `tts_error`: a Sarvam error message when TTS fails.

Check lead scoring:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/leads
```

After a chat message, the backend asks Groq for strict JSON lead analysis, saves or updates the session lead in `backend/data/leads.json`, and classifies it with these score ranges:

- Hot: 75-100
- Warm: 40-74
- Cold: 0-39

If Groq lead analysis fails, the backend still saves a fallback Warm lead so the RM dashboard remains usable.
