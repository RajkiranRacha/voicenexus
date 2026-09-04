export interface LatencyMetrics {
  stt_ms: number;
  nlu_ms: number;
  tts_ms: number;
  total_turn_ms: number;
}

export interface DialogueTurn {
  turn_id: number;
  speaker: 'caller' | 'ai' | 'system';
  text: string;
  timestamp: string;
  latency?: LatencyMetrics;
  state?: string;
}

export interface CallerProfile {
  account_number: string;
  phone_number: string;
  customer_name: string;
  zip_code: string;
  address: string;
  plan_name: string;
  monthly_rate: number;
  current_balance: number;
  due_date: string;
  payment_card_last4?: string;
  email?: string;
  auth_status: string;
  has_active_outage: boolean;
  router_status: string;
}

export interface EscalationPayload {
  session_id: string;
  ani: string;
  customer_profile: {
    account_number: string;
    customer_name: string;
    auth_status: string;
    auth_method: string;
    phone_number: string;
  };
  call_context: {
    primary_intent: string;
    intent_confidence: number;
    duration_in_ivr_seconds: number;
    turns_count: number;
  };
  resolution_summary: {
    attempted_action: string;
    current_balance: number;
    failure_or_escalation_reason: string;
    notes: string;
    flow_step?: string;
  };
  recommended_agent_queue: string;
  transcript_snippet: Array<{ speaker: string; text: string }>;
  created_at: string;
}

export interface LiveStreamTurn {
  session_id: string;
  turn: DialogueTurn;
  metadata?: {
    ani?: string;
    customer_name?: string;
    account_number?: string;
    state?: string;
    language?: string;
  };
}

export interface AdminConfigData {
  operator_name: string;
  greeting_prompt: string;
  spanish_greeting_prompt: string;
  hindi_greeting_prompt?: string;
  hold_prompt: string;
  close_prompt: string;
  escalation_prompt: string;
  regulatory_disclosure_enabled: boolean;
  regulatory_disclosure_prompt: string;
  default_voice: string;
  spanish_voice: string;
  hindi_voice?: string;
  voice_rate: string;
  voice_pitch: string;
  language: string;
  pronunciation_overrides: Record<string, string>;
}

export interface ActiveCallState {
  sessionId: string;
  agentId: string;
  callerName: string;
  ani: string;
  isMicActive: boolean;
  isMuted: boolean;
  isAudioConnected: boolean;
  status: 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED';
}

export interface TelemetrySummary {
  total_calls: number;
  active_calls: number;
  contained_calls: number;
  escalated_calls: number;
  abandoned_calls: number;
  containment_rate_pct: number;
  transfer_rate_pct: number;
  abandonment_rate_pct: number;
  avg_handle_time_automated_sec: number;
  avg_handle_time_escalated_sec: number;
  median_latency_ms: number;
  latency_slo_target_ms: number;
  latency_slo_breach_pct: number;
  avg_csat: number | null;
  csat_response_count: number;
  intent_distribution: Record<string, number>;
  escalation_reasons: Record<string, number>;
}

export interface CallRecord {
  session_id: string;
  ani: string;
  account_number: string;
  customer_name: string;
  intent: string;
  duration_sec: number;
  final_state: string;
  escalation_reason?: string;
  avg_latency_ms: number;
  turns_count: number;
  csat_rating?: number | null;
  transcript: Array<{ speaker: string; text: string }>;
  timestamp: string;
}
