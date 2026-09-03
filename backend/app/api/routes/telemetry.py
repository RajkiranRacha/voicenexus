from fastapi import APIRouter
from app.services.telemetry import telemetry_service

router = APIRouter(prefix="/api/telemetry", tags=["Care-Ops Telemetry"])

@router.get("/summary")
def get_telemetry_summary():
    return telemetry_service.get_summary().model_dump()

@router.get("/cdrs")
def get_call_detail_records(limit: int = 50):
    return telemetry_service.get_recent_cdrs(limit)
