import os
import json
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
CONFIG_FILE = os.path.join(CONFIG_DIR, "admin_config.json")

class VoiceNexusConfig(BaseModel):
    # Server & Port
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = True

    # Brand Voice & Persona (VN-7)
    DEFAULT_VOICE: str = "en-US-JennyNeural"  # High-quality neural voice via Edge-TTS
    BACKUP_VOICE: str = "en-US-GuyNeural"
    SPANISH_VOICE: str = "es-US-PalomaNeural"
    HINDI_VOICE: str = "hi-IN-SwaraNeural"
    VOICE_RATE: str = "+0%"
    VOICE_PITCH: str = "+0Hz"
    LANGUAGE: str = "en-US"

    # Pronunciation Overrides (VN-7)
    PRONUNCIATION_OVERRIDES: dict[str, str] = {
        r"\bONT\b": "O-N-T",
        r"\bVoIP\b": "Voice over I-P",
        r"\bGbps\b": "gigabits per second",
        r"\bMbps\b": "megabits per second",
        r"\bSSID\b": "Wi-Fi network name",
        r"\bSMS\b": "text message",
        r"\bDTMF\b": "touch tone",
    }

    # Regulatory & Compliance Disclosure (VN-9)
    REGULATORY_DISCLOSURE_ENABLED: bool = True
    REGULATORY_DISCLOSURE_PROMPT: str = (
        "This call may be recorded for quality assurance and uses automated intelligence."
    )

    # Tenant Prompts (VN-9)
    OPERATOR_NAME: str = "NexusFiber Telco"
    GREETING_PROMPT: str = (
        "Thank you for calling NexusFiber Care. I am your automated digital assistant. "
        "How can I help you today?"
    )
    SPANISH_GREETING_PROMPT: str = (
        "Gracias por llamar a NexusFiber Atención al Cliente. Soy su asistente digital automatizado. "
        "¿Cómo le puedo ayudar hoy?"
    )
    HINDI_GREETING_PROMPT: str = (
        "NexusFiber में कॉल करने के लिए धन्यवाद। मैं आपका स्वचालित डिजिटल सहायक हूँ। मैं आज आपकी क्या सहायता कर सकता हूँ?"
    )
    HOLD_PROMPT: str = "Please hold for just a moment while I pull up your account records."
    CLOSE_PROMPT: str = "Thank you for being a valued NexusFiber customer. Have a great day!"
    ESCALATION_PROMPT: str = (
        "I want to make sure this gets resolved correctly. I am transferring you to one of our "
        "care specialists right now. I've sent them your verified details so you won't have to repeat yourself."
    )

    # Demo fallback subscriber ANIs (used when a call session has no verified
    # account yet, e.g. a caller who typed free-form text instead of going
    # through ANI/KBA/OTP verification in the simulator).
    DEFAULT_DEMO_ANI: str = "+15550192834"
    DEFAULT_OUTAGE_DEMO_ANI: str = "+15550148821"

    # Escalation & Safety Thresholds
    MAX_UNRECOGNIZED_TURNS: int = 2
    CONFIRMATION_REQUIRED_FOR_ACTIONS: bool = True
    TARGET_LATENCY_MS: int = 1000

    # Optional AI Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    GROQ_WHISPER_MODEL: str = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    VAPI_API_KEY: str = os.getenv("VAPI_API_KEY", "")
    VAPI_PHONE_NUMBER: str = os.getenv("VAPI_PHONE_NUMBER", "")
    AGENT_FORWARDING_PHONE: str = os.getenv("AGENT_FORWARDING_PHONE", "")

    # WebRTC / NAT Traversal Configuration
    TURN_SERVER_URL: str = os.getenv("TURN_SERVER_URL", "")
    TURN_USERNAME: str = os.getenv("TURN_USERNAME", "")
    TURN_CREDENTIAL: str = os.getenv("TURN_CREDENTIAL", "")
    ICE_SERVERS_JSON: str = os.getenv("ICE_SERVERS_JSON", "")

    # Local Speech-To-Text (VN-STT): server-side transcription via faster-whisper,
    # running fully offline/on-CPU so caller speech recognition doesn't depend on
    # the browser's opaque Web Speech API.
    # Defaults to False in cloud/constrained environments like Render (512MB RAM free tier).
    STT_ENABLED: bool = os.getenv("STT_ENABLED", "false").lower() in ("true", "1", "yes")
    STT_MODEL_SIZE: str = os.getenv("STT_MODEL_SIZE", "tiny")
    STT_DEBUG_LOGGING: bool = os.getenv("STT_DEBUG_LOGGING", "false").lower() in ("true", "1", "yes")

def get_voice_for_language(lang: str, default_voice: str) -> str:
    if lang.startswith("es"):
        if default_voice and (default_voice.startswith("es-") or "Paloma" in default_voice or "Alonso" in default_voice):
            return default_voice
        return config.SPANISH_VOICE
    elif lang.startswith("hi"):
        if default_voice and (default_voice.startswith("hi-") or "Swara" in default_voice or "Madhur" in default_voice):
            return default_voice
        return config.HINDI_VOICE
    else:
        if default_voice and default_voice.startswith("en-"):
            return default_voice
        return config.DEFAULT_VOICE if config.DEFAULT_VOICE.startswith("en-") else "en-US-JennyNeural"

def get_whisper_language_code(lang: str) -> str:
    """BCP-47 locale prefixes ("en-US", "es-US", "hi-IN") already are the
    ISO 639-1 codes faster-whisper expects ("en", "es", "hi")."""
    return lang.split("-")[0].lower() if lang else "en"

config = VoiceNexusConfig()

def save_persisted_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    data = config.model_dump()
    # Ensure sensitive credentials and API keys are never persisted into tracked files
    for k in list(data.keys()):
        upper_k = k.upper()
        if any(term in upper_k for term in ("KEY", "SECRET", "TOKEN", "CREDENTIAL", "PASSWORD")):
            data[k] = ""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def load_persisted_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.items():
                    if hasattr(config, k) and v is not None:
                        setattr(config, k, v)
        except Exception as e:
            print(f"[Config] Error loading persisted config: {e}")

    # Environment variables MUST take precedence over persisted config files
    if "PORT" in os.environ:
        try:
            config.PORT = int(os.environ["PORT"])
        except ValueError:
            pass
    if "HOST" in os.environ:
        config.HOST = os.environ["HOST"]
    if "STT_ENABLED" in os.environ:
        config.STT_ENABLED = os.environ["STT_ENABLED"].lower() in ("true", "1", "yes")
    elif os.environ.get("RENDER") == "true":
        config.STT_ENABLED = False
    if "STT_MODEL_SIZE" in os.environ:
        config.STT_MODEL_SIZE = os.environ["STT_MODEL_SIZE"]
    if "GROQ_API_KEY" in os.environ:
        config.GROQ_API_KEY = os.environ["GROQ_API_KEY"]
    if "GROQ_MODEL" in os.environ:
        config.GROQ_MODEL = os.environ["GROQ_MODEL"]
    if "GROQ_WHISPER_MODEL" in os.environ:
        config.GROQ_WHISPER_MODEL = os.environ["GROQ_WHISPER_MODEL"]
    if "GEMINI_API_KEY" in os.environ:
        config.GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
    if "OPENAI_API_KEY" in os.environ:
        config.OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    if "VAPI_API_KEY" in os.environ:
        config.VAPI_API_KEY = os.environ["VAPI_API_KEY"]
    if "VAPI_PHONE_NUMBER" in os.environ:
        config.VAPI_PHONE_NUMBER = os.environ["VAPI_PHONE_NUMBER"]
    if "AGENT_FORWARDING_PHONE" in os.environ:
        config.AGENT_FORWARDING_PHONE = os.environ["AGENT_FORWARDING_PHONE"]
    if "TURN_SERVER_URL" in os.environ:
        config.TURN_SERVER_URL = os.environ["TURN_SERVER_URL"]
    if "TURN_USERNAME" in os.environ:
        config.TURN_USERNAME = os.environ["TURN_USERNAME"]
    if "TURN_CREDENTIAL" in os.environ:
        config.TURN_CREDENTIAL = os.environ["TURN_CREDENTIAL"]
    if "ICE_SERVERS_JSON" in os.environ:
        config.ICE_SERVERS_JSON = os.environ["ICE_SERVERS_JSON"]

load_persisted_config()

def get_ice_servers() -> list[dict]:
    """
    Returns the array of ICE servers (STUN + TURN) used for WebRTC peer connections.
    Includes multiple redundant public STUN servers by default, plus any configured
    TURN relay servers for traversing symmetric NATs and restrictive firewalls.
    """
    # 1. Custom raw JSON override (e.g. from Metered or Twilio)
    if config.ICE_SERVERS_JSON and config.ICE_SERVERS_JSON.strip():
        try:
            parsed = json.loads(config.ICE_SERVERS_JSON)
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed
        except Exception as e:
            print(f"[Config] Error parsing ICE_SERVERS_JSON: {e}")

    # 2. Default high-reliability public STUN servers
    servers: list[dict] = [
        {"urls": [
            "stun:stun.l.google.com:19302",
            "stun:stun1.l.google.com:19302",
            "stun:stun2.l.google.com:19302",
            "stun:stun.cloudflare.com:3478",
        ]}
    ]

    # 3. Configured TURN relay server
    if config.TURN_SERVER_URL and config.TURN_SERVER_URL.strip():
        urls = [u.strip() for u in config.TURN_SERVER_URL.split(",") if u.strip()]
        turn_entry: dict = {"urls": urls}
        if config.TURN_USERNAME and config.TURN_USERNAME.strip():
            turn_entry["username"] = config.TURN_USERNAME.strip()
        if config.TURN_CREDENTIAL and config.TURN_CREDENTIAL.strip():
            turn_entry["credential"] = config.TURN_CREDENTIAL.strip()
        servers.append(turn_entry)

    return servers


