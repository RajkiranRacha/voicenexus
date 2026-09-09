# VoiceNexus Deployment & Team Testing Guide

This guide details how to run, deploy, and verify the VoiceNexus Conversational IVR Platform for team testing, multi-device demonstrations, and production deployments.

---

## 1. Local Network & Multi-Device Team Demonstration

To simulate a genuine telecom customer care call without audio echo:

### Setup
1. Double-click `run_server.bat` (or `build_and_start.bat`).
2. The server binds to `0.0.0.0:8000`, making it accessible to any device on the same local Wi-Fi / LAN network.
3. Note your computer's local IP address (e.g. `192.168.1.45`).

### Multi-Device Testing (Recommended)
- **Device 1 (Mobile Phone or Tablet)**:
  Open `http://<LAN_IP>:8000/customer` in Chrome or Safari on your phone.
  Tap **Dial Care Line** to simulate an inbound caller.
- **Device 2 (Agent Laptop)**:
  Open `http://<LAN_IP>:8000/agent` in your laptop browser.
  The live CTI bridge automatically pops incoming transfers here.

### Single-Machine Testing (Two Windows)
- Open **Window 1**: `http://localhost:8000/` (Customer Phone Portal)
- Click the **"Open Agent in New Window"** button in the top navigation bar to automatically pop open **Window 2** (`http://localhost:8000/agent`).

> [!TIP]
> Because the Customer Portal and Agent Desktop are rendered on separate routes, their audio streams and microphone inputs are fully isolated. You will no longer hear your own voice echoed back during transfer testing!

---

## 2. Docker Deployment

For containerized deployment on any Linux, macOS, or Windows host with Docker:

### 1. Build and Run with Docker Compose
```bash
docker-compose up --build -d
```

### 2. Verify Container Health
```bash
docker-compose ps
docker-compose logs -f
```

The container includes:
- Production-optimized React 19 frontend bundle.
- Python 3.12 with FastAPI, Uvicorn, and faster-whisper.
- Volume mount `./backend/data:/app/backend/data` preserving tenant prompts and telecom knowledge base across container restarts.

### 3. Stop Container
```bash
docker-compose down
```

---

## 3. Cloud Deployment (Render, Fly.io, AWS EC2, Azure)

### Option A: Cloud VM / EC2 Deployment
1. Provision an Ubuntu 22.04 / 24.04 VM (minimum 2 vCPU, 4GB RAM recommended for local Whisper STT).
2. Clone repository:
   ```bash
   git clone https://github.com/RajkiranRacha/voicenexus.git
   cd voicenexus
   ```
3. Run with Docker Compose:
   ```bash
   docker compose up -d
   ```
4. Point DNS to your server IP (e.g. `care.yourtelco.com`). Configure reverse proxy (Nginx or Caddy) with SSL certificate (`https` and `wss`).

> [!IMPORTANT]
> **Microphone Permissions (HTTPS)**: Modern web browsers (Chrome, Safari, Edge) require **HTTPS** (or `localhost`) to grant microphone access for speech recognition and WebRTC voice calls. When hosting over a public domain or IP, ensure SSL/TLS is enabled via reverse proxy.

---

## 4. Verification Checklist for Testers

| Scenario | Steps to Verify | Expected Result |
|---|---|---|
| **Defect 1: Auto Call Wrap-Up** | 1. Dial Care Line as Jordan Rivera.<br>2. Say *"Pay bill now"*, confirm payment.<br>3. When AI asks *"Can I help you with anything else today?"*, say or type *"No, Thanks for resolving"* (or *"There is no more concerns good to drop now"*). | AI responds: *"You're very welcome! We're glad your issue was resolved. Thank you for choosing NexusFiber Telco. Have a wonderful day! Goodbye."* The call automatically disconnects, dialer resets, and 5-star CSAT rating prompt is displayed. |
| **Defect 2: Telecom Domain Knowledge** | 1. In Customer Phone, ask *"How do I activate eSIM on my phone?"* or *"Why is the red LOS light blinking on my router?"* or *"What roaming pass do I need for Europe?"* | AI immediately retrieves the validated telecom knowledge article and delivers a concise spoken answer in <1.0s. |
| **Defect 2: Knowledge Ingestion** | 1. In Admin Portal (`/admin`), go to **Telecom Knowledge Base**.<br>2. Click **New Knowledge Article** and add a test topic (e.g., *"5G in Mexico"*).<br>3. In Customer Phone, ask about that topic. | AI answers immediately with the newly added knowledge without requiring a restart. |
| **Defect 3: Portal Separation & Audio Echo** | 1. Open `/customer` in Window 1 and `/agent` in Window 2.<br>2. In Window 1, say *"I need an agent"*.<br>3. In Window 2, accept call. | Screen-pop appears with zero delay. Two-way voice connects cleanly with zero microphone/speaker feedback loop. |
