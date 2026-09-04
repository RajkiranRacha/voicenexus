import io
import os
import math
import time
import asyncio
from typing import Optional, Dict, Any
from faster_whisper import WhisperModel
from app.config import config

_DEBUG_DUMP_DIR = os.environ.get("STT_DEBUG_DUMP_DIR", "")
_debug_dump_counter = 0


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
            io.BytesIO(audio_bytes),
            language=language,
            # beam_size=1 (greedy decoding) is far more prone to the classic
            # Whisper hallucination/repetition failure mode ("Thank you. Thank
            # you.") on quiet/noisy audio than the library's own default of 5.
            beam_size=5,
            vad_filter=True,
            # The library default min_silence_duration_ms=2000 barely does
            # anything on a ~4s chunk (there's rarely 2 full seconds of
            # silence inside one), so background noise before/after real
            # speech was passing straight to the model. min_speech_duration_ms
            # also defaults to 0, so a single noise blip could register as a
            # "speech" segment. Both tightened for short-chunk streaming use,
            # and the speech-probability threshold raised so only reasonably
            # unambiguous audio reaches the model at all - marginal audio is
            # exactly what triggers confident-sounding hallucinated sentences.
            # speech_pad_ms=2000 (library default 400) matters more than it
            # sounds: live testing showed VAD's default padding clipping the
            # tail of a word right at the chunk boundary, e.g. "i want to
            # check my bill" became "I want to check my guild" purely because
            # trimming cut acoustic context Whisper needed to finish "bill" -
            # confirmed by getting the correct word back once padding widened.
            vad_parameters={"min_silence_duration_ms": 300, "min_speech_duration_ms": 250,
                             "threshold": 0.6, "speech_pad_ms": 2000},
        )
        texts, logprobs = [], []
        # `segments` is a generator - the actual CPU-bound decode/inference work
        # happens while iterating it, so this loop must run inside the same
        # to_thread worker as the rest of this method, not after it returns.
        for seg in segments:
            # Whisper's own no_speech_threshold/log_prob_threshold only
            # influence internal decoding fallback, they don't drop the
            # segment from the output - so a low-confidence/likely-silence
            # segment can still surface as hallucinated text. Gate explicitly.
            # -0.5 was itself too strict: it was tuned against pristine
            # synthetic TTS audio (-0.26 to -0.29) and ended up discarding
            # CORRECT real speech - live testing on the "small" model caught
            # a perfect transcription, 'How much is my bill?', scoring -0.696
            # and getting thrown away. Real human speech (mic distance,
            # background noise, accent) legitimately scores lower confidence
            # than lab-clean audio even when it's completely right. -0.8
            # keeps every correct real-speech example seen so far (-0.44 to
            # -0.72) while still catching the worst outliers (-0.9 to -1.4).
            # It won't cleanly separate every hallucination, but a stray
            # wrong phrase is recoverable in the review-before-send box,
            # whereas silently discarding correct speech is not.
            rejected = seg.no_speech_prob > 0.6 or seg.avg_logprob < -0.8
            if config.STT_DEBUG_LOGGING:
                print(f"[STT] segment {'REJECTED' if rejected else 'accepted'}: "
                      f"text={seg.text.strip()!r} no_speech_prob={seg.no_speech_prob:.3f} "
                      f"avg_logprob={seg.avg_logprob:.3f} compression_ratio={seg.compression_ratio:.3f}")
            if rejected:
                continue
            stripped = seg.text.strip()
            if stripped:
                texts.append(stripped)
                logprobs.append(seg.avg_logprob)
        text = " ".join(texts).strip()
        confidence = max(0.0, min(1.0, math.exp(sum(logprobs) / len(logprobs)))) if logprobs else 0.0
        return {"text": text, "confidence": round(confidence, 3), "language": getattr(info, "language", language)}

    async def transcribe(self, audio_bytes: bytes, language: Optional[str] = None) -> Dict[str, Any]:
        if not self.available or not audio_bytes:
            return {"text": "", "confidence": 0.0, "language": language, "stt_ms": 0.0}
        if _DEBUG_DUMP_DIR:
            global _debug_dump_counter
            _debug_dump_counter += 1
            path = os.path.join(_DEBUG_DUMP_DIR, f"chunk_{_debug_dump_counter:04d}_{len(audio_bytes)}b.webm")
            try:
                with open(path, "wb") as f:
                    f.write(audio_bytes)
            except Exception as e:
                print(f"[STT] debug dump failed: {e}")
        start = time.perf_counter()
        result = await asyncio.to_thread(self._transcribe_sync, audio_bytes, language)
        result["stt_ms"] = round((time.perf_counter() - start) * 1000, 1)
        return result


stt_service = LocalWhisperSttService()
