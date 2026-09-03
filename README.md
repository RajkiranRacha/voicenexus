# VoiceNexus — Conversational IVR Platform (v1.0)

> **"Turn IVR into resolution, not frustration."**

VoiceNexus is an AI IVR platform engineered for telecom, broadband, and cable service providers. It delivers natural, low-latency, goal-directed conversations that resolve routine customer care issues in-flow while escalating cleanly to live agents with full verified context.

---

## 🚀 Key Features Implemented

1. **Sub-Second Voice Orchestration Pipeline (`NFR Latency ≤ 1.0s`):**
   - Full duplex WebSocket audio streaming.
   - Sub-250ms neural speech synthesis with Microsoft Edge Neural voices (`en-US-JennyNeural`, `en-US-GuyNeural`, `en-GB-SoniaNeural`).
   - Instant barge-in / interruption handling.
2. **Deterministic Care State Machine (`VN-1`, `VN-2`):**
   - Implements PRD experience principles: *Identity before action*, *Confirm before committing*, *Honest limits*, and *Clean transfer*.
   - Goal-directed subflows for:
     - **Billing & Payment Promise (`VN-4`):** Balance inquiry, arrangement date extraction, explicit confirmation check, and idempotent commitment.
     - **Outage & Equipment Triage (`VN-4`):** Real-time area outage lookup by ZIP, optical line diagnostic testing, remote router bounce, and field technician dispatch booking.
     - **Plan & Account Management (`VN-4`):** Plan speed comparison, step-up OTP challenge, rate adjustment authorization.
     - **Callback Window Scheduling (`VN-8`):** Queue reservation for async customer callback.
3. **Identity Verification (`VN-3`):**
   - Tier 1: Passive Automatic Number Identification (ANI) match against subscriber BSS/OSS accounts.
   - Tier 2: Step-up SMS OTP challenge.
4. **Structured Escalation & Agent Desktop (`VN-5`, `VN-10`):**
   - Automated generation of the `EscalationPayload` JSON schema.
   - Real-time CTI Screen-Pop feed to the Live Agent Desktop over WebSockets.
   - Live transcript overlay to ensure zero-repetition handoff.
5. **Care-Ops Telemetry & Analytics Dashboard (`VN-6`):**
   - Real-time computation of Containment Rate (%), Live Agent Transfer Rate (%), AHT Automated vs Escalated (sec), Median Response Latency (ms), Intent Distribution, and Escalation Drivers.
   - Interactive Call Detail Records (CDR) inspector.
6. **Degraded Mode & DTMF Touch-Tone Fallback (`VN-9`):**
   - 12-key DTMF dialpad with instant `0` key operator escalation.
7. **Brand Voice & Tenant Customization (`VN-7`, `VN-9`):**
   - Configurable operator branding, greeting/hold prompts, and speech pace.

---

## 📁 Repository Structure

```
voicenexus/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── agent.py         # Agent Desktop API & WebSockets (VN-5, VN-10)
│   │   │   │   └── telemetry.py     # Care-Ops metrics & CDR APIs (VN-6)
│   │   │   └── websocket_call.py    # Real-time Telephony / WebPhone Gateway
│   │   ├── engine/
│   │   │   ├── flows/
│   │   │   │   ├── billing_flow.py       # Billing & Payment Promise subflow
│   │   │   │   ├── outage_triage_flow.py # Outage check & line diagnostics
│   │   │   │   ├── plan_flow.py          # Plan inquiry & speed upgrades
│   │   │   │   └── callback_flow.py      # Async callback scheduler
│   │   │   ├── intent_classifier.py      # NLU intent pattern recognizer
│   │   │   ├── orchestrator.py           # Dialogue turn & latency coordinator
│   │   │   └── state_machine.py          # Deterministic Care State Machine
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic schemas & EscalationPayload
│   │   ├── services/
│   │   │   ├── agent_hub.py         # Agent Desktop broadcast broker
│   │   │   ├── bss_oss.py           # Mock Telco system of record & idempotency
│   │   │   ├── identity.py          # ANI & SMS OTP verification
│   │   │   ├── telemetry.py         # Metrics calculation & CDR logger
│   │   │   └── tts.py               # Neural streaming TTS engine
│   │   ├── config.py                # Tenant settings & latency targets
│   │   └── main.py                  # FastAPI application entrypoint
│   ├── tests/
│   │   └── test_flows.py            # Complete automated test suite
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── PhoneSimulator.tsx   # Interactive WebPhone & Audio visualizer
    │   │   ├── AgentDesktop.tsx     # CTI Screen-Pop & live transcript overlay
    │   │   ├── OpsDashboard.tsx     # Care-Ops KPI metrics & CDR inspector
    │   │   └── AdminConfig.tsx      # Voice persona & tenant prompt editor
    │   ├── types.ts                 # TypeScript data contracts
    │   └── App.tsx                  # Unified 4-mode application shell
    └── package.json
```

---

## 🏃‍♂️ How to Run

### Option 1: Unified Single-Port Launch (Recommended)
Because the frontend has already been built into `frontend/dist/`, running the FastAPI server serves both the backend APIs/WebSockets and the complete UI on port `8000`:

```bash
cd backend
python -m uvicorn app.main:app --port 8000 --reload
```
Then open your browser to **`http://localhost:8000`**.

### Option 2: Live Frontend Development Mode
Run the backend on port `8000` and Vite dev server on port `5173`:

Terminal 1 (Backend):
```bash
cd backend
python -m uvicorn app.main:app --port 8000 --reload
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```
Open **`http://localhost:5173`**.

---

## 🧪 Running Automated Tests

```bash
cd backend
python -m pytest tests/test_flows.py -v
```
