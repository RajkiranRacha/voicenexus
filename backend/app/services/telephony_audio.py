import io
import wave
import audioop
import av
from typing import List

class TelephonyAudioService:
    """
    Telephony Audio Transcoding & Signal Processing Service.
    Converts between PSTN/Twilio 8,000Hz G.711 μ-law (PCMU) audio
    and standard 16-bit PCM WAV / MP3 used by Whisper STT & Edge-TTS.
    """

    @staticmethod
    def mulaw_to_wav(mulaw_bytes: bytes) -> bytes:
        """
        Converts 8,000Hz mono 8-bit μ-law audio frames into a standard
        16-bit mono 8,000Hz PCM WAV file in memory.
        """
        if not mulaw_bytes:
            return b""
        pcm_data = audioop.ulaw2lin(mulaw_bytes, 2)
        wav_buf = io.BytesIO()
        with wave.open(wav_buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(8000)
            wf.writeframes(pcm_data)
        return wav_buf.getvalue()

    @staticmethod
    def mp3_to_mulaw(mp3_bytes: bytes) -> bytes:
        """
        Decodes synthesized MP3 speech (e.g. from Edge-TTS), resamples to
        8,000Hz mono, and encodes into G.711 μ-law bytes for Twilio.
        """
        if not mp3_bytes:
            return b""
        in_buf = io.BytesIO(mp3_bytes)
        container = av.open(in_buf, mode="r", format="mp3")
        resampler = av.AudioResampler(format="s16", layout="mono", rate=8000)

        pcm_chunks = []
        for frame in container.decode(audio=0):
            for resampled in resampler.resample(frame):
                pcm_chunks.append(resampled.to_ndarray().tobytes())

        raw_pcm_8k = b"".join(pcm_chunks)
        return audioop.lin2ulaw(raw_pcm_8k, 2)

    @staticmethod
    def chunk_mulaw(mulaw_bytes: bytes, chunk_size: int = 160) -> List[bytes]:
        """
        Splits a stream of 8kHz μ-law bytes into 20ms frames (160 bytes each).
        Twilio expects 20ms frames in each WebSocket media payload.
        """
        return [mulaw_bytes[i:i + chunk_size] for i in range(0, len(mulaw_bytes), chunk_size)]

    @staticmethod
    def calculate_rms(mulaw_bytes: bytes) -> int:
        """
        Calculates Root-Mean-Square (RMS) volume energy of a μ-law audio chunk.
        Silence is typically < 250; human voice speech is typically > 600.
        """
        if not mulaw_bytes:
            return 0
        pcm = audioop.ulaw2lin(mulaw_bytes, 2)
        return audioop.rms(pcm, 2)


telephony_audio = TelephonyAudioService()
