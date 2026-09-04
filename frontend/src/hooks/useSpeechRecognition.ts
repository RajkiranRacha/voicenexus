import { useRef, useState, useCallback } from 'react';

const ERROR_MESSAGES: Record<string, string> = {
  'no-speech': "Didn't catch that — no speech detected. Try again.",
  'audio-capture': "No microphone was found.",
  'not-allowed': "Microphone access is blocked. Check browser permissions.",
  'network': "Speech recognition network error. Try again.",
};

/**
 * Wraps the browser Web Speech API (SpeechRecognition) for caller utterance capture.
 * Interim results stream to `onInterimResult` so the caller can see what's being
 * heard while speaking; the final result goes to `onFinalResult` for the caller to
 * review/edit before sending, since the API is single-alternative and can mishear
 * words with no confidence check.
 */
export function useSpeechRecognition(
  lang: string,
  onInterimResult: (transcript: string) => void,
  onFinalResult: (transcript: string) => void,
) {
  const [isListening, setIsListening] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  const toggleListening = useCallback(() => {
    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRec) {
      alert("Speech recognition is not supported in this browser. Please use text input or one-click scenarios.");
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    try {
      setError(null);
      const recognition = new SpeechRec();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = lang;

      recognition.onstart = () => setIsListening(true);

      recognition.onresult = (event: any) => {
        const result = event.results[event.results.length - 1];
        const transcript = result[0].transcript;
        if (!transcript) return;
        if (result.isFinal) {
          onFinalResult(transcript);
        } else {
          onInterimResult(transcript);
        }
      };

      recognition.onerror = (event: any) => {
        setError(ERROR_MESSAGES[event?.error] || "Speech recognition error. Please try again or type instead.");
        setIsListening(false);
      };
      recognition.onend = () => setIsListening(false);

      recognitionRef.current = recognition;
      recognition.start();
    } catch {
      setError("Speech recognition error. Please try again or type instead.");
      setIsListening(false);
    }
  }, [isListening, lang, onInterimResult, onFinalResult]);

  return { isListening, error, toggleListening };
}
