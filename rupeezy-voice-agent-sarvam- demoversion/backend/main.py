from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes.chat import router as chat_router
from routes.leads import router as leads_router
from config import API_HOST, API_PORT, FRONTEND_DIR, FRONTEND_ORIGINS

app = FastAPI(
    title="Rupeezy Voice Agent API",
    description="AI-powered voice sales agent for Rupeezy partner onboarding",
    version="1.0.0",
)

if FRONTEND_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=FRONTEND_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(chat_router)
app.include_router(leads_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
