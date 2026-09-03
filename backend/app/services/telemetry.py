from typing import Dict, List, Any
from datetime import datetime
from app.models.schemas import TelemetrySummary, CallState, IntentEnum

class TelemetryService:
    """
    Care-Ops Telemetry & Analytics Engine (VN-6).
    Tracks containment rates, handle times, escalation drivers, and call detail records.
    """

    def __init__(self):
        self._records: List[Dict[str, Any]] = []
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self._seed_sample_metrics()

    def _seed_sample_metrics(self):
        # Pre-populate with realistic baseline operational data so dashboard has rich insights immediately
        sample_calls = [
            {"session_id": "call-101", "intent": "BILLING_INQUIRY", "duration": 48, "state": "RESOLVED_CONTAINED", "latency": 540},
            {"session_id": "call-102", "intent": "PAYMENT_PROMISE", "duration": 72, "state": "RESOLVED_CONTAINED", "latency": 620},
            {"session_id": "call-103", "intent": "OUTAGE_TRIAGE", "duration": 55, "state": "RESOLVED_CONTAINED", "latency": 490},
            {"session_id": "call-104", "intent": "PLAN_UPGRADE", "duration": 85, "state": "RESOLVED_CONTAINED", "latency": 580},
            {"session_id": "call-105", "intent": "BILLING_INQUIRY", "duration": 110, "state": "ESCALATING_TO_AGENT", "reason": "OUT_OF_SCOPE_BILLING_REQUEST", "latency": 610},
            {"session_id": "call-106", "intent": "AGENT_ESCALATION", "duration": 25, "state": "ESCALATING_TO_AGENT", "reason": "EXPLICIT_AGENT_REQUEST", "latency": 380},
            {"session_id": "call-107", "intent": "CALLBACK_SCHEDULE", "duration": 60, "state": "RESOLVED_CONTAINED", "latency": 510},
            {"session_id": "call-108", "intent": "OUTAGE_TRIAGE", "duration": 95, "state": "RESOLVED_CONTAINED", "latency": 530},
            {"session_id": "call-109", "intent": "BILLING_INQUIRY", "duration": 42, "state": "RESOLVED_CONTAINED", "latency": 470},
            {"session_id": "call-110", "intent": "UNKNOWN", "duration": 35, "state": "ESCALATING_TO_AGENT", "reason": "EXCEEDED_MAX_UNRECOGNIZED_TURNS", "latency": 640},
        ]
        for c in sample_calls:
            self.record_completed_call(
                session_id=c["session_id"],
                ani="+15550192834",
                account_number="ACC-992014-X",
                customer_name="Sample Subscriber",
                intent=c["intent"],
                duration_sec=c["duration"],
                final_state=c["state"],
                escalation_reason=c.get("reason"),
                avg_latency_ms=c["latency"],
                turns_count=3,
                transcript=[{"speaker": "ai", "text": "Greeting"}, {"speaker": "caller", "text": "Help with bill"}]
            )

    def record_call_start(self, session_id: str, ani: str):
        self._active_sessions[session_id] = {
            "session_id": session_id,
            "ani": ani,
            "start_time": datetime.now()
        }

    def record_completed_call(
        self,
        session_id: str,
        ani: str,
        account_number: str,
        customer_name: str,
        intent: str,
        duration_sec: int,
        final_state: str,
        escalation_reason: str = None,
        avg_latency_ms: float = 550.0,
        turns_count: int = 1,
        transcript: List[Dict[str, str]] = None
    ):
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]

        record = {
            "session_id": session_id,
            "ani": ani,
            "account_number": account_number,
            "customer_name": customer_name,
            "intent": intent,
            "duration_sec": max(1, duration_sec),
            "final_state": final_state,
            "escalation_reason": escalation_reason,
            "avg_latency_ms": avg_latency_ms,
            "turns_count": turns_count,
            "transcript": transcript or [],
            "timestamp": datetime.now().isoformat()
        }
        self._records.insert(0, record)  # Most recent first

    def get_summary(self) -> TelemetrySummary:
        total = len(self._records)
        if total == 0:
            return TelemetrySummary(active_calls=len(self._active_sessions))

        contained = [r for r in self._records if r["final_state"] == CallState.RESOLVED_CONTAINED.value]
        escalated = [r for r in self._records if r["final_state"] == CallState.ESCALATING_TO_AGENT.value]

        containment_rate = (len(contained) / total) * 100.0 if total > 0 else 0.0
        transfer_rate = (len(escalated) / total) * 100.0 if total > 0 else 0.0

        aht_auto = (
            sum(r["duration_sec"] for r in contained) / len(contained)
            if contained else 0.0
        )
        aht_esc = (
            sum(r["duration_sec"] for r in escalated) / len(escalated)
            if escalated else 0.0
        )
        
        latencies = [r["avg_latency_ms"] for r in self._records if r.get("avg_latency_ms")]
        median_lat = sorted(latencies)[len(latencies)//2] if latencies else 500.0

        intent_dist: Dict[str, int] = {}
        for r in self._records:
            it = r.get("intent", "UNKNOWN")
            intent_dist[it] = intent_dist.get(it, 0) + 1

        esc_reasons: Dict[str, int] = {}
        for r in escalated:
            reason = r.get("escalation_reason") or "POLICY_LIMIT"
            esc_reasons[reason] = esc_reasons.get(reason, 0) + 1

        return TelemetrySummary(
            total_calls=total,
            active_calls=len(self._active_sessions),
            contained_calls=len(contained),
            escalated_calls=len(escalated),
            containment_rate_pct=round(containment_rate, 1),
            transfer_rate_pct=round(transfer_rate, 1),
            avg_handle_time_automated_sec=round(aht_auto, 1),
            avg_handle_time_escalated_sec=round(aht_esc, 1),
            median_latency_ms=round(median_lat, 1),
            intent_distribution=intent_dist,
            escalation_reasons=esc_reasons
        )

    def get_recent_cdrs(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._records[:limit]

telemetry_service = TelemetryService()
