import re
from typing import Optional, Dict
from fastapi import APIRouter
from pydantic import BaseModel, field_validator
from app.config import config, save_persisted_config
from app.services.tts import tts_service

router = APIRouter(prefix="/api/admin", tags=["Admin Config"])

# edge-tts requires pitch as a signed Hz offset (e.g. "+0Hz"), not a percent
# string like the rate field -- a mismatched format raises inside
# edge_tts.Communicate() and silently degrades every subsequent call to
# text-only mode (see NeuralTtsService._synthesize_safe).
PITCH_PATTERN = re.compile(r"^[+-]\d+Hz$")


class VoiceSettingsUpdate(BaseModel):
    voice_name: str
    rate: str = "+0%"
    pitch: str = "+0Hz"
    language: str = "en-US"

    @field_validator("pitch")
    @classmethod
    def validate_pitch(cls, v: str) -> str:
        if not PITCH_PATTERN.match(v):
            return "+0Hz"
        return v


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


from app.services.telecom_kb import telecom_kb_service


class KnowledgeArticleModel(BaseModel):
    id: Optional[str] = None
    topic: str
    category: str = "General"
    keywords: list[str] = []
    questions: list[str] = []
    answers: Dict[str, str] = {}
    action_type: str = "RESOLVED_INFO"


class KnowledgeTestRequest(BaseModel):
    query: str
    language: str = "en-US"


class KnowledgeImportRequest(BaseModel):
    articles: list[Dict]


@router.get("/knowledge")
def get_knowledge_base():
    """Retrieve all telecom domain knowledge articles (Defect-2)."""
    return telecom_kb_service.get_all()


@router.post("/knowledge")
def upsert_knowledge_article(article: KnowledgeArticleModel):
    """Add or edit a telecom knowledge article."""
    saved = telecom_kb_service.upsert_article(article.model_dump())
    return {"success": True, "article": saved}


@router.delete("/knowledge/{article_id}")
def delete_knowledge_article(article_id: str):
    """Delete a telecom knowledge article."""
    success = telecom_kb_service.delete_article(article_id)
    return {"success": success, "article_id": article_id}


@router.post("/knowledge/import")
def import_knowledge_articles(req: KnowledgeImportRequest):
    """Batch import knowledge articles from JSON."""
    count = telecom_kb_service.import_batch(req.articles)
    return {"success": True, "imported_count": count}


@router.post("/knowledge/test")
def test_knowledge_query(req: KnowledgeTestRequest):
    """Test how the AI resolves a given query using the telecom KB."""
    match = telecom_kb_service.find_match(req.query, language=req.language)
    if match:
        return {"matched": True, **match}
    return {"matched": False, "message": "No article matched with confidence >= 0.70. Would trigger standard flow or escalation."}
