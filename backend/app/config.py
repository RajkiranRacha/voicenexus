import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class VoiceNexusConfig(BaseModel):
    # Server & Port
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Brand Voice & Persona (VN-7)
    DEFAULT_VOICE: str = "en-US-JennyNeural"  # High-quality neural voice via Edge-TTS
    BACKUP_VOICE: str = "en-US-GuyNeural"
    VOICE_RATE: str = "+0%"
    VOICE_PITCH: str = "+0Hz"
    LANGUAGE: str = "en-US"

    # Tenant Prompts (VN-9)
    OPERATOR_NAME: str = "NexusFiber Telco"
    GREETING_PROMPT: str = (
        "Thank you for calling NexusFiber Care. I am your automated digital assistant. "
        "How can I help you today?"
    )
    HOLD_PROMPT: str = "Please hold for just a moment while I pull up your account records."
    CLOSE_PROMPT: str = "Thank you for being a valued NexusFiber customer. Have a great day!"
    ESCALATION_PROMPT: str = (
        "I want to make sure this gets resolved correctly. I am transferring you to one of our "
        "care specialists right now. I've sent them your verified details so you won't have to repeat yourself."
    )

    # Escalation & Safety Thresholds
    MAX_UNRECOGNIZED_TURNS: int = 2
    CONFIRMATION_REQUIRED_FOR_ACTIONS: bool = True
    TARGET_LATENCY_MS: int = 1000

    # Optional AI Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

config = VoiceNexusConfig()
