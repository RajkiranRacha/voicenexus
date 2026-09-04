import { useRef, useState, useCallback } from 'react';

/** Plays base64-encoded neural TTS audio clips and tracks playback/barge-in state. */
export function useTtsPlayback() {
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);

  const playAudioBase64 = useCallback((base64String: string) => {
    try {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
      }
      const audio = new Audio(`data:audio/mp3;base64,${base64String}`);
      currentAudioRef.current = audio;
      setIsPlayingAudio(true);

      audio.onended = () => setIsPlayingAudio(false);
      audio.onerror = () => setIsPlayingAudio(false);
      audio.play().catch(() => setIsPlayingAudio(false));
    } catch {
      setIsPlayingAudio(false);
    }
  }, []);

  const stopPlayback = useCallback(() => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      setIsPlayingAudio(false);
    }
  }, []);

  return { isPlayingAudio, playAudioBase64, stopPlayback };
}
