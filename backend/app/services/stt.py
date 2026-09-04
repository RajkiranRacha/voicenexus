import io
import math
import time
import asyncio
from typing import Optional, Dict, Any
from faster_whisper import WhisperModel
from app.config import config


class LocalWhisperSttService:
    """
    Server-side Speech-To-Text (VN-STT) using a locally-hosted Whisper model
    via faster-whisper/CTranslate2. Runs fully offline on CPU once the model
    weights are cached, replacing the browser's opaque Web Speech API with
    transcription we control and can attach confidence scores to.
    """

    def __init__(self):
        self.available = False
        self.model: Optional[WhisperModel] = None
        if not config.STT_ENABLED:
            print("[STT] Disabled via config; caller mic input unavailable, text/DTMF only.")
            return
        try:
            self.model = WhisperModel(config.STT_MODEL_SIZE, device="cpu", compute_type="int8")
            self.available = True
        except Exception as e:
            print(f"[STT] Degraded mode: failed to load model '{config.STT_MODEL_SIZE}' ({e}).")

    def _transcribe_sync(self, audio_bytes: bytes, language: Optional[str]) -> Dict[str, Any]:
        segments, info = self.model.transcribe(
            io.BytesIO(audio_bytes), language=language, beam_size=1, vad_filter=True,
        )
        texts, logprobs = [], []
        # `segments` is a generator - the actual CPU-bound decode/inference work
        # happens while iterating it, so this loop must run inside the same
        # to_thread worker as the rest of this method, not after it returns.
        for seg in segments:
            texts.append(seg.text.strip())
            logprobs.append(seg.avg_logprob)
        text = " ".join(t for t in texts if t).strip()
        confidence = max(0.0, min(1.0, math.exp(sum(logprobs) / len(logprobs)))) if logprobs else 0.0
        return {"text": text, "confidence": round(confidence, 3), "language": getattr(info, "language", language)}

    async def transcribe(self, audio_bytes: bytes, language: Optional[str] = None) -> Dict[str, Any]:
        if not self.available or not audio_bytes:
            return {"text": "", "confidence": 0.0, "language": language, "stt_ms": 0.0}
        start = time.perf_counter()
        result = await asyncio.to_thread(self._transcribe_sync, audio_bytes, language)
        result["stt_ms"] = round((time.perf_counter() - start) * 1000, 1)
        return result


stt_service = LocalWhisperSttService()
