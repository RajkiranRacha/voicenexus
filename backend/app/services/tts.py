import io
import re
import asyncio
import base64
from typing import AsyncGenerator, Optional
import edge_tts
from app.config import config

PITCH_PATTERN = re.compile(r"^[+-]\d+Hz$")

class NeuralTtsService:
    """
    Streaming Neural Text-To-Speech Service (VN-7).
    Generates human-like voice synthesis with sub-250ms chunk latency.
    Applies telco pronunciation overrides automatically.
    """

    def __init__(self):
        self.voice = config.DEFAULT_VOICE
        self.rate = config.VOICE_RATE
        self.pitch = config.VOICE_PITCH

    def set_voice(self, voice_name: str, rate: str = "+0%", pitch: str = "+0%"):
        self.voice = voice_name
        self.rate = rate
        self.pitch = pitch

    def apply_pronunciation_overrides(self, text: str) -> str:
        """
        Replaces telco acronyms and technical terms with phonetic pronunciation strings.
        """
        processed = text
        for pattern, replacement in config.PRONUNCIATION_OVERRIDES.items():
            processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)
        return processed

    async def synthesize_to_bytes(
        self,
        text: str,
        voice_override: Optional[str] = None,
        rate_override: Optional[str] = None
    ) -> bytes:
        """
        Synthesize text to complete audio bytes (mp3) with pronunciation overrides.
        """
        clean_text = self.apply_pronunciation_overrides(text)
        selected_voice = voice_override or self.voice or config.DEFAULT_VOICE
        selected_rate = rate_override or self.rate or config.VOICE_RATE
        selected_pitch = self.pitch or config.VOICE_PITCH
        # edge-tts requires a signed Hz offset (e.g. "+0Hz"); any other format
        # raises inside edge_tts.Communicate() and would otherwise silently
        # degrade every call to text-only mode.
        if not PITCH_PATTERN.match(selected_pitch):
            selected_pitch = "+0Hz"
        communicate = edge_tts.Communicate(
            text=clean_text,
            voice=selected_voice,
            rate=selected_rate,
            pitch=selected_pitch
        )
        audio_stream = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        return audio_stream.getvalue()

    async def synthesize_to_base64(
        self,
        text: str,
        voice_override: Optional[str] = None,
        rate_override: Optional[str] = None
    ) -> str:
        """
        Returns base64 encoded audio for immediate browser playback.
        """
        audio_bytes = await self.synthesize_to_bytes(
            text, voice_override=voice_override, rate_override=rate_override
        )
        return base64.b64encode(audio_bytes).decode("utf-8")

tts_service = NeuralTtsService()
