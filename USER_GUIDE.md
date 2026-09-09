# VoiceNexus — Non-Technical User Guide

> **"Turn IVR into resolution, not frustration."**

Welcome to **VoiceNexus**, an AI-powered Conversational Interactive Voice Response (IVR) platform purpose-built for telecommunications, broadband, and cable service providers. 

This guide is written in plain language for **contact center leaders, customer care managers, product managers, business analysts, and evaluators**. You do not need any programming knowledge to explore, test, and understand VoiceNexus.

---

## 📑 Table of Contents

1. [What is VoiceNexus?](#1-what-is-voicenexus)
2. [Key Problems VoiceNexus Solves](#2-key-problems-voicenexus-solves)
3. [The Four Roles in the Platform](#3-the-four-roles-in-the-platform)
   - [Role 1: The Caller (Phone Simulator)](#role-1-the-caller-phone-simulator)
   - [Role 2: The Care Specialist (Agent Desktop)](#role-2-the-care-specialist-agent-desktop)
   - [Role 3: Contact Center Operations (Care-Ops Dashboard)](#role-3-contact-center-operations-care-ops-dashboard)
   - [Role 4: Telecom Administrator (Admin Settings)](#role-4-telecom-administrator-admin-settings)
4. [Step-by-Step Guided Walkthroughs](#4-step-by-step-guided-walkthroughs)
   - [Tour A: Paying a Bill & Setting a Payment Promise](#tour-a-paying-a-bill--setting-a-payment-promise)
   - [Tour B: Diagnosing an Outage & Rebooting a Router](#tour-b-diagnosing-an-outage--rebooting-a-router)
   - [Tour C: Upgrading Internet Speed](#tour-c-upgrading-internet-speed)
   - [Tour D: Seamless Live Agent Escalation (Zero Repetition)](#tour-d-seamless-live-agent-escalation-zero-repetition)
   - [Tour E: Switching Languages Mid-Call (English, Spanish, Hindi)](#tour-e-switching-languages-mid-call-english-spanish-hindi)
   - [Tour F: Calling from an Unrecognized Number (Security Verification)](#tour-f-calling-from-an-unrecognized-number-security-verification)
5. [Frequently Asked Questions (FAQ)](#5-frequently-asked-questions-faq)
6. [Glossary of Terms](#6-glossary-of-terms)

---

## 1. What is VoiceNexus?

When customers call customer service today, they usually experience **"IVR Hell"**:
- Enduring lengthy robotic menus: *"Press 1 for billing, press 2 for technical support..."*
- Repeating account numbers, names, and passwords multiple times.
- Getting trapped in dead-end loops or abruptly disconnected.
- Finally reaching a live agent, only to be asked: *"What was your account number again?"*

**VoiceNexus replaces clunky phone trees with a natural, conversational AI agent.** 

Callers speak in their own words just as they would to a human care representative. VoiceNexus understands the customer's intent, securely identifies them, completes common account tasks instantly, and — when human expertise is truly required — smoothly transfers the caller to a live agent with their entire conversation history pre-loaded.

---

## 2. Key Problems VoiceNexus Solves

| Traditional IVR Pain Point | VoiceNexus Solution | Business Impact |
| :--- | :--- | :--- |
| **Long Touch-Tone Menus** | **Natural Voice Understanding**: Callers say what they want in everyday language. | Cuts call setup time by over 50%. |
| **High Agent Call Volumes** | **Automated In-Flow Resolution**: Resolves billing payments, outage checks, router reboots, and plan quotes automatically. | Lifts **Containment Rate** to 60–80%, drastically reducing cost per call. |
| **Customer Repetition on Escalation** | **Zero-Repetition Handoff (Screen-Pop)**: When a human agent takes over, they see the customer's name, verified identity, issue summary, and live transcript before saying "Hello". | Lowers Average Handle Time (AHT) and dramatically boosts Customer Satisfaction (CSAT). |
| **Language Barriers** | **Instant Multilingual Switching**: Supports English, Spanish, and Hindi dynamically in the same call. | Expands accessibility for diverse customer bases. |
| **Blind Spots in Call Center Data** | **Real-Time Care-Ops Dashboard**: Operations teams see live containment rates, response latency, caller drop-offs, and escalation drivers. | Immediate visibility into emerging outages and customer friction points. |

---

## 3. The Four Roles in the Platform

The VoiceNexus web application includes four interactive modules accessible via the top navigation bar:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  VoiceNexus   [1. Phone Simulator] [2. Agent Desktop] [3. Care-Ops] [4. Admin]  [?]  ● Online │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Role 1: The Caller (Phone Simulator)
This screen puts you in the shoes of a telecom subscriber calling customer service.
- **Simulate Phone Numbers**: Click one of the pre-configured callers (Jordan, Elena, Marcus) or enter your own custom phone number.
- **Two Ways to Talk**:
  1. **Voice Microphone**: Click **Voice Mic** to speak into your computer microphone.
  2. **Text Chat & Quick Presets**: Type your response or click any one-click preset button (no microphone required!).
- **Natural Voice Audio**: VoiceNexus speaks back to you in clear, studio-grade neural voices. If your browser blocks audio, an automatic visual indicator appears and browser fallback speech takes over.
- **DTMF Keypad**: If you prefer pressing keys, an on-screen touch-tone dialpad is available. Pressing `0` escalates immediately to an operator.
- **Live Latency Tracker**: Displays sub-second turn latency, showing how quickly the AI processed your words.

---

### Role 2: The Care Specialist (Agent Desktop)
This screen simulates the live customer care agent’s computer terminal in the contact center.
- **CTI Screen-Pop**: The moment a call requires human assistance, it appears in the **Pending Escalations Queue** with an audible notification.
- **Verified Identity Badge**: Shows whether the caller was automatically recognized by their phone number (ANI), passed a security question, or confirmed via SMS code.
- **AI Executive Summary**: A concise 3-bullet breakdown of:
  - *Primary Intent*: What the customer called about.
  - *Escalation Reason*: Why the AI transferred the call (e.g., customer requested human, payment promise exceeds limits).
  - *Account Details*: Outstanding balance, billing dates, address.
- **AI Next-Best-Action**: Automatically suggests the best policy or response for the agent (e.g., *"Offer the customer a 7-day payment extension"*).
- **Full Call Transcript**: The agent sees every word exchanged with the AI prior to transfer, eliminating the need to ask: *"What seems to be the problem today?"*
- **Two-Way Voice Bridge**: Click **Accept & Answer Call** to speak directly to the caller via real-time browser audio, or use one-click canned responses.

---

### Role 3: Contact Center Operations (Care-Ops Dashboard)
This screen gives supervisors and executives a bird's-eye view of call center efficiency.
- **Containment Rate (%)**: The percentage of calls resolved entirely by the AI without human intervention.
- **Agent Transfer Rate (%)**: The percentage of calls routed to human agents.
- **Abandonment Rate (%)**: The percentage of callers who hung up before finishing.
- **Customer Satisfaction (CSAT)**: Rolling star rating based on post-call customer feedback.
- **Average Handle Time (AHT)**: Time spent resolving calls automatically vs. time spent before transferring to an agent.
- **Median Turn Latency (SLO Tracker)**: Tracks whether response times stay within the strict telecom benchmark of **≤ 1.0 second**.
- **Intent Volume Distribution**: Bar chart showing what customers call about most (Billing, Outages, Plan Changes, Callbacks).
- **Agent Escalation Root Causes**: Breakdown of why calls were escalated to humans.
- **Call Detail Records (CDR) Table & CSV Export**: Searchable list of recent calls with an **Eye** button to inspect transcripts, plus a one-click **Export CSV** button for Excel and reporting tools.

---

### Role 4: Telecom Administrator (Admin Settings)
This screen allows operations staff to configure the AI's personality, branding, and compliance settings without writing any code.
- **Brand Identity**: Customize the Telco name (e.g., *NexusFiber*, *MetroBroadband*).
- **Voice Persona Selection**: Choose from Microsoft Neural voices in English (*Jenny*, *Guy*, *Aria*, *Sonia*), Spanish (*Paloma*, *Alonso*), or Hindi (*Swara*, *Madhur*).
- **Speech Cadence & Pitch**: Set the AI's speaking speed (-25% for slow/deliberate, Normal, +25% fast).
- **Custom Greetings & Prompts**: Edit greetings for English, Spanish, and Hindi, as well as hold messages and transfer announcements.
- **Regulatory Disclosure Toggle**: Enforce automatic legal disclaimers at the start of calls (*"This call may be recorded for quality assurance and uses automated intelligence"*).
- **Telco Acronym Dictionary**: Ensure technical terms are pronounced naturally (e.g., pronounce `"ONT"` as *"O-N-T"*, `"VoIP"` as *"Voice over I-P"*, and `"Gbps"` as *"gigabits per second"*).

---

## 4. Step-by-Step Guided Walkthroughs

Try these scenarios directly in your browser. Each takes less than 2 minutes.

### Tour A: Paying a Bill & Setting a Payment Promise
1. Go to **Phone Simulator**.
2. Select preset caller **Jordan Rivera** (Balance: $142.50).
3. Click **Start Call**. The AI greets Jordan by name because his phone number was automatically matched.
4. Click preset **"Pay Bill Now (Card on File)"** or type: *"I'd like to pay my balance with the card on file."*
5. The AI states the balance ($142.50), references the card on file (ending in `4242`), and asks for explicit confirmation.
6. Click preset **"Confirm Card Payment"** or type: *"Yes, please charge my card."*
7. VoiceNexus processes the payment, provides a confirmation code, and gracefully closes the call.
8. Switch to **Care-Ops (VN-6)**: Notice that the call is logged as **Contained** with 100% resolution!

---

### Tour B: Diagnosing an Outage & Rebooting a Router
1. Go to **Phone Simulator**.
2. Select preset caller **Elena Vance** or **Marcus Brody**.
3. Click **Start Call**.
4. Click preset **"Check Internet Outage"** or type: *"My internet is completely down."*
5. VoiceNexus checks the service address in real time:
   - For Elena: Identifies an active fiber node outage in her ZIP code and offers to send SMS updates.
   - For Marcus: Detects degraded Wi-Fi signal/packet loss on the home gateway and asks permission to perform a remote reboot.
6. Click preset **"Approve Router Reboot"** or type: *"Yes, reboot it."*
7. The AI simulates sending a remote reset signal to the optical terminal, verifies link restoration, and asks if anything else is needed.

---

### Tour C: Upgrading Internet Speed
1. Go to **Phone Simulator**.
2. Select preset caller **Jordan Rivera** and click **Start Call**.
3. Click preset **"Inquire Plan & Upgrade"** or type: *"What plan am I on and can I upgrade to gigabit speed?"*
4. VoiceNexus looks up Jordan's current plan (500 Mbps at $65/mo) and quotes the Gigabit Tier upgrade ($85/mo).
5. The AI asks if he would like to authorize the change.
6. Because financial commitments require customer consent, VoiceNexus issues a step-up confirmation code before finalizing the order.

---

### Tour D: Seamless Live Agent Escalation (Zero Repetition)
1. Open two browser tabs or split your screen:
   - **Tab 1**: Navigate to **Phone Simulator**.
   - **Tab 2**: Navigate to **Agent Desktop**.
2. In **Tab 1**, start a call as **Jordan Rivera**.
3. Click preset **"Explicit Agent Request"** or type: *"I need to speak to a human representative right now."*
4. VoiceNexus responds politely: *"I am transferring you to one of our care specialists right now. I've sent them your verified details so you won't have to repeat yourself."*
5. In **Tab 2 (Agent Desktop)**:
   - Notice the **Pending Escalations** badge update with a red alert badge.
   - The card displays Jordan's name, verified phone number, current balance, and the exact reason for transfer (*"Customer explicitly requested live agent"*).
   - Click **Accept & Answer Call**.
   - The two-way voice bridge connects! The agent can speak into their microphone or use quick canned responses to greet Jordan without asking for his account number.

---

### Tour E: Switching Languages Mid-Call (English, Spanish, Hindi)
1. Go to **Phone Simulator** and start a call.
2. At any point during the conversation, click preset **"Bilingual: Switch to Spanish"** or type: *"Quiero hablar en español."*
3. VoiceNexus immediately shifts its voice and language to fluent Spanish (`es-US-PalomaNeural`) and continues the conversation.
4. Try typing: *"hindi mein baat karo"* or *"Please speak in Hindi"*.
5. VoiceNexus transitions seamlessly into Hindi (`hi-IN-SwaraNeural`), retaining the caller's context and history.
6. Say: *"Please switch back to English"* to return to English.

---

### Tour F: Calling from an Unrecognized Number (Security Verification)
1. Go to **Phone Simulator**.
2. In the phone number box, type any random phone number (e.g., `+15559876543`) or select **Unregistered Caller**.
3. Click **Start Call**.
4. VoiceNexus notices that this number is not linked to any account on file.
5. Instead of rejecting the call, the AI requests Knowledge-Based Authentication (KBA): *"To protect your privacy, could you please provide your 10-digit account number or billing ZIP code?"*
6. Click preset **"KBA Auth: Verify Zip 94107"** or type: *"My billing zip code is 94107."*
7. VoiceNexus verifies the ZIP code against the customer database, links the session to the customer profile, and unlocks billing and technical assistance!

---

## 5. Frequently Asked Questions (FAQ)

### Q: Do I need a working microphone to evaluate VoiceNexus?
**No.** Every flow in VoiceNexus can be operated 100% silently using the text input box or the built-in preset buttons. Microphone support is available for real voice testing, but completely optional.

### Q: What makes VoiceNexus different from a standard chatbot?
VoiceNexus is designed specifically for **voice-first telephony**:
- **Ultra-low latency**: Responds in under 1 second, avoiding awkward conversational pauses.
- **Barge-In capability**: If the caller interrupts while the AI is speaking, the AI immediately stops talking and listens.
- **Deterministic guardrails**: The system follows strict telco business rules (identity verification before disclosing balances, confirmation before charging cards) rather than freely guessing.

### Q: How does VoiceNexus handle complex issues it cannot resolve?
VoiceNexus follows the principle of **"Honest Limits"**:
- It never fabricates answers or guesses.
- It summarizes what the caller was attempting to do.
- It packages the data into a standardized `EscalationPayload` and routes the call to a human agent, or offers to schedule a callback if queues are full.

### Q: Can VoiceNexus be connected to real telecom lines (SIP/PSTN)?
**Yes.** While the web demo uses WebSockets and WebRTC for browser simulation, the backend architecture is designed to interface with standard telecom session border controllers (SBCs), SIP trunks, and telephony providers like Twilio, Amazon Chime, or Genesys.

### Q: Are changes made in the Admin panel applied immediately?
**Yes.** If you change the Telco name, speech speed, or active voice in the **Admin** tab and click **Save Configuration**, the very next call you start will use those new settings without restarting any servers.

---

## 6. Glossary of Terms

- **ANI (Automatic Number Identification)**: The caller ID phone number passed through the telephone network. Used by VoiceNexus to instantly identify subscribers.
- **AHT (Average Handle Time)**: The average duration of a customer call. VoiceNexus reduces AHT by resolving routine requests quickly and pre-populating context for live agents.
- **Barge-In**: The ability for a caller to speak over the AI and interrupt it, causing the AI to instantly cease playback and process the new speech.
- **CDR (Call Detail Record)**: A comprehensive data record generated at the end of each call, containing timestamps, duration, intent, latency metrics, and transcript history.
- **Containment Rate**: The percentage of calls completely resolved by the AI without transferring to a human representative.
- **CTI (Computer Telephony Integration)**: Technology that connects phone systems with agent software, enabling features like Screen-Pop.
- **DTMF (Dual-Tone Multi-Frequency)**: Touch-tone keypad signals generated when pressing 0–9, *, or # on a phone dialpad.
- **KBA (Knowledge-Based Authentication)**: Security verification using known personal information, such as billing ZIP code or account number.
- **Screen-Pop**: Automatically opening a customer's record on an agent's screen when an escalated call arrives.
- **SLO (Service Level Objective)**: A target performance benchmark. VoiceNexus enforces a latency SLO of ≤ 1,000 milliseconds (1 second) per turn.
