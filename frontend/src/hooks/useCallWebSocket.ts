import { useState, useRef, useCallback, useEffect } from 'react';
import type { RefObject } from 'react';
import { apiGet, wsUrl } from '../api/client';
import { useWebRTCPeer } from './useWebRTCPeer';
import { useTtsPlayback } from './useTtsPlayback';
import type { DialogueTurn, CallerProfile, LatencyMetrics } from '../types';

export type CallUiState = 'IDLE' | 'CONNECTING' | 'IN_CALL' | 'ESCALATED' | 'ENDED';

/**
 * Owns the caller-phone WebSocket lifecycle: session start, turn exchange,
 * DTMF/barge-in, and the answerer side of the WebRTC voice bridge to a live
 * agent. Extracted from PhoneSimulator's startCall/ws.onmessage router.
 */
export function useCallWebSocket(agentAudioRef: RefObject<HTMLAudioElement | null>) {
  const [callState, setCallState] = useState<CallUiState>('IDLE');
  const [turns, setTurns] = useState<DialogueTurn[]>([]);
  const [latestLatency, setLatestLatency] = useState<LatencyMetrics | null>(null);
  const [callerProfile, setCallerProfile] = useState<CallerProfile | null>(null);
  const [callLanguage, setCallLanguage] = useState<string>('en-US');
  const [audioDegraded, setAudioDegraded] = useState<boolean>(false);
  const [connectedAgent, setConnectedAgent] = useState<{ id: string; name: string } | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sttPartial, setSttPartial] = useState<{ text: string; confidence: number } | null>(null);
  const [sttFinal, setSttFinal] = useState<{ text: string; confidence: number } | null>(null);
  const [sttError, setSttError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const callStateRef = useRef<CallUiState>(callState);
  const sttLatencyAccumRef = useRef<number>(0);
  useEffect(() => { callStateRef.current = callState; }, [callState]);

  // Sync the pre-call language badge/speech-recognition default from the
  // operator's configured language before any call has started.
  useEffect(() => {
    apiGet<{ language?: string }>('/api/admin/config')
      .then((data) => {
        if (data && data.language) setCallLanguage(data.language);
      })
      .catch(() => {});
  }, []);

  const { isPlayingAudio, playAudioBase64, stopPlayback } = useTtsPlayback();

  const sendIceCandidate = useCallback((candidate: RTCIceCandidateInit) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'RTC_ICE_CANDIDATE', candidate }));
    }
  }, []);

  const onRemoteStream = useCallback((stream: MediaStream) => {
    if (agentAudioRef.current) {
      agentAudioRef.current.srcObject = stream;
      agentAudioRef.current.play().catch(() => {});
    }
  }, [agentAudioRef]);

  const webrtc = useWebRTCPeer({ onIceCandidate: sendIceCandidate, onRemoteStream });

  const handleBargeIn = useCallback(() => {
    stopPlayback();
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'BARGE_IN' }));
    }
  }, [stopPlayback]);

  const startCall = useCallback((ani: string, autoPlayAudio: boolean) => {
    setCallState('CONNECTING');
    setTurns([]);
    setLatestLatency(null);
    setConnectedAgent(null);
    setSessionId(null);

    const ws = new WebSocket(wsUrl('/ws/call'));

    ws.onopen = () => {
      setCallState('IN_CALL');
      ws.send(JSON.stringify({ type: 'START_CALL', ani }));
    };

    ws.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'SESSION_STARTED') {
          if (data.session_id) setSessionId(data.session_id);
          setCallerProfile(data.caller_account || null);
          if (data.language) setCallLanguage(data.language);
          if (data.turn) {
            setTurns([data.turn]);
            if (data.turn.latency) setLatestLatency(data.turn.latency);
          }
          setAudioDegraded(!!data.audio_degraded);
          if (data.audio_base64 && autoPlayAudio) {
            playAudioBase64(data.audio_base64);
          }
        } else if (data.type === 'TURN_RESPONSE') {
          if (data.turn) {
            setTurns(prev => [...prev, data.turn]);
            if (data.turn.latency) setLatestLatency(data.turn.latency);
          }
          if (data.escalated) setCallState('ESCALATED');
          setAudioDegraded(!!data.audio_degraded);
          if (data.audio_base64 && autoPlayAudio) {
            playAudioBase64(data.audio_base64);
          }
        } else if (data.type === 'AGENT_CONNECTED') {
          setCallState('IN_CALL');
          setConnectedAgent({ id: data.agent_id, name: data.agent_name || "Sarah J. (Care Specialist)" });
          setTurns(prev => [
            ...prev,
            {
              turn_id: Date.now(),
              speaker: 'system',
              text: `[Agent Connected]: You are now speaking with ${data.agent_name || 'Sarah J.'}. Your microphone and audio connection are active.`,
              timestamp: new Date().toISOString()
            }
          ]);
        } else if (data.type === 'RTC_OFFER') {
          const answer = await webrtc.answerOffer(data.sdp);
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'RTC_ANSWER', sdp: answer }));
          }
        } else if (data.type === 'RTC_ICE_CANDIDATE') {
          if (data.candidate) await webrtc.addRemoteIceCandidate(data.candidate);
        } else if (data.type === 'AGENT_LIVE_SPEECH') {
          const agentTurn: DialogueTurn = {
            turn_id: Date.now(),
            speaker: 'ai',
            text: data.text,
            timestamp: new Date().toISOString()
          };
          setTurns(prev => [...prev, agentTurn]);

          if ('speechSynthesis' in window && autoPlayAudio) {
            const utter = new SpeechSynthesisUtterance(data.text);
            utter.lang = callLanguage;
            window.speechSynthesis.speak(utter);
          }
        } else if (data.type === 'STT_PARTIAL_RESULT') {
          sttLatencyAccumRef.current += data.stt_ms ?? 0;
          setSttPartial({ text: data.text, confidence: data.confidence });
        } else if (data.type === 'STT_RESULT') {
          sttLatencyAccumRef.current += data.stt_ms ?? 0;
          setSttFinal({ text: data.text, confidence: data.confidence });
        } else if (data.type === 'STT_ERROR') {
          setSttError(data.message);
        } else if (data.type === 'AGENT_DISCONNECT' || data.type === 'CALL_ENDED') {
          setCallState('ENDED');
          setConnectedAgent(null);
          webrtc.close();
        }
      } catch (err) {
        console.error("Caller WS message error:", err);
      }
    };

    ws.onclose = () => {
      if (callStateRef.current !== 'ENDED' && callStateRef.current !== 'ESCALATED') {
        setCallState('ENDED');
      }
    };

    wsRef.current = ws;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playAudioBase64, webrtc]);

  const endCall = useCallback(() => {
    stopPlayback();
    webrtc.close();
    setConnectedAgent(null);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'END_CALL' }));
      wsRef.current.close();
    }
    setCallState('ENDED');
  }, [stopPlayback, webrtc]);

  const sendUtterance = useCallback((text: string, setInputText?: (v: string) => void) => {
    if (!text.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    handleBargeIn();

    const callerTurn: DialogueTurn = {
      turn_id: Date.now(),
      speaker: 'caller',
      text,
      timestamp: new Date().toISOString()
    };
    setTurns(prev => [...prev, callerTurn]);
    setInputText?.('');

    // Real accumulated server-side transcription latency from any mic
    // recording that fed this utterance; 0 for manually-typed text, which is
    // more honest than the flat fake constant this used to send.
    const sttLatencyMs = sttLatencyAccumRef.current;
    sttLatencyAccumRef.current = 0;

    if (connectedAgent) {
      wsRef.current.send(JSON.stringify({ type: 'CALLER_LIVE_SPEECH', text }));
    } else {
      wsRef.current.send(JSON.stringify({ type: 'CALLER_UTTERANCE', text, stt_latency_ms: sttLatencyMs }));
    }
  }, [connectedAgent, handleBargeIn]);

  const sendAudioChunk = useCallback((base64: string, mimeType: string, isFinal: boolean) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'CALLER_AUDIO_CHUNK', audio_base64: base64, mime_type: mimeType, is_final: isFinal }));
    }
  }, []);

  const sendDtmf = useCallback((digit: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    handleBargeIn();
    const callerTurn: DialogueTurn = {
      turn_id: Date.now(),
      speaker: 'caller',
      text: `[DTMF Tone: ${digit}]`,
      timestamp: new Date().toISOString()
    };
    setTurns(prev => [...prev, callerTurn]);
    wsRef.current.send(JSON.stringify({ type: 'DTMF_KEY', digit }));
  }, [handleBargeIn]);

  return {
    callState, turns, latestLatency, callerProfile, callLanguage, audioDegraded, connectedAgent, sessionId,
    isPlayingAudio,
    isCallerMicActive: webrtc.isMicActive,
    isCallerMuted: webrtc.isMuted,
    toggleCallerMute: webrtc.toggleMute,
    sttPartial, sttFinal, sttError, sendAudioChunk,
    startCall, endCall, sendUtterance, sendDtmf, handleBargeIn,
  };
}
