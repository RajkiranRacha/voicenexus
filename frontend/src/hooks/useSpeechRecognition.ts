import { useRef, useState, useCallback, useEffect } from 'react';

const CHUNK_MS = 2500;
const CANDIDATE_MIME_TYPES = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus'];

const MIC_ERROR_MESSAGES: Record<string, string> = {
  NotAllowedError: "Microphone access is blocked. Check browser permissions.",
  NotFoundError: "No microphone device found.",
};

function pickSupportedMimeType(): string | null {
  const MR = (window as any).MediaRecorder;
  if (!MR) return null;
  return CANDIDATE_MIME_TYPES.find((t) => MR.isTypeSupported?.(t)) || '';
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = reader.result as string;
      resolve(result.split(',')[1] || '');
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

type SttResult = { text: string; confidence: number } | null;

/**
 * Captures caller speech via MediaRecorder and streams it to the backend for
 * server-side transcription (local Whisper, see app/services/stt.py), instead
 * of relying on the browser's opaque Web Speech API. Each ~2.5s recording
 * cycle produces one self-contained webm/opus clip (MediaRecorder chunks
 * emitted via `timeslice` are NOT independently decodable, so a stop/restart
 * loop is used instead) sent over the existing call WebSocket; the resulting
 * transcript text accumulates into the review box via onInterimResult /
 * onFinalResult so a mis-transcription can be caught before it's sent.
 */
export function useSpeechRecognition(
  _lang: string,
  onInterimResult: (transcript: string) => void,
  onFinalResult: (transcript: string) => void,
  sendAudioChunk: (base64: string, mimeType: string, isFinal: boolean) => void,
  sttPartial: SttResult,
  sttFinal: SttResult,
) {
  const [isListening, setIsListening] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const mimeTypeRef = useRef<string>('');
  const isListeningRef = useRef<boolean>(false);
  const stoppingRef = useRef<boolean>(false);
  const chunkTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const accumulatedTextRef = useRef<string>('');

  const appendText = useCallback((piece: string) => {
    if (!piece) return accumulatedTextRef.current;
    accumulatedTextRef.current = (accumulatedTextRef.current + ' ' + piece).trim();
    return accumulatedTextRef.current;
  }, []);

  useEffect(() => {
    if (sttPartial) onInterimResult(appendText(sttPartial.text));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sttPartial]);

  useEffect(() => {
    if (sttFinal) onFinalResult(appendText(sttFinal.text));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sttFinal]);

  const startChunk = useCallback((stream: MediaStream) => {
    const mimeType = mimeTypeRef.current;
    const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
    recorderRef.current = recorder;
    const parts: BlobPart[] = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) parts.push(e.data);
    };

    recorder.onstop = async () => {
      const isFinal = stoppingRef.current;
      const blob = new Blob(parts, { type: mimeType || recorder.mimeType });
      if (blob.size > 0) {
        try {
          const base64 = await blobToBase64(blob);
          sendAudioChunk(base64, blob.type, isFinal);
        } catch {
          setError("Speech recognition error. Please try again or type instead.");
        }
      }
      if (isFinal) {
        streamRef.current?.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        setIsListening(false);
      } else if (isListeningRef.current && streamRef.current) {
        startChunk(streamRef.current);
      }
    };

    recorder.onerror = () => {
      setError("Speech recognition error. Please try again or type instead.");
    };

    recorder.start();
    chunkTimeoutRef.current = setTimeout(() => {
      if (recorderRef.current === recorder && recorder.state === 'recording') {
        recorder.stop();
      }
    }, CHUNK_MS);
  }, [sendAudioChunk]);

  const toggleListening = useCallback(() => {
    if (isListening) {
      isListeningRef.current = false;
      stoppingRef.current = true;
      if (chunkTimeoutRef.current) clearTimeout(chunkTimeoutRef.current);
      if (recorderRef.current && recorderRef.current.state !== 'inactive') {
        recorderRef.current.stop();
      } else {
        streamRef.current?.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        setIsListening(false);
      }
      return;
    }

    if (!(window as any).MediaRecorder || !navigator.mediaDevices?.getUserMedia) {
      alert("Voice recording is not supported in this browser. Please use text input or one-click scenarios.");
      return;
    }

    setError(null);
    if (!mimeTypeRef.current) {
      const supported = pickSupportedMimeType();
      if (supported === null) {
        alert("Voice recording is not supported in this browser. Please use text input or one-click scenarios.");
        return;
      }
      mimeTypeRef.current = supported;
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
      .then((stream) => {
        streamRef.current = stream;
        accumulatedTextRef.current = '';
        stoppingRef.current = false;
        isListeningRef.current = true;
        setIsListening(true);
        startChunk(stream);
      })
      .catch((err: any) => {
        setError(MIC_ERROR_MESSAGES[err?.name] || "Could not access the microphone. Please try again or type instead.");
        setIsListening(false);
      });
  }, [isListening, startChunk]);

  return { isListening, error, toggleListening };
}
