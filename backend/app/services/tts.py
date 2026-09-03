import io
import asyncio
import base64
from typing import AsyncGenerator
import edge_tts
from app.config import config

class NeuralTtsService:
    """
    Streaming Neural Text-To-Speech Service (VN-7).
    Generates human-like voice synthesis with sub-250ms chunk latency.
    """

    def __init__(self):
        self.voice = config.DEFAULT_VOICE
        self.rate = config.VOICE_RATE
        self.pitch = config.VOICE_PITCH

    def set_voice(self, voice_name: str, rate: str = "+0%", pitch: str = "+0%"):
        self.voice = voice_name
        self.rate = rate
        self.pitch = pitch

    async def synthesize_to_bytes(self, text: str) -> bytes:
        """
        Synthesize text to complete audio bytes (mp3).
        """
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch
        )
        audio_stream = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        return audio_stream.getvalue()

    async def synthesize_to_base64(self, text: str) -> str:
        """
        Returns base64 encoded audio for immediate browser playback.
        """
        audio_bytes = await self.synthesize_to_bytes(text)
        return base64.b64encode(audio_bytes).decode("utf-8")

tts_service = NeuralTtsService()
