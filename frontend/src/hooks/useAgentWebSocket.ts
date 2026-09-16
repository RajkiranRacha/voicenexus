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
 * voice bridge to an accepted caller.
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
  const [isAutoplayBlocked, setIsAutoplayBlocked] = useState<boolean>(false);
  const [isCallerSpeaking, setIsCallerSpeaking] = useState<boolean>(false);
  const [iceServers, setIceServers] = useState<RTCIceServer[] | undefined>(undefined);

  const wsRef = useRef<WebSocket | null>(null);
  const activeCallSessionIdRef = useRef<string | null>(null);
  const acceptedCallsRef = useRef<string[]>([]);
  const remoteStreamRef = useRef<MediaStream | null>(null);
  const callerSpeakingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => { activeCallSessionIdRef.current = activeCallSessionId; }, [activeCallSessionId]);
  useEffect(() => { acceptedCallsRef.current = acceptedCalls; }, [acceptedCalls]);

  // Fetch dynamic WebRTC ICE configuration (STUN/TURN) from backend
  useEffect(() => {
    apiGet<{ iceServers?: RTCIceServer[] }>('/api/rtc-config')
      .then((data) => {
        if (data && Array.isArray(data.iceServers) && data.iceServers.length > 0) {
          setIceServers(data.iceServers);
        }
      })
      .catch(() => {});
  }, []);

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
    remoteStreamRef.current = stream;
    if (remoteAudioRef.current) {
      remoteAudioRef.current.srcObject = stream;
      remoteAudioRef.current.play()
        .then(() => {
          setIsAutoplayBlocked(false);
        })
        .catch((err) => {
          console.warn('[Agent] Audio autoplay blocked:', err);
          setIsAutoplayBlocked(true);
        });
    }
  }, [remoteAudioRef]);

  // Ensure stream stays attached if remoteAudioRef element is mounted/re-rendered
  useEffect(() => {
    if (remoteAudioRef.current && remoteStreamRef.current) {
      remoteAudioRef.current.srcObject = remoteStreamRef.current;
      remoteAudioRef.current.play()
        .then(() => setIsAutoplayBlocked(false))
        .catch(() => {});
    }
  }, [remoteAudioRef]);

  const unlockAudio = useCallback(() => {
    if (remoteAudioRef.current) {
      remoteAudioRef.current.play()
        .then(() => setIsAutoplayBlocked(false))
        .catch(() => {});
    }
  }, [remoteAudioRef]);

  const webrtc = useWebRTCPeer({
    onIceCandidate: sendIceCandidate,
    onRemoteStream,
    iceServers,
    onConnectionStateChange: (state) => {
      setIsAudioConnected(state === 'connected');
    }
  });

  const isTelephonyCall = Boolean(
    activeCallSessionId?.startsWith('vapi-') || activeCallSessionId?.startsWith('twilio-')
  );

  // Track connection state: Telephony Voice Bridge (PSTN/cellular) or WebRTC P2P (browser)
  useEffect(() => {
    if (isTelephonyCall) {
      setIsAudioConnected(Boolean(activeCallSessionId));
    } else {
      setIsAudioConnected(webrtc.connectionState === 'connected');
    }
  }, [webrtc.connectionState, isTelephonyCall, activeCallSessionId]);

  const endActiveCall = useCallback(() => {
    const sessionId = activeCallSessionIdRef.current;
    if (sessionId && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'AGENT_DISCONNECT', session_id: sessionId }));
    }
    webrtc.close();
    remoteStreamRef.current = null;
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

    let isUnmounted = false;
    let reconnectDelay = 1000;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let heartbeatTimer: ReturnType<typeof setInterval> | null = null;

    const connectWs = () => {
      if (isUnmounted) return;

      const ws = new WebSocket(wsUrl('/api/agent/ws'));

      ws.onopen = () => {
        setIsConnected(true);
        reconnectDelay = 1000;

        // Periodic heartbeat ping every 20s to prevent Render proxy timeout
        if (heartbeatTimer) clearInterval(heartbeatTimer);
        heartbeatTimer = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'PING', timestamp: Date.now() }));
          }
        }, 20000);
      };

      ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'PONG') {
            return;
          } else if (data.type === 'NEW_ESCALATION') {
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

              // Voice exchange: play caller voice through agent laptop speakers
              const isCallActiveWithAgent =
                sessId === activeCallSessionIdRef.current || acceptedCallsRef.current.includes(sessId);

              if (isCallActiveWithAgent) {
                setIsCallerSpeaking(true);
                if (callerSpeakingTimerRef.current) clearTimeout(callerSpeakingTimerRef.current);
                callerSpeakingTimerRef.current = setTimeout(() => setIsCallerSpeaking(false), 3200);

                if (data.audio_base64) {
                  try {
                    const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`);
                    audio.play().catch(() => {
                      if ('speechSynthesis' in window) {
                        const utter = new SpeechSynthesisUtterance(data.text);
                        window.speechSynthesis.speak(utter);
                      }
                    });
                  } catch {
                    if ('speechSynthesis' in window) {
                      const utter = new SpeechSynthesisUtterance(data.text);
                      window.speechSynthesis.speak(utter);
                    }
                  }
                } else if ('speechSynthesis' in window) {
                  const utter = new SpeechSynthesisUtterance(data.text);
                  window.speechSynthesis.speak(utter);
                }
              }
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
          console.error('Agent WS message handling error:', err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        if (heartbeatTimer) clearInterval(heartbeatTimer);
        if (!isUnmounted) {
          reconnectTimer = setTimeout(() => {
            reconnectDelay = Math.min(reconnectDelay * 1.5, 10000);
            connectWs();
          }, reconnectDelay);
        }
      };

      wsRef.current = ws;
    };

    connectWs();

    return () => {
      isUnmounted = true;
      if (heartbeatTimer) clearInterval(heartbeatTimer);
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (wsRef.current) wsRef.current.close();
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

  const transferCallToPhone = useCallback((phoneNumber: string) => {
    const sessionId = activeCallSessionIdRef.current;
    if (sessionId && phoneNumber.trim() && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'AGENT_TRANSFER_PHONE',
        session_id: sessionId,
        phone_number: phoneNumber.trim()
      }));
    }
  }, []);

  return {
    escalations, selectedEscalation, setSelectedEscalation,
    acceptedCalls, isConnected,
    liveCalls, selectedLiveSessionId, setSelectedLiveSessionId,
    activeCallSessionId,
    isMicActive: webrtc.isMicActive, isMuted: webrtc.isMuted, micError: webrtc.micError,
    isAudioConnected,
    isCallerSpeaking,
    isTelephonyCall,
    webrtcConnectionState: webrtc.connectionState,
    iceConnectionState: webrtc.iceConnectionState,
    isAutoplayBlocked,
    unlockAudio,
    toggleMute: webrtc.toggleMute,
    acceptCall, endActiveCall, sendAgentLiveSpeech, transferCallToPhone,
  };
}
