# Rupeezy Voice Agent

Local voice sales agent demo using a static HTML/CSS/JS frontend and a FastAPI backend. Groq is used for the LLM and Sarvam AI is used for text-to-speech.

## Project Structure

```text
frontend/   Static voice agent and RM dashboard files
backend/    FastAPI API, lead scoring, Groq, and Sarvam integration
scripts/    Local development helper scripts
```

This is not a React app. Vite is only used as the local frontend dev server.

## Requirements

- Node.js 18 or newer for local Vite development
- Python 3.10 or newer
- Groq API key
- Sarvam API key

## Environment Setup

From this project folder, create your local environment file:

```powershell
copy .env.example .env
```

Fill in the real values for:

```env
GROQ_API_KEY=your_groq_api_key
SARVAM_API_KEY=your_sarvam_api_key
```

Keep `.env` local. It is ignored by git and must not be committed. `.env.example` contains placeholders only.

Useful optional values:

```env
DEMO_WHATSAPP_NUMBER=
FRONTEND_ORIGINS=
AGENT_NAME=Rupeezy AI Agent
SESSION_TTL_MINUTES=30
```

`FRONTEND_ORIGINS` is a comma-separated CORS allowlist. Leave it blank when FastAPI serves the frontend on the same Render domain. Set it only if the frontend is hosted separately, for example:

```env
FRONTEND_ORIGINS=https://your-static-site.onrender.com
```

## Local Development

Use the nested project folder that contains `frontend/`, `backend/`, `.env.example`, and `package.json`:

```powershell
cd "C:\Users\Suma Dilish\Desktop\rpz\rupeezy-voice-agent\rupeezy-voice-agent-sarvam- demoversion"
npm install
npm run dev
```

`npm install` installs Vite and also installs Python backend packages from `backend/requirements.txt`.

`npm run dev` starts:

```text
Frontend dashboard: http://localhost:5173
Backend API:        http://127.0.0.1:8000
```

The local Vite server proxies API routes to FastAPI, so frontend code can use same-origin API paths in both local development and production.

Open:

```text
http://localhost:5173
http://localhost:5173/dashboard.html
```

Use Chrome or Edge for microphone speech recognition. If speech-to-text is unavailable, use the text box.

## Run Backend Only

Render and backend-only local runs should use this shape:

```powershell
uvicorn main:app --host 0.0.0.0 --port $env:PORT --app-dir backend
```

For a local fixed port:

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend
```

FastAPI serves the static frontend from `frontend/`, so the app is available from the backend URL as well.

## Render Deployment

This repository includes `../render.yaml` at the repository root. It points Render at this nested app folder and starts the service with:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT --app-dir backend
```

In Render:

1. Create a new Blueprint from the repository, or create a Web Service manually.
2. If creating manually, set the root directory to `rupeezy-voice-agent-sarvam- demoversion`.
3. Use build command `pip install -r backend/requirements.txt`.
4. Use start command `uvicorn main:app --host 0.0.0.0 --port $PORT --app-dir backend`.
5. Add environment variables in Render, never in source control:
   - `GROQ_API_KEY`
   - `SARVAM_API_KEY`
   - Optional: `DEMO_WHATSAPP_NUMBER`, `AGENT_NAME`, `SESSION_TTL_MINUTES`
6. Leave `FRONTEND_ORIGINS` blank if the frontend is served by this FastAPI service.

## Verify

Check backend health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Check API keys locally:

```powershell
python backend/test_keys.py
```

Check full Groq plus Sarvam flow:

```powershell
$body = @{ session_id = "manual-test"; message = "Mera naam Rahul hai, main financial advisor hoon" } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/chat -Method Post -ContentType "application/json" -Body $body
```

Check lead scoring:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/leads
```

After a chat message, the backend asks Groq for strict JSON lead analysis, saves or updates the session lead in `backend/data/leads.json`, and classifies it with these score ranges:

- Hot: 75-100
- Warm: 40-74
- Cold: 0-39
