import React, { useState, useEffect, useRef } from 'react';
import { 
  Phone, PhoneOff, Mic, MicOff, Volume2, Radio, 
  Send, ShieldCheck, Zap, Globe
} from 'lucide-react';
import type { DialogueTurn, CallerProfile, LatencyMetrics } from '../types';

const PRESET_CALLERS = [
  {
    name: "Jordan Rivera",
    ani: "+15550192834",
    scenario: "Billing balance ($142.50), card on file, payment promise"
  },
  {
    name: "Elena Vance",
    ani: "+15550148821",
    scenario: "Seattle Metro area broadband outage"
  },
  {
    name: "Marcus Brody",
    ani: "+15550173399",
    scenario: "Degraded Wi-Fi gateway / packet loss triage"
  },
  {
    name: "Unregistered Caller (Unknown ANI)",
    ani: "+15559990000",
    scenario: "Requires KBA Auth (Account # or Zip code 94107)"
  }
];

const PRESET_UTTERANCES = [
  { label: "Pay Bill Now (Card on File)", text: "I want to pay my bill now using the card on file." },
  { label: "Confirm Card Payment", text: "Yes, please charge my card." },
  { label: "Check Balance & Pay Next Week", text: "How much is my bill and can I set up a payment arrangement for next Friday?" },
  { label: "KBA Auth: Verify Zip 94107", text: "My billing zip code is 94107." },
  { label: "Bilingual: Switch to Spanish", text: "Quiero hablar en español." },
  { label: "Bilingual: Switch to English", text: "Please switch back to English." },
  { label: "Pronunciation: ONT & VoIP Status", text: "What is my ONT and VoIP speed status?" },
  { label: "Check Internet Outage", text: "My internet connection is completely down." },
  { label: "Opt-in to SMS Outage Alerts", text: "Yes, please enroll me in text alerts." },
  { label: "Approve Router Reboot", text: "Yes, go ahead and send the reset signal to reboot my router." },
  { label: "Inquire Plan & Upgrade", text: "What plan am I on and can I upgrade to gigabit speed?" },
  { label: "Schedule a Callback", text: "I'd like to schedule a callback for tomorrow morning." },
  { label: "Explicit Agent Request", text: "I need to speak to a human representative right now." }
];

export const PhoneSimulator: React.FC = () => {
  const [selectedAni, setSelectedAni] = useState<string>(PRESET_CALLERS[0].ani);
  const [customAni, setCustomAni] = useState<string>("");
  const [callState, setCallState] = useState<'IDLE' | 'CONNECTING' | 'IN_CALL' | 'ESCALATED' | 'ENDED'>('IDLE');
  const [turns, setTurns] = useState<DialogueTurn[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [latestLatency, setLatestLatency] = useState<LatencyMetrics | null>(null);
  const [callerProfile, setCallerProfile] = useState<CallerProfile | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);
  const [autoPlayAudio, setAutoPlayAudio] = useState<boolean>(true);
  const [callLanguage, setCallLanguage] = useState<string>('en-US');
  const [isListening, setIsListening] = useState<boolean>(false);

  // Live Agent Connection States
  const [connectedAgent, setConnectedAgent] = useState<{ id: string; name: string } | null>(null);
  const [isCallerMuted, setIsCallerMuted] = useState<boolean>(false);
  const [isCallerMicActive, setIsCallerMicActive] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const agentAudioRef = useRef<HTMLAudioElement | null>(null);
  const callerPcRef = useRef<RTCPeerConnection | null>(null);
  const callerStreamRef = useRef<MediaStream | null>(null);
  const chatBottomRef = useRef<HTMLDivElement | null>(null);
  const recognitionRef = useRef<any>(null);

  const activeAni = customAni.trim() || selectedAni;

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns]);

  useEffect(() => {
    fetch('/api/admin/config')
      .then(res => res.json())
      .then(data => {
        if (data && data.language) {
          setCallLanguage(data.language);
        }
      })
      .catch(() => {});
  }, []);

  const toggleListening = () => {
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
      const recognition = new SpeechRec();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = callLanguage;

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          sendUtterance(transcript);
        }
        setIsListening(false);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch {
      setIsListening(false);
    }
  };

  const handleIncomingRtcOffer = async (sdpOffer: any) => {
    try {
      let stream = callerStreamRef.current;
      if (!stream) {
        try {
          stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          callerStreamRef.current = stream;
          setIsCallerMicActive(true);
          setIsCallerMuted(false);
        } catch (e) {
          console.warn("Caller microphone access unavailable:", e);
        }
      }

      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      });
      callerPcRef.current = pc;

      if (stream) {
        stream.getAudioTracks().forEach(track => {
          pc.addTrack(track, stream!);
        });
      }

      pc.ontrack = (event) => {
        if (agentAudioRef.current && event.streams[0]) {
          agentAudioRef.current.srcObject = event.streams[0];
          agentAudioRef.current.play().catch(() => {});
        }
      };

      pc.onicecandidate = (event) => {
        if (event.candidate && wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'RTC_ICE_CANDIDATE',
            candidate: event.candidate
          }));
        }
      };

      await pc.setRemoteDescription(new RTCSessionDescription(sdpOffer));
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);

      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'RTC_ANSWER',
          sdp: answer
        }));
      }
    } catch (err) {
      console.error("Error answering WebRTC offer:", err);
    }
  };

  const toggleCallerMute = () => {
    if (callerStreamRef.current) {
      const nextMute = !isCallerMuted;
      callerStreamRef.current.getAudioTracks().forEach(track => {
        track.enabled = !nextMute;
      });
      setIsCallerMuted(nextMute);
    }
  };

  const startCall = () => {
    setCallState('CONNECTING');
    setTurns([]);
    setLatestLatency(null);
    setConnectedAgent(null);

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/call`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setCallState('IN_CALL');
      ws.send(JSON.stringify({
        type: 'START_CALL',
        ani: activeAni
      }));
    };

    ws.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'SESSION_STARTED') {
          if (data.caller_account) {
            setCallerProfile(data.caller_account);
          } else {
            setCallerProfile(null);
          }
          if (data.language) {
            setCallLanguage(data.language);
          }
          if (data.turn) {
            setTurns([data.turn]);
            if (data.turn.latency) {
              setLatestLatency(data.turn.latency);
            }
          }
          if (data.audio_base64 && autoPlayAudio) {
            playAudioBase64(data.audio_base64);
          }
        } else if (data.type === 'TURN_RESPONSE') {
          if (data.turn) {
            setTurns(prev => [...prev, data.turn]);
            if (data.turn.latency) {
              setLatestLatency(data.turn.latency);
            }
          }
          if (data.escalated) {
            setCallState('ESCALATED');
          }
          if (data.audio_base64 && autoPlayAudio) {
            playAudioBase64(data.audio_base64);
          }
        } else if (data.type === 'AGENT_CONNECTED') {
          // Agent answered the transfer!
          setCallState('IN_CALL');
          setConnectedAgent({
            id: data.agent_id,
            name: data.agent_name || "Sarah J. (Care Specialist)"
          });
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
          await handleIncomingRtcOffer(data.sdp);
        } else if (data.type === 'RTC_ICE_CANDIDATE') {
          if (callerPcRef.current && data.candidate) {
            try {
              await callerPcRef.current.addIceCandidate(new RTCIceCandidate(data.candidate));
            } catch (e) {
              // ignore
            }
          }
        } else if (data.type === 'AGENT_LIVE_SPEECH') {
          const agentTurn: DialogueTurn = {
            turn_id: Date.now(),
            speaker: 'ai',
            text: data.text,
            timestamp: new Date().toISOString()
          };
          setTurns(prev => [...prev, agentTurn]);

          // Speak agent's words locally through speech synthesis if available
          if ('speechSynthesis' in window && autoPlayAudio) {
            const utter = new SpeechSynthesisUtterance(data.text);
            utter.lang = callLanguage;
            window.speechSynthesis.speak(utter);
          }
        } else if (data.type === 'AGENT_DISCONNECT' || data.type === 'CALL_ENDED') {
          setCallState('ENDED');
          setConnectedAgent(null);
          callerStreamRef.current?.getTracks().forEach(t => t.stop());
          callerPcRef.current?.close();
        }
      } catch (err) {
        console.error("Caller WS message error:", err);
      }
    };

    ws.onclose = () => {
      if (callState !== 'ENDED' && callState !== 'ESCALATED') {
        setCallState('ENDED');
      }
    };

    wsRef.current = ws;
  };

  const endCall = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      setIsPlayingAudio(false);
    }
    callerStreamRef.current?.getTracks().forEach(t => t.stop());
    callerStreamRef.current = null;
    callerPcRef.current?.close();
    callerPcRef.current = null;
    setIsCallerMicActive(false);
    setConnectedAgent(null);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'END_CALL' }));
      wsRef.current.close();
    }
    setCallState('ENDED');
  };

  const playAudioBase64 = (base64String: string) => {
    try {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
      }
      const audio = new Audio(`data:audio/mp3;base64,${base64String}`);
      currentAudioRef.current = audio;
      setIsPlayingAudio(true);

      audio.onended = () => {
        setIsPlayingAudio(false);
      };
      audio.onerror = () => {
        setIsPlayingAudio(false);
      };
      audio.play().catch(() => {
        setIsPlayingAudio(false);
      });
    } catch {
      setIsPlayingAudio(false);
    }
  };

  const handleBargeIn = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      setIsPlayingAudio(false);
    }
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'BARGE_IN' }));
    }
  };

  const sendUtterance = (text: string) => {
    if (!text.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    
    handleBargeIn();

    const callerTurn: DialogueTurn = {
      turn_id: Date.now(),
      speaker: 'caller',
      text: text,
      timestamp: new Date().toISOString()
    };
    setTurns(prev => [...prev, callerTurn]);
    setInputText('');

    if (connectedAgent) {
      wsRef.current.send(JSON.stringify({
        type: 'CALLER_LIVE_SPEECH',
        text: text
      }));
    } else {
      wsRef.current.send(JSON.stringify({
        type: 'CALLER_UTTERANCE',
        text: text,
        stt_latency_ms: 120.0
      }));
    }
  };

  const sendDtmf = (digit: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    handleBargeIn();
    const callerTurn: DialogueTurn = {
      turn_id: Date.now(),
      speaker: 'caller',
      text: `[DTMF Tone: ${digit}]`,
      timestamp: new Date().toISOString()
    };
    setTurns(prev => [...prev, callerTurn]);
    wsRef.current.send(JSON.stringify({
      type: 'DTMF_KEY',
      digit: digit
    }));
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-7xl mx-auto">
      {/* Audio element for playing live agent voice */}
      <audio ref={agentAudioRef} autoPlay />

      {/* Left Column: Phone Console & Audio Telemetry */}
      <div className="lg:col-span-4 space-y-4">
        {/* Softphone Hardware Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                connectedAgent ? 'bg-emerald-400 animate-ping' :
                callState === 'IN_CALL' ? 'bg-emerald-500 animate-pulse' :
                callState === 'ESCALATED' ? 'bg-amber-500' :
                callState === 'CONNECTING' ? 'bg-blue-500 animate-pulse' : 'bg-slate-600'
              }`} />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                {connectedAgent ? `Live with ${connectedAgent.name}` :
                 callState === 'IN_CALL' ? 'Active Call In-Flow' :
                 callState === 'ESCALATED' ? 'Escalated to Agent' :
                 callState === 'CONNECTING' ? 'Connecting to SBC...' : 'Line Idle'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setAutoPlayAudio(!autoPlayAudio)}
                className={`p-1.5 rounded-lg text-xs flex items-center space-x-1 ${
                  autoPlayAudio ? 'bg-indigo-950 text-indigo-300 border border-indigo-700' : 'bg-slate-800 text-slate-400'
                }`}
                title="Toggle Audio Voice Playback"
              >
                <Volume2 className="w-3.5 h-3.5" />
                <span>{autoPlayAudio ? 'Voice On' : 'Muted'}</span>
              </button>
            </div>
          </div>

          {/* Caller Identity Selection */}
          <div className="mt-4 space-y-2">
            <label className="text-xs font-medium text-slate-300">Simulate Inbound Caller (ANI):</label>
            <div className="space-y-1.5">
              {PRESET_CALLERS.map((c) => (
                <button
                  key={c.ani}
                  disabled={callState === 'IN_CALL' || callState === 'CONNECTING'}
                  onClick={() => { setSelectedAni(c.ani); setCustomAni(""); }}
                  className={`w-full text-left p-2.5 rounded-xl border text-xs transition-all cursor-pointer ${
                    activeAni === c.ani
                      ? 'border-indigo-500 bg-indigo-950/40 text-white'
                      : 'border-slate-800 bg-slate-950/50 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="font-semibold text-slate-200">{c.name} ({c.ani})</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{c.scenario}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Active Call Controls */}
          <div className="mt-5 pt-4 border-t border-slate-800">
            {callState === 'IDLE' || callState === 'ENDED' ? (
              <button
                onClick={startCall}
                className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-emerald-950/40 transition-all cursor-pointer"
              >
                <Phone className="w-5 h-5" />
                <span>Dial Care Line (+1 800 NEXUS-CARE)</span>
              </button>
            ) : (
              <div className="space-y-2">
                <button
                  onClick={endCall}
                  className="w-full py-2.5 px-4 bg-rose-600 hover:bg-rose-500 text-white font-semibold rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-rose-950/40 transition-all cursor-pointer"
                >
                  <PhoneOff className="w-4 h-4" />
                  <span>Disconnect Call</span>
                </button>

                {connectedAgent ? (
                  <button
                    type="button"
                    onClick={toggleCallerMute}
                    className={`w-full py-2 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center space-x-2 transition-all cursor-pointer ${
                      isCallerMuted 
                        ? 'border-rose-500/80 bg-rose-950/50 text-rose-200' 
                        : 'border-emerald-800 bg-emerald-950/40 text-emerald-300'
                    }`}
                  >
                    {isCallerMuted ? <MicOff className="w-3.5 h-3.5 text-rose-400" /> : <Mic className="w-3.5 h-3.5 text-emerald-400" />}
                    <span>{isCallerMuted ? 'Caller Mic Muted (Click to Unmute)' : 'Caller Mic Live (Click to Mute)'}</span>
                  </button>
                ) : (
                  /* Barge-in Interruption Button */
                  <button
                    onClick={handleBargeIn}
                    disabled={!isPlayingAudio}
                    className={`w-full py-2 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center space-x-2 transition-all ${
                      isPlayingAudio 
                        ? 'border-amber-500/80 bg-amber-950/50 text-amber-200 animate-pulse cursor-pointer'
                        : 'border-slate-800 bg-slate-900/50 text-slate-500 cursor-not-allowed'
                    }`}
                  >
                    <MicOff className="w-3.5 h-3.5" />
                    <span>{isPlayingAudio ? 'Barge-In (Interrupt AI Speech)' : 'AI Not Speaking'}</span>
                  </button>
                )}
              </div>
            )}
          </div>

          {/* DTMF Dialpad (VN-9 degraded mode fallback) */}
          <div className="mt-5 pt-4 border-t border-slate-800">
            <div className="text-[11px] font-semibold uppercase text-slate-400 mb-2 flex items-center justify-between">
              <span>DTMF Touch-Tone Keypad</span>
              <span className="text-[10px] text-slate-500 font-normal">0 = Operator</span>
            </div>
            <div className="grid grid-cols-3 gap-1.5">
              {['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'].map((digit) => (
                <button
                  key={digit}
                  disabled={callState !== 'IN_CALL'}
                  onClick={() => sendDtmf(digit)}
                  className="py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 active:bg-indigo-600 text-slate-200 font-mono text-sm font-semibold disabled:opacity-40 transition-all cursor-pointer"
                >
                  {digit}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Real-Time Sub-Second Latency Telemetry Badge */}
        {latestLatency && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <span>Turn Latency Budget</span>
              </span>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                latestLatency.total_turn_ms <= 1000 
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                  : 'bg-amber-950 text-amber-300 border border-amber-800'
              }`}>
                {latestLatency.total_turn_ms} ms (SLO: ≤1000ms)
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center text-[11px]">
              <div className="bg-slate-950 p-2 rounded-lg border border-slate-800/60">
                <div className="text-slate-500">STT ASR</div>
                <div className="font-semibold text-slate-300">{latestLatency.stt_ms} ms</div>
              </div>
              <div className="bg-slate-950 p-2 rounded-lg border border-slate-800/60">
                <div className="text-slate-500">NLU / FSM</div>
                <div className="font-semibold text-indigo-300">{latestLatency.nlu_ms} ms</div>
              </div>
              <div className="bg-slate-950 p-2 rounded-lg border border-slate-800/60">
                <div className="text-slate-500">Neural TTS</div>
                <div className="font-semibold text-cyan-300">{latestLatency.tts_ms} ms</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Right Column: Live Conversation Transcript & Interactive Utterance Prompts */}
      <div className="lg:col-span-8 flex flex-col space-y-4">
        {/* Caller Context Banner */}
        {callerProfile ? (
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-3.5 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center font-bold">
                {callerProfile.customer_name[0]}
              </div>
              <div>
                <div className="font-semibold text-slate-200 flex items-center space-x-1.5">
                  <span>{callerProfile.customer_name}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border flex items-center space-x-1 ${
                    callerProfile.auth_status === 'OTP_VERIFIED' ? 'bg-purple-950 text-purple-300 border-purple-800' :
                    callerProfile.auth_status === 'KBA_VERIFIED' ? 'bg-emerald-950 text-emerald-300 border-emerald-800' :
                    'bg-indigo-950 text-indigo-300 border-indigo-800'
                  }`}>
                    <ShieldCheck className="w-2.5 h-2.5" />
                    <span>{callerProfile.auth_status}</span>
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 flex items-center space-x-1">
                    <Globe className="w-2.5 h-2.5 text-cyan-400" />
                    <span>{callLanguage}</span>
                  </span>
                </div>
                <div className="text-slate-400 text-[11px]">
                  Acc: {callerProfile.account_number} · {callerProfile.plan_name} · Bal: ${callerProfile.current_balance.toFixed(2)}
                </div>
              </div>
            </div>
            <div className="text-right text-[11px] text-slate-400 hidden sm:block">
              <div>Zip: {callerProfile.zip_code}</div>
              <div className={callerProfile.has_active_outage ? 'text-rose-400 font-semibold' : 'text-slate-400'}>
                {callerProfile.has_active_outage ? '⚠ Area Outage Active' : 'Network Nominal'}
              </div>
            </div>
          </div>
        ) : callState === 'IN_CALL' ? (
          <div className="bg-amber-950/40 border border-amber-900/60 rounded-2xl p-3.5 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2 text-amber-300">
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              <span>
                <strong>Unregistered ANI ({activeAni}):</strong> Awaiting Knowledge-Based Authentication (say Account # or Zip Code 94107).
              </span>
            </div>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 flex items-center space-x-1">
              <Globe className="w-2.5 h-2.5 text-cyan-400" />
              <span>{callLanguage}</span>
            </span>
          </div>
        ) : null}

        {/* Connected to Live Agent Banner */}
        {connectedAgent && (
          <div className="bg-emerald-950/60 border border-emerald-800/90 rounded-2xl p-3.5 flex flex-wrap items-center justify-between gap-2 text-xs shadow-lg shadow-emerald-950/30">
            <div className="flex items-center space-x-2.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              <div>
                <div className="font-bold text-emerald-300 flex items-center space-x-1.5">
                  <span>Connected to Live Care Specialist</span>
                  <span className="text-white bg-emerald-800/80 px-2 py-0.5 rounded-md text-[11px]">
                    {connectedAgent.name}
                  </span>
                </div>
                <div className="text-[11px] text-emerald-400/80">
                  Two-way voice connection active · You can speak directly to the specialist
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <span className={`px-2.5 py-1 rounded-lg border text-[11px] font-semibold flex items-center space-x-1.5 ${
                isCallerMicActive
                  ? (isCallerMuted ? 'bg-amber-950 text-amber-300 border-amber-800' : 'bg-emerald-900/80 text-emerald-200 border-emerald-700')
                  : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}>
                {isCallerMuted ? <MicOff className="w-3 h-3 text-amber-400" /> : <Mic className="w-3 h-3 text-emerald-400 animate-pulse" />}
                <span>{isCallerMuted ? 'Mic: Muted' : 'Mic: Live (Active)'}</span>
              </span>

              <button
                type="button"
                onClick={toggleCallerMute}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-[11px] font-medium transition-all cursor-pointer"
              >
                {isCallerMuted ? 'Unmute' : 'Mute'}
              </button>
            </div>
          </div>
        )}

        {/* Live Audio & Transcript Display */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex-1 flex flex-col h-[480px] shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
            <span className="text-xs font-semibold text-slate-300 flex items-center space-x-2">
              <Radio className="w-3.5 h-3.5 text-indigo-400" />
              <span>In-Flow Audio Dialogue Stream</span>
            </span>
            {isPlayingAudio && (
              <span className="text-[11px] text-cyan-400 flex items-center space-x-1.5 animate-pulse">
                <Volume2 className="w-3.5 h-3.5" />
                <span>VoiceNexus is speaking...</span>
              </span>
            )}
          </div>

          {/* Transcript Scroll Area */}
          <div className="flex-1 overflow-y-auto space-y-3.5 pr-2">
            {turns.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs">
                <Phone className="w-8 h-8 mb-2 text-slate-600 stroke-[1.5]" />
                <p>Click <strong className="text-emerald-400">Dial Care Line</strong> to simulate an inbound customer call.</p>
              </div>
            ) : (
              turns.map((turn, idx) => (
                <div
                  key={idx}
                  className={`flex ${turn.speaker === 'caller' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[82%] rounded-2xl px-4 py-3 text-xs leading-relaxed shadow-sm ${
                      turn.speaker === 'caller'
                        ? 'bg-indigo-600 text-white rounded-br-none'
                        : turn.speaker === 'ai'
                        ? 'bg-slate-800/90 text-slate-100 border border-slate-700/60 rounded-bl-none'
                        : 'bg-amber-950/60 text-amber-200 border border-amber-800'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1 opacity-75 text-[10px]">
                      <span className="font-semibold">
                        {turn.speaker === 'caller' ? 'Caller (Customer)' : 'VoiceNexus AI IVR'}
                      </span>
                      {turn.latency && (
                        <span>{turn.latency.total_turn_ms} ms</span>
                      )}
                    </div>
                    <div className="text-sm">{turn.text}</div>
                  </div>
                </div>
              ))
            )}
            <div ref={chatBottomRef} />
          </div>

          {/* Custom Caller Speech Input with Microphone */}
          <div className="mt-3 pt-3 border-t border-slate-800 flex space-x-2">
            <button
              type="button"
              disabled={callState !== 'IN_CALL'}
              onClick={toggleListening}
              className={`px-3 py-2 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all ${
                isListening
                  ? 'bg-rose-600 text-white animate-pulse'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              } disabled:opacity-40 cursor-pointer`}
              title="Speak into microphone via Web Speech API"
            >
              <Mic className="w-3.5 h-3.5" />
              <span>{isListening ? 'Listening...' : 'Voice Mic'}</span>
            </button>

            <input
              type="text"
              disabled={callState !== 'IN_CALL'}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendUtterance(inputText)}
              placeholder={callState === 'IN_CALL' ? "Speak or type as caller (e.g., 'How much is my bill?')..." : "Start call to speak"}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
            />
            <button
              disabled={callState !== 'IN_CALL' || !inputText.trim()}
              onClick={() => sendUtterance(inputText)}
              className="px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Send</span>
            </button>
          </div>
        </div>

        {/* Quick PRD Evaluation Scenarios (One-Click Testing) */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold text-slate-300 mb-2 flex items-center justify-between">
            <span>One-Click Test Utterances (PRD Scenarios):</span>
            <span className="text-[10px] text-slate-500">Fast Scenario Replay</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {PRESET_UTTERANCES.map((u, i) => (
              <button
                key={i}
                disabled={callState !== 'IN_CALL'}
                onClick={() => sendUtterance(u.text)}
                className="text-left p-2 rounded-xl bg-slate-850 hover:bg-indigo-950/60 border border-slate-800 hover:border-indigo-700/60 text-slate-300 hover:text-white text-[11px] transition-all disabled:opacity-40 disabled:hover:bg-slate-850 disabled:hover:border-slate-800 cursor-pointer"
              >
                <div className="font-semibold text-indigo-400">{u.label}</div>
                <div className="text-[10px] text-slate-400 truncate mt-0.5">"{u.text}"</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
