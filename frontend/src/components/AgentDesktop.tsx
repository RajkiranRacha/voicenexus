import React, { useState, useEffect, useRef } from 'react';
import { 
  Headphones, ShieldCheck, UserCheck, 
  MessageSquare, CheckCircle2, Sparkles, Inbox, Radio, Lightbulb,
  Mic, MicOff, PhoneOff, Volume2, Send, AlertCircle
} from 'lucide-react';
import type { EscalationPayload, DialogueTurn } from '../types';

interface LiveCallSession {
  turns: DialogueTurn[];
  metadata?: {
    ani?: string;
    customer_name?: string;
    account_number?: string;
    state?: string;
    language?: string;
  };
}

export const AgentDesktop: React.FC = () => {
  const [escalations, setEscalations] = useState<EscalationPayload[]>([]);
  const [selectedEscalation, setSelectedEscalation] = useState<EscalationPayload | null>(null);
  const [acceptedCalls, setAcceptedCalls] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'ESCALATIONS' | 'LIVE_STREAM'>('ESCALATIONS');
  const [liveCalls, setLiveCalls] = useState<Record<string, LiveCallSession>>({});
  const [selectedLiveSessionId, setSelectedLiveSessionId] = useState<string | null>(null);

  // Active Two-Way Voice Call States
  const [activeCallSessionId, setActiveCallSessionId] = useState<string | null>(null);
  const [isMicActive, setIsMicActive] = useState<boolean>(false);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [micError, setMicError] = useState<string | null>(null);
  const [agentSpeechText, setAgentSpeechText] = useState<string>('');
  const [isAudioConnected, setIsAudioConnected] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const remoteAudioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    // Fetch any currently pending escalations via REST
    fetch('/api/agent/pending')
      .then(res => res.json())
      .then((data: EscalationPayload[]) => {
        if (Array.isArray(data) && data.length > 0) {
          setEscalations(data);
          setSelectedEscalation(data[0]);
        }
      })
      .catch(() => {});

    // Open Real-time WebSocket connection to Agent Hub
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/agent/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
    };

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
          if (pcRef.current && data.sdp) {
            await pcRef.current.setRemoteDescription(new RTCSessionDescription(data.sdp));
            setIsAudioConnected(true);
          }
        } else if (data.type === 'RTC_ICE_CANDIDATE') {
          if (pcRef.current && data.candidate) {
            try {
              await pcRef.current.addIceCandidate(new RTCIceCandidate(data.candidate));
            } catch (e) {
              // ignore duplicate candidate
            }
          }
        } else if (data.type === 'CALLER_LIVE_SPEECH') {
          // Live caller speech transcription received
          const sessId = data.session_id || activeCallSessionId;
          if (sessId && data.text) {
            const callerTurn: DialogueTurn = {
              turn_id: Date.now(),
              speaker: 'caller',
              text: data.text,
              timestamp: new Date().toISOString()
            };
            setLiveCalls(prev => {
              const existing = prev[sessId] || { turns: [] };
              return {
                ...prev,
                [sessId]: {
                  ...existing,
                  turns: [...existing.turns, callerTurn]
                }
              };
            });
          }
        } else if (data.type === 'CALL_ENDED') {
          // Caller ended the call
          if (data.session_id === activeCallSessionId) {
            endActiveCall();
          }
        }
      } catch (err) {
        console.error("Agent WS message handling error:", err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
      localStreamRef.current?.getTracks().forEach(t => t.stop());
      pcRef.current?.close();
    };
  }, [activeCallSessionId]);

  const startVoiceConnection = async (sessionId: string) => {
    setActiveCallSessionId(sessionId);
    setMicError(null);
    let stream: MediaStream | null = null;

    // 1. Request microphone access immediately
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      localStreamRef.current = stream;
      setIsMicActive(true);
      setIsMuted(false);
    } catch (err: any) {
      console.warn("Microphone access failed:", err);
      setMicError(
        err.name === 'NotAllowedError'
          ? "Microphone permission was denied by browser. Please allow microphone in browser settings to speak directly."
          : "No microphone device found. You can still transmit voice responses using quick speech."
      );
      setIsMicActive(false);
    }

    // 2. Setup WebRTC Peer Connection
    try {
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      });
      pcRef.current = pc;

      if (stream) {
        stream.getAudioTracks().forEach(track => {
          pc.addTrack(track, stream!);
        });
      }

      pc.ontrack = (event) => {
        if (remoteAudioRef.current && event.streams[0]) {
          remoteAudioRef.current.srcObject = event.streams[0];
          remoteAudioRef.current.play().catch(() => {});
          setIsAudioConnected(true);
        }
      };

      pc.onicecandidate = (event) => {
        if (event.candidate && wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'RTC_ICE_CANDIDATE',
            session_id: sessionId,
            candidate: event.candidate
          }));
        }
      };

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'RTC_OFFER',
          session_id: sessionId,
          sdp: offer
        }));
      }
    } catch (err) {
      console.error("WebRTC initialization error:", err);
    }
  };

  const acceptCall = (sessionId: string) => {
    fetch('/api/agent/accept', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, agent_id: 'agent-sarah-j' })
    })
      .then(res => res.json())
      .then(() => {
        setAcceptedCalls(prev => [...prev, sessionId]);
        startVoiceConnection(sessionId);
      });
  };

  const toggleMute = () => {
    if (localStreamRef.current) {
      const nextMute = !isMuted;
      localStreamRef.current.getAudioTracks().forEach(track => {
        track.enabled = !nextMute;
      });
      setIsMuted(nextMute);
    }
  };

  const endActiveCall = () => {
    if (activeCallSessionId) {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'AGENT_DISCONNECT',
          session_id: activeCallSessionId
        }));
      }
    }
    localStreamRef.current?.getTracks().forEach(track => track.stop());
    localStreamRef.current = null;
    pcRef.current?.close();
    pcRef.current = null;
    setIsMicActive(false);
    setIsAudioConnected(false);
    setActiveCallSessionId(null);
  };

  const sendAgentLiveSpeech = (text: string) => {
    if (!text.trim() || !activeCallSessionId) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'AGENT_LIVE_SPEECH',
        session_id: activeCallSessionId,
        text: text,
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
      return {
        ...prev,
        [activeCallSessionId]: {
          ...existing,
          turns: [...existing.turns, agentTurn]
        }
      };
    });

    setAgentSpeechText('');
  };

  const getNextBestAction = (intent: string, balance: number, reason: string) => {
    if (reason.includes("OUT_OF_SCOPE") || reason.includes("DISPUTE")) {
      return {
        action: "Specialized Billing Review",
        recommendation: "Review line-item charges on latest invoice. Customer requested split-payment or fee dispute which requires manual adjustment override.",
        tip: "You have authority to issue a courtesy credit of up to $25 without supervisor sign-off."
      };
    }
    if (intent.includes("BILLING") || intent.includes("PAYMENT")) {
      return {
        action: "Payment Resolution & Autopay Enrollment",
        recommendation: `Customer balance is $${balance.toFixed(2)}. Offer 3-month split arrangement or $10 monthly discount for Autopay sign-up.`,
        tip: "Confirm payment promise in BSS to prevent automatic service suspension."
      };
    }
    if (intent.includes("OUTAGE")) {
      return {
        action: "Active Service Restoration Check",
        recommendation: "Regional fiber outage active. Inform customer repair crew is on-site with estimated restoration in 2 hours. Do NOT dispatch a truck.",
        tip: "Enroll customer in automated SMS restoration alerts."
      };
    }
    if (intent.includes("PLAN")) {
      return {
        action: "Loyalty Upgrade Offer",
        recommendation: "Eligible for Gigabit Pro 1000 promotion ($110/mo) with free Wi-Fi 6 gateway upgrade.",
        tip: "Mention 1-year price lock guarantee to close the upgrade."
      };
    }
    return {
      action: "Active Listening & Inquiry Clarification",
      recommendation: "Acknowledge the customer's previous turns in IVR. Confirm their primary issue directly without asking them to repeat basic information.",
      tip: "Customer identity has already been verified via VoiceNexus."
    };
  };

  const activeLiveSessions = Object.keys(liveCalls);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Top Banner with Navigation Tabs */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center">
            <Headphones className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <span>Agent Desktop & CTI Screen-Pop</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                isConnected ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400'
              }`}>
                {isConnected ? 'CTI Bridge Live' : 'Disconnected'}
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Zero-repetition customer handoff with verified identity and AI Next-Best-Action guidance.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveTab('ESCALATIONS')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
              activeTab === 'ESCALATIONS'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <Inbox className="w-3.5 h-3.5" />
            <span>Escalation Queue ({escalations.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('LIVE_STREAM')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
              activeTab === 'LIVE_STREAM'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <Radio className="w-3.5 h-3.5 text-cyan-400" />
            <span>Live Calls ({activeLiveSessions.length})</span>
          </button>
        </div>
      </div>

      {activeTab === 'ESCALATIONS' ? (
        /* Escalations Queue Layout */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left List: Incoming Escalation Queue */}
          <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                <Inbox className="w-3.5 h-3.5 text-indigo-400" />
                <span>Pending Escalations ({escalations.length})</span>
              </span>
            </div>

            <div className="space-y-2 max-h-[580px] overflow-y-auto pr-1">
              {escalations.length === 0 ? (
                <div className="p-8 text-center text-slate-500 text-xs">
                  <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-slate-600 stroke-[1.5]" />
                  No escalated calls waiting in queue.
                  <div className="text-[11px] text-slate-600 mt-1">
                    Calls requiring human care will automatically pop here.
                  </div>
                </div>
              ) : (
                escalations.map((esc) => {
                  const isSelected = selectedEscalation?.session_id === esc.session_id;
                  const isAccepted = acceptedCalls.includes(esc.session_id);

                  return (
                    <button
                      key={esc.session_id}
                      onClick={() => setSelectedEscalation(esc)}
                      className={`w-full text-left p-3.5 rounded-xl border text-xs transition-all cursor-pointer ${
                        isSelected
                          ? 'border-indigo-500 bg-indigo-950/40 shadow-md'
                          : 'border-slate-800 bg-slate-950/50 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-slate-200">
                          {esc.customer_profile.customer_name}
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.2 rounded font-medium ${
                          isAccepted ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'
                        }`}>
                          {isAccepted ? 'Answered' : 'Awaiting Agent'}
                        </span>
                      </div>
                      <div className="text-slate-400 text-[11px] truncate">
                        {esc.call_context.primary_intent}
                      </div>
                      <div className="flex items-center justify-between mt-2 text-[10px] text-slate-500">
                        <span>Queue: {esc.recommended_agent_queue}</span>
                        <span>{esc.call_context.duration_in_ivr_seconds}s in IVR</span>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Panel: Selected Call Handoff Payload & Live Transcript */}
          <div className="lg:col-span-8 space-y-4">
            {selectedEscalation ? (
              <div className="space-y-4">
                {/* Structured Handoff Card (VN-5) */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
                  <div className="flex items-start justify-between pb-4 border-b border-slate-800">
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="text-base font-bold text-slate-100">
                          {selectedEscalation.customer_profile.customer_name}
                        </h3>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center space-x-1 font-semibold">
                          <ShieldCheck className="w-3 h-3" />
                          <span>{selectedEscalation.customer_profile.auth_status}</span>
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        ANI: {selectedEscalation.ani} · Account: {selectedEscalation.customer_profile.account_number}
                      </div>
                    </div>

                    <div>
                      {/* Audio element for playing caller's voice */}
                      <audio ref={remoteAudioRef} autoPlay />

                      {!acceptedCalls.includes(selectedEscalation.session_id) ? (
                        <button
                          onClick={() => acceptCall(selectedEscalation.session_id)}
                          className="py-2 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl text-xs flex items-center space-x-2 shadow-lg shadow-emerald-950/40 transition-all cursor-pointer"
                        >
                          <UserCheck className="w-4 h-4" />
                          <span>Accept & Answer Call</span>
                        </button>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <button
                            type="button"
                            onClick={toggleMute}
                            className={`py-2 px-3.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                              isMuted
                                ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-950/40'
                                : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
                            }`}
                            title={isMuted ? 'Unmute microphone' : 'Mute microphone'}
                          >
                            {isMuted ? <MicOff className="w-3.5 h-3.5 text-white" /> : <Mic className="w-3.5 h-3.5 text-emerald-400" />}
                            <span>{isMuted ? 'Muted' : 'Mute Mic'}</span>
                          </button>

                          <button
                            type="button"
                            onClick={endActiveCall}
                            className="py-2 px-3.5 bg-rose-700 hover:bg-rose-600 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 shadow-lg shadow-rose-950/40 transition-all cursor-pointer"
                            title="Disconnect active voice call"
                          >
                            <PhoneOff className="w-3.5 h-3.5" />
                            <span>End Call</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Two-Way Voice Connection Status & Mic Banner */}
                  {acceptedCalls.includes(selectedEscalation.session_id) && (
                    <div className="bg-emerald-950/40 border border-emerald-800/80 rounded-xl p-3.5 space-y-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center space-x-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                          <span className="text-xs font-bold text-emerald-300">
                            Voice Call Active with Customer ({selectedEscalation.customer_profile.customer_name})
                          </span>
                        </div>
                        <div className="flex items-center space-x-2 text-xs">
                          <span className={`px-2.5 py-1 rounded-lg border font-semibold flex items-center space-x-1.5 ${
                            isMicActive 
                              ? (isMuted ? 'bg-amber-950 text-amber-300 border-amber-800' : 'bg-emerald-900/60 text-emerald-300 border-emerald-700')
                              : 'bg-rose-950 text-rose-300 border-rose-800'
                          }`}>
                            {isMicActive ? (
                              isMuted ? <MicOff className="w-3 h-3 text-amber-400" /> : <Mic className="w-3 h-3 text-emerald-400 animate-pulse" />
                            ) : (
                              <AlertCircle className="w-3 h-3 text-rose-400" />
                            )}
                            <span>
                              {isMicActive ? (isMuted ? 'Microphone: Muted' : 'Microphone: Live (Active)') : 'Microphone: Inactive / Denied'}
                            </span>
                          </span>

                          <span className={`px-2.5 py-1 rounded-lg border font-semibold flex items-center space-x-1.5 ${
                            isAudioConnected ? 'bg-cyan-950 text-cyan-300 border-cyan-800' : 'bg-slate-800 text-slate-300 border-slate-700'
                          }`}>
                            <Volume2 className="w-3 h-3 text-cyan-400" />
                            <span>{isAudioConnected ? 'Two-Way Audio: Connected' : 'Audio Stream: Initializing...'}</span>
                          </span>
                        </div>
                      </div>

                      {micError && (
                        <div className="text-[11px] text-amber-300 bg-amber-950/60 border border-amber-800/60 rounded-lg p-2 flex items-center space-x-1.5">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-amber-400" />
                          <span>{micError}</span>
                        </div>
                      )}

                      {/* Agent Quick Response / Live Speech Input */}
                      <div className="pt-2 border-t border-emerald-900/50 space-y-2">
                        <div className="text-[11px] font-semibold text-slate-300 flex items-center justify-between">
                          <span>Speak to Caller / Quick Handoff Responses:</span>
                          <span className="text-[10px] text-slate-400">Streams voice & text directly to customer's ear</span>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                          {[
                            `Hello ${selectedEscalation.customer_profile.customer_name}, my name is Sarah. I see your verified details here and can assist you right away.`,
                            "I have reviewed your billing arrangement. Let's get this scheduled for you.",
                            "Our technicians are currently addressing the fiber node in your area. Service will restore shortly.",
                            "I can apply the promotional Gigabit upgrade to your account with free equipment."
                          ].map((canned, i) => (
                            <button
                              key={i}
                              type="button"
                              onClick={() => sendAgentLiveSpeech(canned)}
                              className="text-left p-1.5 rounded-lg bg-slate-900 hover:bg-indigo-950/80 border border-slate-800 hover:border-indigo-700/80 text-[11px] text-slate-300 hover:text-white transition-all cursor-pointer"
                            >
                              "{canned}"
                            </button>
                          ))}
                        </div>

                        <div className="flex space-x-2 pt-1">
                          <input
                            type="text"
                            value={agentSpeechText}
                            onChange={(e) => setAgentSpeechText(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && sendAgentLiveSpeech(agentSpeechText)}
                            placeholder="Type or speak a live response to caller..."
                            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                          />
                          <button
                            type="button"
                            disabled={!agentSpeechText.trim()}
                            onClick={() => sendAgentLiveSpeech(agentSpeechText)}
                            className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl text-xs font-semibold flex items-center space-x-1 transition-all cursor-pointer"
                          >
                            <Send className="w-3.5 h-3.5" />
                            <span>Transmit</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* AI Executive Summary Pill */}
                  <div className="bg-indigo-950/40 border border-indigo-900/60 rounded-xl p-3.5 space-y-2">
                    <div className="flex items-center space-x-1.5 text-xs font-bold text-indigo-300">
                      <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                      <span>AI-Prepared Context (Do Not Ask Customer to Repeat)</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                      <div>
                        <div className="text-slate-400 text-[11px]">Primary Intent</div>
                        <div className="font-semibold text-slate-200">
                          {selectedEscalation.call_context.primary_intent}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400 text-[11px]">Escalation Reason</div>
                        <div className="font-semibold text-amber-300">
                          {selectedEscalation.resolution_summary.failure_or_escalation_reason}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400 text-[11px]">Current Balance</div>
                        <div className="font-semibold text-slate-200">
                          ${selectedEscalation.resolution_summary.current_balance?.toFixed(2) || '0.00'}
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-slate-300 pt-1 border-t border-indigo-900/40">
                      <span className="text-slate-400 font-medium">Notes: </span>
                      {selectedEscalation.resolution_summary.notes}
                    </div>
                  </div>

                  {/* AI Next-Best-Action Guidance (VN-10) */}
                  {(() => {
                    const nba = getNextBestAction(
                      selectedEscalation.call_context.primary_intent,
                      selectedEscalation.resolution_summary.current_balance || 0,
                      selectedEscalation.resolution_summary.failure_or_escalation_reason || ""
                    );
                    return (
                      <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 space-y-1.5 text-xs">
                        <div className="flex items-center space-x-1.5 text-cyan-300 font-bold">
                          <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                          <span>AI Next-Best-Action: {nba.action}</span>
                        </div>
                        <p className="text-slate-300 leading-relaxed">{nba.recommendation}</p>
                        <div className="text-[11px] text-emerald-400/90 font-medium pt-1">
                          Tip: {nba.tip}
                        </div>
                      </div>
                    );
                  })()}

                  {/* Live Transcript Overlay (VN-10) */}
                  <div className="space-y-2">
                    <div className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                      <MessageSquare className="w-3.5 h-3.5 text-indigo-400" />
                      <span>IVR Transcript & Pre-Handoff Dialogue</span>
                    </div>
                    <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 max-h-[240px] overflow-y-auto space-y-2.5 text-xs">
                      {selectedEscalation.transcript_snippet.length === 0 ? (
                        <div className="text-slate-500 text-center py-4">No prior turns captured.</div>
                      ) : (
                        selectedEscalation.transcript_snippet.map((t, i) => (
                          <div key={i} className="flex space-x-2">
                            <span className={`font-semibold text-[11px] min-w-[70px] ${
                              t.speaker === 'caller' ? 'text-indigo-400' : 'text-slate-400'
                            }`}>
                              {t.speaker === 'caller' ? 'Caller:' : 'VoiceNexus:'}
                            </span>
                            <span className="text-slate-200 flex-1">{t.text}</span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 text-xs shadow-xl">
                Select an escalated call on the left to inspect the structured handoff payload.
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Real-Time Live Call Monitor View (VN-10) */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
            <div className="pb-3 border-b border-slate-800 mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
              <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
              <span>In-Flight Call Streams ({activeLiveSessions.length})</span>
            </div>

            <div className="space-y-2 max-h-[580px] overflow-y-auto pr-1">
              {activeLiveSessions.length === 0 ? (
                <div className="p-8 text-center text-slate-500 text-xs">
                  <Radio className="w-8 h-8 mx-auto mb-2 text-slate-600 stroke-[1.5]" />
                  No live calls currently streaming.
                  <div className="text-[11px] text-slate-600 mt-1">
                    Start a call in Phone Simulator to watch real-time turns pop here.
                  </div>
                </div>
              ) : (
                activeLiveSessions.map((sId) => {
                  const call = liveCalls[sId];
                  const isSelected = selectedLiveSessionId === sId;
                  return (
                    <button
                      key={sId}
                      onClick={() => setSelectedLiveSessionId(sId)}
                      className={`w-full text-left p-3.5 rounded-xl border text-xs transition-all cursor-pointer ${
                        isSelected
                          ? 'border-indigo-500 bg-indigo-950/40 shadow-md'
                          : 'border-slate-800 bg-slate-950/50 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-slate-200">
                          {call.metadata?.customer_name || 'In-Flight Caller'}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-medium">
                          {call.metadata?.state || 'IN_PROGRESS'}
                        </span>
                      </div>
                      <div className="text-slate-400 text-[11px]">
                        Session: {sId} · Turns: {call.turns.length}
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Live Call Dialogue Stream Pane */}
          <div className="lg:col-span-8 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            {selectedLiveSessionId && liveCalls[selectedLiveSessionId] ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div>
                    <h3 className="font-bold text-slate-100 text-sm">
                      Live Stream: {liveCalls[selectedLiveSessionId].metadata?.customer_name || selectedLiveSessionId}
                    </h3>
                    <div className="text-xs text-slate-400">
                      ANI: {liveCalls[selectedLiveSessionId].metadata?.ani || 'Unknown'} · State: {liveCalls[selectedLiveSessionId].metadata?.state}
                    </div>
                  </div>
                  <span className="text-xs text-emerald-400 flex items-center space-x-1 font-semibold">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                    <span>Real-Time Overlay Active</span>
                  </span>
                </div>

                <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 max-h-[460px] overflow-y-auto space-y-3 text-xs">
                  {liveCalls[selectedLiveSessionId].turns.map((t, idx) => (
                    <div key={idx} className={`flex ${t.speaker === 'caller' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[80%] rounded-xl px-3.5 py-2 leading-relaxed ${
                        t.speaker === 'caller'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-800 text-slate-200 border border-slate-700'
                      }`}>
                        <div className="text-[10px] opacity-75 font-semibold mb-0.5">
                          {t.speaker === 'caller' ? 'Caller' : 'VoiceNexus AI'}
                        </div>
                        <div>{t.text}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-slate-500 text-xs">
                Select a live session to monitor dialogue turns in real-time.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
