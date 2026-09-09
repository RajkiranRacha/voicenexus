import { useState, useRef, useCallback, useEffect } from 'react';
import type { RefObject } from 'react';
import { apiGet, apiPost, wsUrl } from '../api/client';
import { useWebRTCPeer } from './useWebRTCPeer';
import type { EscalationPayload, DialogueTurn } from '../types';

export interface LiveCallSession {
  turns: DialogueTurn[];
  metadata?: {
    ani?: string;
    customer_name?: string;
    account_number?: string;
    state?: string;
    language?: string;
  };
}

/**
 * Owns the agent-desktop CTI bridge: pending-escalation fetch + queue
 * updates, live transcript streaming, and the offerer side of the WebRTC
 * voice bridge to an accepted caller. Extracted from AgentDesktop's combined
 * fetch+WebSocket effect.
 *
 * Unlike the original inline effect (which re-ran on every activeCallSessionId
 * change, tearing down and reconnecting the whole CTI WebSocket on every
 * accepted/ended call), this connects once and uses a ref for the "is this
 * CALL_ENDED event for my active call" check -- the hub connection now stays
 * up across accept/end-call cycles.
 */
export function useAgentWebSocket(remoteAudioRef: RefObject<HTMLAudioElement | null>) {
  const [escalations, setEscalations] = useState<EscalationPayload[]>([]);
  const [selectedEscalation, setSelectedEscalation] = useState<EscalationPayload | null>(null);
  const [acceptedCalls, setAcceptedCalls] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [liveCalls, setLiveCalls] = useState<Record<string, LiveCallSession>>({});
  const [selectedLiveSessionId, setSelectedLiveSessionId] = useState<string | null>(null);
  const [activeCallSessionId, setActiveCallSessionId] = useState<string | null>(null);
  const [isAudioConnected, setIsAudioConnected] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const activeCallSessionIdRef = useRef<string | null>(null);
  useEffect(() => { activeCallSessionIdRef.current = activeCallSessionId; }, [activeCallSessionId]);

  const sendIceCandidate = useCallback((candidate: RTCIceCandidateInit) => {
    if (wsRef.current?.readyState === WebSocket.OPEN && activeCallSessionIdRef.current) {
      wsRef.current.send(JSON.stringify({
        type: 'RTC_ICE_CANDIDATE',
        session_id: activeCallSessionIdRef.current,
        candidate
      }));
    }
  }, []);

  const onRemoteStream = useCallback((stream: MediaStream) => {
    if (remoteAudioRef.current) {
      remoteAudioRef.current.srcObject = stream;
      remoteAudioRef.current.play().catch(() => {});
      setIsAudioConnected(true);
    }
  }, [remoteAudioRef]);

  const webrtc = useWebRTCPeer({ onIceCandidate: sendIceCandidate, onRemoteStream });

  const endActiveCall = useCallback(() => {
    const sessionId = activeCallSessionIdRef.current;
    if (sessionId && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'AGENT_DISCONNECT', session_id: sessionId }));
    }
    webrtc.close();
    setIsAudioConnected(false);
    setActiveCallSessionId(null);

    if (sessionId) {
      setAcceptedCalls(prev => prev.filter(id => id !== sessionId));
      setEscalations(prev => prev.filter(e => e.session_id !== sessionId));
      setSelectedEscalation(prev => (prev && prev.session_id === sessionId ? null : prev));
    }
  }, [webrtc]);

  useEffect(() => {
    apiGet<EscalationPayload[]>('/api/agent/pending')
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setEscalations(data);
          setSelectedEscalation(data[0]);
        }
      })
      .catch(() => {});

    const ws = new WebSocket(wsUrl('/api/agent/ws'));

    ws.onopen = () => setIsConnected(true);

    ws.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'NEW_ESCALATION') {
          const payload: EscalationPayload = data.payload;
          setEscalations(prev => {
            const exists = prev.some(e => e.session_id === payload.session_id);
            if (exists) return prev;
            return [payload, ...prev];
          });
          setSelectedEscalation(prev => prev || payload);
        } else if (data.type === 'CALL_ACCEPTED') {
          if (data.session_id) {
            setAcceptedCalls(prev => prev.includes(data.session_id) ? prev : [...prev, data.session_id]);
          }
        } else if (data.type === 'TRANSCRIPT_STREAM') {
          const { session_id, turn, metadata } = data;
          setLiveCalls(prev => {
            const existing = prev[session_id] || { turns: [], metadata };
            return {
              ...prev,
              [session_id]: {
                turns: [...existing.turns, turn],
                metadata: metadata || existing.metadata
              }
            };
          });
          setSelectedLiveSessionId(prev => prev || session_id);
        } else if (data.type === 'RTC_ANSWER') {
          if (data.sdp) {
            await webrtc.setRemoteAnswer(data.sdp);
            setIsAudioConnected(true);
          }
        } else if (data.type === 'RTC_ICE_CANDIDATE') {
          if (data.candidate) await webrtc.addRemoteIceCandidate(data.candidate);
        } else if (data.type === 'CALLER_LIVE_SPEECH') {
          const sessId = data.session_id || activeCallSessionIdRef.current;
          if (sessId && data.text) {
            const callerTurn: DialogueTurn = {
              turn_id: Date.now(),
              speaker: 'caller',
              text: data.text,
              timestamp: new Date().toISOString()
            };
            setLiveCalls(prev => {
              const existing = prev[sessId] || { turns: [] };
              return { ...prev, [sessId]: { ...existing, turns: [...existing.turns, callerTurn] } };
            });
          }
        } else if (data.type === 'CALL_ENDED') {
          if (data.session_id) {
            setEscalations(prev => prev.filter(e => e.session_id !== data.session_id));
            setSelectedEscalation(prev => (prev && prev.session_id === data.session_id ? null : prev));
          }
          if (data.session_id === activeCallSessionIdRef.current) {
            endActiveCall();
          }
        }
      } catch (err) {
        console.error("Agent WS message handling error:", err);
      }
    };

    ws.onclose = () => setIsConnected(false);

    wsRef.current = ws;

    return () => {
      ws.close();
      webrtc.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startVoiceConnection = useCallback(async (sessionId: string) => {
    setActiveCallSessionId(sessionId);
    activeCallSessionIdRef.current = sessionId;

    const offer = await webrtc.createOffer();
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'RTC_OFFER', session_id: sessionId, sdp: offer }));
    }
  }, [webrtc]);

  const acceptCall = useCallback((sessionId: string) => {
    apiPost('/api/agent/accept', { session_id: sessionId, agent_id: 'agent-sarah-j' })
      .then(() => {
        setAcceptedCalls(prev => [...prev, sessionId]);
        startVoiceConnection(sessionId);
      });
  }, [startVoiceConnection]);

  const sendAgentLiveSpeech = useCallback((text: string) => {
    if (!text.trim() || !activeCallSessionId) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'AGENT_LIVE_SPEECH',
        session_id: activeCallSessionId,
        text,
        agent_name: 'Sarah J. (Care Specialist)'
      }));
    }

    const agentTurn: DialogueTurn = {
      turn_id: Date.now(),
      speaker: 'ai',
      text: `[Agent Sarah J.]: ${text}`,
      timestamp: new Date().toISOString()
    };

    setLiveCalls(prev => {
      const existing = prev[activeCallSessionId] || { turns: [] };
      return { ...prev, [activeCallSessionId]: { ...existing, turns: [...existing.turns, agentTurn] } };
    });
  }, [activeCallSessionId]);

  return {
    escalations, selectedEscalation, setSelectedEscalation,
    acceptedCalls, isConnected,
    liveCalls, selectedLiveSessionId, setSelectedLiveSessionId,
    activeCallSessionId,
    isMicActive: webrtc.isMicActive, isMuted: webrtc.isMuted, micError: webrtc.micError,
    isAudioConnected,
    toggleMute: webrtc.toggleMute,
    acceptCall, endActiveCall, sendAgentLiveSpeech,
  };
}
