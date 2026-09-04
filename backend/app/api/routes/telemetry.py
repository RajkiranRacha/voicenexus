import csv
import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.services.telemetry import telemetry_service

router = APIRouter(prefix="/api/telemetry", tags=["Care-Ops Telemetry"])


class CsatSubmission(BaseModel):
    session_id: str
    rating: int = Field(ge=1, le=5)


@router.get("/summary")
def get_telemetry_summary():
    return telemetry_service.get_summary().model_dump()


@router.get("/cdrs")
def get_call_detail_records(limit: int = 50):
    return telemetry_service.get_recent_cdrs(limit)


@router.post("/csat")
def submit_csat(req: CsatSubmission):
    """
    Records a caller's post-call satisfaction rating (PRD business-impact
    category "Care CSAT").
    """
    found = telemetry_service.record_csat(req.session_id, req.rating)
    if not found:
        raise HTTPException(status_code=404, detail="No call record found for that session_id")
    return {"success": True, "session_id": req.session_id, "rating": req.rating}


@router.get("/export")
def export_call_summaries(format: str = "csv", limit: int = 500):
    """
    Exports call detail records for downstream reporting/analytics warehouses
    (PRD Dependencies: "Reporting & analytics warehouse -- or exported call
    summaries -- to feed operator dashboards").
    """
    records = telemetry_service.get_recent_cdrs(limit)

    if format == "json":
        return records

    columns = [
        "session_id", "timestamp", "ani", "account_number", "customer_name",
        "intent", "duration_sec", "final_state", "escalation_reason",
        "avg_latency_ms", "turns_count", "csat_rating"
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for record in records:
        writer.writerow(record)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=voicenexus_call_summaries.csv"}
    )
