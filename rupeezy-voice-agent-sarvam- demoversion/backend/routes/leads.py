from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import DEMO_WHATSAPP_NUMBER
from services.leads import read_leads, save_lead, seed_demo_lead

router = APIRouter()


class LeadRecord(BaseModel):
    id: str | None = None
    name: str | None = None
    phone: str | None = None
    language_detected: str | None = None
    lead_score: int | None = None
    lead_status: str | None = None
    main_objection: str | None = None
    conversation_summary: str | None = None
    next_action: str | None = None
    handoff_status: str | None = None
    transcript: str | None = None
    timestamp: str | None = None


@router.get("/leads")
async def get_leads():
    try:
        return read_leads()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not load leads: {exc}") from exc


@router.get("/dashboard-config")
async def get_dashboard_config():
    return {"demo_whatsapp_number": DEMO_WHATSAPP_NUMBER}


@router.post("/save-lead")
async def post_save_lead(record: LeadRecord):
    try:
        lead = save_lead(record.model_dump(exclude_none=True))
        return {"status": "ok", "lead": lead}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not save lead: {exc}") from exc


@router.post("/seed-demo-lead")
async def post_seed_demo_lead():
    try:
        lead = seed_demo_lead()
        return {"status": "ok", "lead": lead}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not seed demo lead: {exc}") from exc
