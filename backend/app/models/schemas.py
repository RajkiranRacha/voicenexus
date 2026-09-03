from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class AuthStatus(str, Enum):
    UNAUTHENTICATED = "UNAUTHENTICATED"
    ANI_MATCHED = "ANI_MATCHED"
    OTP_VERIFIED = "OTP_VERIFIED"

class IntentEnum(str, Enum):
    BILLING_INQUIRY = "BILLING_INQUIRY"
    PAYMENT_PROMISE = "PAYMENT_PROMISE"
    OUTAGE_TRIAGE = "OUTAGE_TRIAGE"
    PLAN_INQUIRY = "PLAN_INQUIRY"
    PLAN_UPGRADE = "PLAN_UPGRADE"
    CALLBACK_SCHEDULE = "CALLBACK_SCHEDULE"
    AGENT_ESCALATION = "AGENT_ESCALATION"
    CONFIRMATION_YES = "CONFIRMATION_YES"
    CONFIRMATION_NO = "CONFIRMATION_NO"
    UNKNOWN = "UNKNOWN"

class CallState(str, Enum):
    RINGING = "RINGING"
    GREETING = "GREETING"
    AUTH_CHALLENGE = "AUTH_CHALLENGE"
    INTENT_ROUTING = "INTENT_ROUTING"
    SUBFLOW_EXECUTION = "SUBFLOW_EXECUTION"
    CONFIRMATION_PENDING = "CONFIRMATION_PENDING"
    RESOLVED_CONTAINED = "RESOLVED_CONTAINED"
    ESCALATING_TO_AGENT = "ESCALATING_TO_AGENT"
    CALL_ENDED = "CALL_ENDED"

class LatencyMetrics(BaseModel):
    stt_ms: float = 0.0
    nlu_ms: float = 0.0
    tts_ms: float = 0.0
    total_turn_ms: float = 0.0

class DialogueTurn(BaseModel):
    turn_id: int
    speaker: str  # "caller" | "ai" | "system"
    text: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    latency: Optional[LatencyMetrics] = None
    state: Optional[str] = None

class SubscriberAccount(BaseModel):
    account_number: str
    phone_number: str
    customer_name: str
    zip_code: str
    address: str
    plan_name: str
    monthly_rate: float
    current_balance: float
    due_date: str
    auth_status: AuthStatus = AuthStatus.UNAUTHENTICATED
    has_active_outage: bool = False
    router_status: str = "ONLINE"  # "ONLINE", "OFFLINE", "DEGRADED"

class EscalationPayload(BaseModel):
    session_id: str
    ani: str
    customer_profile: Dict[str, Any]
    call_context: Dict[str, Any]
    resolution_summary: Dict[str, Any]
    recommended_agent_queue: str
    transcript_snippet: List[Dict[str, str]]
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class TelemetrySummary(BaseModel):
    total_calls: int = 0
    active_calls: int = 0
    contained_calls: int = 0
    escalated_calls: int = 0
    containment_rate_pct: float = 0.0
    transfer_rate_pct: float = 0.0
    avg_handle_time_automated_sec: float = 0.0
    avg_handle_time_escalated_sec: float = 0.0
    median_latency_ms: float = 0.0
    intent_distribution: Dict[str, int] = Field(default_factory=dict)
    escalation_reasons: Dict[str, int] = Field(default_factory=dict)
