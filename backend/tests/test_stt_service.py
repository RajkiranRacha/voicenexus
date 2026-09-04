import io
import pytest
import numpy as np
import av
from app.services.stt import LocalWhisperSttService, stt_service


def _make_webm_opus_clip(seconds: float = 1.0, freq: float = 440.0) -> bytes:
    """Synthesizes a short tone and encodes it to webm/opus in-memory, mimicking
    what the browser's MediaRecorder sends over CALLER_AUDIO_CHUNK."""
    sample_rate = 48000
    t = np.linspace(0, seconds, int(sample_rate * seconds), endpoint=False)
    samples = (0.3 * np.sin(2 * np.pi * freq * t)).astype(np.float32)

    buf = io.BytesIO()
    container = av.open(buf, mode="w", format="webm")
    stream = container.add_stream("libopus", rate=sample_rate)
    frame = av.AudioFrame.from_ndarray(samples.reshape(1, -1), format="fltp", layout="mono")
    frame.rate = sample_rate
    for packet in stream.encode(frame):
        container.mux(packet)
    for packet in stream.encode(None):
        container.mux(packet)
    container.close()
    return buf.getvalue()


@pytest.mark.asyncio
async def test_transcribe_short_circuits_when_unavailable():
    service = object.__new__(LocalWhisperSttService)
    service.available = False
    service.model = None

    result = await service.transcribe(b"irrelevant-bytes", language="en")

    assert result["text"] == ""
    assert result["confidence"] == 0.0
    assert result["stt_ms"] == 0.0


@pytest.mark.asyncio
async def test_transcribe_short_circuits_on_empty_audio():
    result = await stt_service.transcribe(b"", language="en")

    assert result["text"] == ""
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_transcribe_decodes_real_webm_opus_clip_and_measures_latency():
    if not stt_service.available:
        pytest.skip("Local Whisper model unavailable in this environment")

    clip = _make_webm_opus_clip()
    result = await stt_service.transcribe(clip, language="en")

    assert isinstance(result["text"], str)
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["stt_ms"] > 0.0
