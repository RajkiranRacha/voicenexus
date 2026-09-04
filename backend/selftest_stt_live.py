"""
Self-contained verification: synthesizes real speech via edge-tts, encodes it
to webm/opus exactly like the browser's MediaRecorder would, and sends it
through the ACTUAL running backend's live /ws/call WebSocket as
CALLER_AUDIO_CHUNK messages -- exercising the full real pipeline (decode, VAD,
Whisper inference, confidence gate, response) without needing a human to
speak into a microphone each time.
"""
import asyncio
import base64
import io
import json
import sys

import av
import edge_tts
import numpy as np
import websockets

PHRASES = [
    "How much is my bill?",
    "I want to check my balance and set up a payment arrangement for next Friday.",
    "My internet connection is completely down.",
    "I need to speak to a human representative right now.",
]


async def synth_webm_opus(text: str) -> bytes:
    communicate = edge_tts.Communicate(text=text, voice="en-US-JennyNeural")
    mp3_buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            mp3_buf.write(chunk["data"])
    mp3_buf.seek(0)

    in_container = av.open(mp3_buf)
    resampler = av.AudioResampler(format="fltp", layout="mono", rate=48000)
    frames = []
    for frame in in_container.decode(audio=0):
        for rframe in resampler.resample(frame):
            frames.append(rframe.to_ndarray())
    in_container.close()
    samples = np.concatenate(frames, axis=1)

    out_buf = io.BytesIO()
    container = av.open(out_buf, mode="w", format="webm")
    stream = container.add_stream("libopus", rate=48000)
    frame = av.AudioFrame.from_ndarray(samples, format="fltp", layout="mono")
    frame.rate = 48000
    for packet in stream.encode(frame):
        container.mux(packet)
    for packet in stream.encode(None):
        container.mux(packet)
    container.close()
    return out_buf.getvalue()


async def main():
    uri = "ws://127.0.0.1:8000/ws/call"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "START_CALL", "ani": "+15550192834"}))
        session_resp = json.loads(await ws.recv())
        print(f"[session] {session_resp.get('type')} session_id={session_resp.get('session_id')}")

        for phrase in PHRASES:
            print(f"\n=== spoken: {phrase!r} ===")
            audio_bytes = await synth_webm_opus(phrase)
            b64 = base64.b64encode(audio_bytes).decode("utf-8")
            await ws.send(json.dumps({
                "type": "CALLER_AUDIO_CHUNK",
                "audio_base64": b64,
                "mime_type": "audio/webm;codecs=opus",
                "is_final": True,
            }))
            resp = json.loads(await ws.recv())
            print(f"  -> {resp.get('type')}: text={resp.get('text')!r} "
                  f"confidence={resp.get('confidence')} stt_ms={resp.get('stt_ms')} "
                  f"degraded={resp.get('degraded')}")

        await ws.send(json.dumps({"type": "END_CALL"}))
        try:
            await asyncio.wait_for(ws.recv(), timeout=3)
        except asyncio.TimeoutError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
