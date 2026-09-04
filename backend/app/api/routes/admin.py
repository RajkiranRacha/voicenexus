from typing import Optional, Dict
from fastapi import APIRouter
from pydantic import BaseModel
from app.config import config, save_persisted_config
from app.services.tts import tts_service

router = APIRouter(prefix="/api/admin", tags=["Admin Config"])


class VoiceSettingsUpdate(BaseModel):
    voice_name: str
    rate: str = "+0%"
    pitch: str = "+0%"
    language: str = "en-US"


class TenantPromptUpdate(BaseModel):
    operator_name: str
    greeting_prompt: str
    spanish_greeting_prompt: Optional[str] = None
    hindi_greeting_prompt: Optional[str] = None
    hold_prompt: Optional[str] = None
    close_prompt: Optional[str] = None
    escalation_prompt: Optional[str] = None
    regulatory_disclosure_enabled: Optional[bool] = None
    regulatory_disclosure_prompt: Optional[str] = None
    pronunciation_overrides: Optional[Dict[str, str]] = None


@router.get("/config")
def get_admin_config():
    return {
        "operator_name": config.OPERATOR_NAME,
        "greeting_prompt": config.GREETING_PROMPT,
        "spanish_greeting_prompt": config.SPANISH_GREETING_PROMPT,
        "hindi_greeting_prompt": config.HINDI_GREETING_PROMPT,
        "hold_prompt": config.HOLD_PROMPT,
        "close_prompt": config.CLOSE_PROMPT,
        "escalation_prompt": config.ESCALATION_PROMPT,
        "regulatory_disclosure_enabled": config.REGULATORY_DISCLOSURE_ENABLED,
        "regulatory_disclosure_prompt": config.REGULATORY_DISCLOSURE_PROMPT,
        "default_voice": config.DEFAULT_VOICE,
        "spanish_voice": config.SPANISH_VOICE,
        "hindi_voice": config.HINDI_VOICE,
        "voice_rate": config.VOICE_RATE,
        "voice_pitch": config.VOICE_PITCH,
        "language": config.LANGUAGE,
        "pronunciation_overrides": config.PRONUNCIATION_OVERRIDES
    }


@router.post("/voice")
def update_voice_settings(req: VoiceSettingsUpdate):
    config.DEFAULT_VOICE = req.voice_name
    if req.voice_name.startswith("es-"):
        config.SPANISH_VOICE = req.voice_name
    elif req.voice_name.startswith("hi-"):
        config.HINDI_VOICE = req.voice_name
    config.VOICE_RATE = req.rate
    config.VOICE_PITCH = req.pitch
    config.LANGUAGE = req.language
    tts_service.set_voice(req.voice_name, req.rate, req.pitch)
    save_persisted_config()
    return {
        "success": True,
        "active_voice": config.DEFAULT_VOICE,
        "rate": config.VOICE_RATE,
        "language": config.LANGUAGE
    }


@router.post("/prompts")
def update_tenant_prompts(req: TenantPromptUpdate):
    config.OPERATOR_NAME = req.operator_name
    config.GREETING_PROMPT = req.greeting_prompt
    if req.spanish_greeting_prompt is not None:
        config.SPANISH_GREETING_PROMPT = req.spanish_greeting_prompt
    if req.hindi_greeting_prompt is not None:
        config.HINDI_GREETING_PROMPT = req.hindi_greeting_prompt
    if req.hold_prompt is not None:
        config.HOLD_PROMPT = req.hold_prompt
    if req.close_prompt is not None:
        config.CLOSE_PROMPT = req.close_prompt
    if req.escalation_prompt is not None:
        config.ESCALATION_PROMPT = req.escalation_prompt
    if req.regulatory_disclosure_enabled is not None:
        config.REGULATORY_DISCLOSURE_ENABLED = req.regulatory_disclosure_enabled
    if req.regulatory_disclosure_prompt is not None:
        config.REGULATORY_DISCLOSURE_PROMPT = req.regulatory_disclosure_prompt
    if req.pronunciation_overrides is not None:
        config.PRONUNCIATION_OVERRIDES = req.pronunciation_overrides
    save_persisted_config()
    return {"success": True, "operator_name": config.OPERATOR_NAME}
