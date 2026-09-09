# How to Feed Knowledge to VoiceNexus AI

This guide explains how contact center administrators, operations managers, and developers can feed, update, and manage telecom domain knowledge for the VoiceNexus Conversational IVR Platform.

---

## 1. Overview of the Knowledge Architecture

VoiceNexus incorporates a high-performance **Telecom Domain Knowledge Base** designed specifically for real-time conversational IVR. Unlike generic web chatbots that generate lengthy walls of text, VoiceNexus delivers **succinct, spoken-voice answers** optimized for telephone delivery within a sub-second response latency budget ($\le 1.0\text{ s}$ SLO).

The knowledge system powers inquiries regarding:
- **eSIM & Device Configuration**: QR code setup, physical-to-eSIM transfer, 5G APN settings.
- **International Roaming**: Global Passport Day Pass rates, enabling data roaming abroad.
- **Wi-Fi & Broadband Hardware**: SSID and password change, optical terminal (ONT) status LEDs, red blinking LOS diagnostic.
- **Account & Porting**: Mobile Number Portability (MNP), generating 6-digit Transfer PINs, moving/service relocation.
- **Billing Policies**: Autopay discounts, paperless billing, equipment returns, avoiding unreturned equipment fees.

---

## 2. Ingestion Methods

VoiceNexus supports four convenient methods to feed data into the AI:

### Method 1: Interactive Web Portal (Recommended for Care-Ops & Admins)

1. Open the VoiceNexus Admin Portal at `http://localhost:8000/admin` (or click **Admin & Knowledge** from the Workspace Selector).
2. Click the **Telecom Knowledge Base (Feed AI Data)** tab at the top.
3. Click **+ New Knowledge Article**.
4. Fill in the article details:
   - **Topic Title**: e.g., `5G Roaming Setup in Japan`
   - **Category**: Select category (e.g., `Roaming & Travel`, `Device & SIM`, `Wi-Fi & Broadband`, `Account & Porting`, `Billing & Payments`).
   - **Keywords**: Comma-separated trigger words and phrases (e.g., `japan roaming, tokyo data, travel pass, data in japan`).
   - **Sample Questions**: One per line representing how callers ask the question.
   - **English Spoken Answer**: Concise response (2-3 sentences), ending with *"Can I help you with anything else today?"*.
   - **Spanish & Hindi Answers (Optional)**: Localized responses for multilingual callers.
5. Click **Save to Knowledge Base**. The changes take effect **immediately** across all active and future calls with zero downtime or restart required.

---

### Method 2: Batch JSON Upload via Admin UI

If you have exported FAQs or articles from existing knowledge bases (Zendesk, Salesforce Service Cloud, ServiceNow, or internal wikis):

1. Open the Admin Portal at `http://localhost:8000/admin` $\to$ **Telecom Knowledge Base**.
2. Click **Batch Import JSON**.
3. Paste a JSON array formatted as follows:

```json
[
  {
    "topic": "5G Standalone (SA) Compatibility",
    "category": "Device & SIM",
    "keywords": ["5g standalone", "5g sa", "true 5g", "5g ultra"],
    "questions": [
      "Does my phone support 5G Standalone?",
      "How do I enable 5G SA on my device?"
    ],
    "answers": {
      "en": "VoiceNexus 5G Standalone is automatically enabled on all 5G-capable devices running the latest OS update. You can verify this under Settings > Cellular > Voice & Data > 5G On. Can I help you with anything else today?",
      "es": "5G Standalone se activa automáticamente en dispositivos compatibles con la última actualización. Verifíquelo en Configuración > Red Móvil. ¿Puedo ayudarle con algo más hoy?",
      "hi": "5G स्टैंडअलोन सभी 5G समर्थित फोन पर स्वचालित रूप से सक्षम है। क्या मैं आपकी किसी और चीज़ में मदद कर सकता हूँ?"
    },
    "action_type": "RESOLVED_INFO"
  }
]
```

4. Click **Import Articles**. The articles will be validated and loaded into active storage.

---

### Method 3: Direct File Configuration (`backend/data/telecom_kb.json`)

Developers and DevOps engineers can manage telecom knowledge directly in source control:

1. Open `backend/data/telecom_kb.json` in your editor.
2. Add, modify, or remove JSON objects in the array.
3. Save the file.
4. VoiceNexus hot-reloads the knowledge file on the next turn or when the **Refresh** button is clicked in the Admin UI.

---

### Method 4: Automated REST API Ingestion

Integrate VoiceNexus into automated CI/CD pipelines or enterprise CRM sync scripts using standard REST endpoints:

#### 1. Retrieve All Knowledge Articles
```http
GET /api/admin/knowledge
```

#### 2. Create or Update an Article
```http
POST /api/admin/knowledge
Content-Type: application/json

{
  "topic": "Wi-Fi 6 Mesh Extender Setup",
  "category": "Equipment & Hardware",
  "keywords": ["mesh extender", "wifi extender", "booster", "dead zone"],
  "questions": [
    "How do I pair my Wi-Fi mesh extender?",
    "Where should I place the Wi-Fi booster?"
  ],
  "answers": {
    "en": "To pair your Wi-Fi 6 extender, plug it in halfway between your router and the weak signal area. Press the WPS button on your main router for 3 seconds, then press WPS on the extender. When the light turns solid white, pairing is complete. Can I help you with anything else today?",
    "es": "Para emparejar su repetidor Wi-Fi, conéctelo a mitad de camino y presione el botón WPS en ambos dispositivos. ¿Puedo ayudarle con algo más hoy?",
    "hi": "वाई-फाई एक्सटेंडर को राउटर के बीच में लगाएं और दोनों पर डब्ल्यूपीएस बटन दबाएं। क्या मैं आपकी किसी और चीज़ में मदद कर सकता हूँ?"
  },
  "action_type": "RESOLVED_INFO"
}
```

#### 3. Delete an Article
```http
DELETE /api/admin/knowledge/{article_id}
```

#### 4. Batch Import Articles
```http
POST /api/admin/knowledge/import
Content-Type: application/json

{
  "articles": [ ... ]
}
```

#### 5. Test Query Matching in Real-Time
```http
POST /api/admin/knowledge/test
Content-Type: application/json

{
  "query": "How do I set up my mesh extender?",
  "language": "en-US"
}
```
**Response**:
```json
{
  "matched": true,
  "article_id": "kb_wifi_6_mesh_extender_setup_10",
  "topic": "Wi-Fi 6 Mesh Extender Setup",
  "category": "Equipment & Hardware",
  "answer": "To pair your Wi-Fi 6 extender, plug it in halfway between your router and the weak signal area...",
  "confidence": 0.94
}
```

---

## 3. Best Practices for Spoken IVR Knowledge

When authoring telecom articles for voice synthesis:

1. **Keep Answers Concise (2-3 Sentences)**:
   Callers cannot re-read a screen. Spoken text should get straight to the solution without preamble or legal disclaimers.
2. **Always End with a Polite Next Step**:
   Conclude with *"Can I help you with anything else today?"* (or *"¿Puedo ayudarle con algo más hoy?"* / *"क्या मैं आपकी किसी और चीज़ में मदद कर सकता हूँ?"*). This prompts the caller to either state their next concern or smoothly trigger the **Call Wrap-Up** flow (*"No, thanks for resolving"*).
3. **Include Broad Conversational Keywords**:
   Include informal terms real customers speak (e.g., for router red light: `red light`, `blinking red`, `los light`, `red dot`, `flashing red`).
4. **Use Phonetic Pronunciation for Telco Acronyms**:
   Terms like `ONT`, `VoIP`, `SSID`, `MNP`, and `APN` are automatically expanded to phonetic equivalents by VoiceNexus pronunciation rules (configured in Admin $\to$ Brand Voice).
