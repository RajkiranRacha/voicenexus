import React, { useState, useEffect, useRef } from 'react';
import {
  Phone, PhoneOff, Mic, MicOff, Volume2, Radio,
  Send, ShieldCheck, Zap, Globe, Star,
  Copy, Check, Users, ChevronDown, ChevronUp,
  Headphones, UserCheck, ExternalLink
} from 'lucide-react';
import { apiGet, apiPost } from '../api/client';
import { useCallWebSocket } from '../hooks/useCallWebSocket';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { TranscriptList } from './shared/TranscriptList';
import { PRESET_CALLERS, PRESET_UTTERANCES } from '../data/presets';
import type { Subscriber } from './SubscriberManager';

export const TEST_ACCOUNTS = [
  { name: "Jordan Rivera", account: "1001", phone: "+15550192834", zip: "94107", email: "jordan.rivera@example.com", balance: "$142.50", scenario: "Billing & payment arrangement" },
  { name: "Elena Vance", account: "1002", phone: "+15550148821", zip: "98101", email: "elena.vance@example.com", balance: "$0.00", scenario: "Active outage in Seattle & offline router" },
  { name: "Marcus Brody", account: "1003", phone: "+15550173399", zip: "78701", email: "marcus.brody@example.com", balance: "$220.00", scenario: "Degraded Wi-Fi & remote reboot" },
  { name: "Sam Taylor", account: "1004", phone: "+15550101001", zip: "90210", email: "sam.taylor@example.com", balance: "$45.00", scenario: "Pure numeric account lookup (1004)" },
  { name: "Alex Morgan", account: "1005", phone: "+15550102002", zip: "10001", email: "alex.morgan@example.com", balance: "$0.00", scenario: "Zero balance & plan upgrade" }
];

const CsatPrompt: React.FC<{ sessionId: string }> = ({ sessionId }) => {
  const [rating, setRating] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const submit = (value: number) => {
    setRating(value);
    apiPost('/api/telemetry/csat', { session_id: sessionId, rating: value })
      .then(() => setSubmitted(true))
      .catch(() => {});
  };

  if (submitted) {
    return (
      <div className="text-xs text-emerald-300 flex items-center space-x-1.5">
        <Star className="w-3.5 h-3.5 text-amber-300 fill-amber-300" />
        <span>Thanks for your feedback!</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 text-xs">
      <span className="text-slate-400">Rate this call:</span>
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          onClick={() => submit(n)}
          className="p-0.5 cursor-pointer"
          title={`${n} star${n > 1 ? 's' : ''}`}
        >
          <Star className={`w-4 h-4 ${rating != null && n <= rating ? 'text-amber-300 fill-amber-300' : 'text-slate-600'}`} />
        </button>
      ))}
    </div>
  );
};

export const PhoneSimulator: React.FC = () => {
  const [liveSubscribers, setLiveSubscribers] = useState<Subscriber[]>([]);
  const [selectedAni, setSelectedAni] = useState<string>(PRESET_CALLERS[0].ani);
  const [customAni, setCustomAni] = useState<string>("");
  const [inputText, setInputText] = useState<string>('');
  const [autoPlayAudio, setAutoPlayAudio] = useState<boolean>(true);
  const [showCheatSheet, setShowCheatSheet] = useState<boolean>(true);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Subscriber[]>('/api/admin/subscribers')
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setLiveSubscribers(data);
        }
      })
      .catch((err) => console.error('Failed to load subscribers in PhoneSimulator:', err));
  }, []);

  const callers = liveSubscribers.length > 0
    ? [
        ...liveSubscribers.map((s) => ({
          name: s.customer_name,
          ani: s.phone_number,
          scenario: `Acc: ${s.account_number} | Zip: ${s.zip_code} | $${Number(s.current_balance).toFixed(2)} balance | ${s.router_status}${s.has_active_outage ? ' (Outage)' : ''}`
        })),
        {
          name: "Unregistered Caller (Unknown ANI)",
          ani: "+15559990000",
          scenario: "Unknown caller - test finding account by Name, Email, Phone, Zip, or Acc #"
        }
      ]
    : PRESET_CALLERS;

  const cheatSheetAccounts = liveSubscribers.length > 0
    ? liveSubscribers.map((s) => ({
        name: s.customer_name,
        account: s.account_number,
        phone: s.phone_number,
        zip: s.zip_code,
        email: s.email || `${s.customer_name.toLowerCase().replace(/\s+/g, '.')}@example.com`,
        balance: `$${Number(s.current_balance).toFixed(2)}`,
        scenario: `${s.plan_name} • Router: ${s.router_status}${s.has_active_outage ? ' • Outage' : ''}`
      }))
    : TEST_ACCOUNTS;

  const copyOrInsert = (value: string, key: string) => {
    navigator.clipboard.writeText(value);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
    setInputText(value);
  };

  const agentAudioRef = useRef<HTMLAudioElement | null>(null);
  const chatBottomRef = useRef<HTMLDivElement | null>(null);

  const activeAni = customAni.trim() || selectedAni;

  const call = useCallWebSocket(agentAudioRef);
  const sendUtterance = (text: string) => call.sendUtterance(text, setInputText);
  // Final speech result is sent immediately instead of waiting in the input
  // box for a manual Send click, so a voice turn behaves like an actual
  // spoken conversation: speak, it understands, it responds.
  const speech = useSpeechRecognition(call.callLanguage, setInputText, sendUtterance);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [call.turns]);

  const startCall = () => call.startCall(activeAni, autoPlayAudio);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-7xl mx-auto">
      {/* Audio element for playing live agent voice */}
      <audio ref={agentAudioRef} autoPlay playsInline />

      {/* Left Column: Phone Console & Audio Telemetry */}
      <div className="lg:col-span-4 space-y-4">
        {/* Softphone Hardware Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                call.connectedAgent ? 'bg-emerald-400 animate-ping' :
                call.callState === 'IN_CALL' ? 'bg-emerald-500 animate-pulse' :
                call.callState === 'ESCALATED' ? 'bg-amber-500' :
                call.callState === 'CONNECTING' ? 'bg-blue-500 animate-pulse' : 'bg-slate-600'
              }`} />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                {call.connectedAgent ? `Live with ${call.connectedAgent.name}` :
                 call.callState === 'IN_CALL' ? 'Active Call In-Flow' :
                 call.callState === 'ESCALATED' ? 'Escalated to Agent' :
                 call.callState === 'CONNECTING' ? 'Connecting to SBC...' : 'Line Idle'}
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
            <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
              {callers.map((c) => (
                <button
                  key={c.ani}
                  disabled={call.callState === 'IN_CALL' || call.callState === 'CONNECTING'}
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

            <div className="pt-1.5">
              <input
                type="tel"
                disabled={call.callState === 'IN_CALL' || call.callState === 'CONNECTING'}
                value={customAni}
                onChange={(e) => setCustomAni(e.target.value)}
                placeholder="Or dial a custom ANI, e.g. +15551234567"
                title="Any number not on file simulates an unregistered caller who must verify by account number or ZIP code."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
              />
            </div>
          </div>

          {/* Active Call Controls */}
          <div className="mt-5 pt-4 border-t border-slate-800">
            {call.callState === 'IDLE' || call.callState === 'ENDED' ? (
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
                  onClick={call.endCall}
                  className="w-full py-2.5 px-4 bg-rose-600 hover:bg-rose-500 text-white font-semibold rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-rose-950/40 transition-all cursor-pointer"
                >
                  <PhoneOff className="w-4 h-4" />
                  <span>Disconnect Call</span>
                </button>

                {call.connectedAgent ? (
                  <button
                    type="button"
                    onClick={call.toggleCallerMute}
                    className={`w-full py-2 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center space-x-2 transition-all cursor-pointer ${
                      call.isCallerMuted
                        ? 'border-rose-500/80 bg-rose-950/50 text-rose-200'
                        : 'border-emerald-800 bg-emerald-950/40 text-emerald-300'
                    }`}
                  >
                    {call.isCallerMuted ? <MicOff className="w-3.5 h-3.5 text-rose-400" /> : <Mic className="w-3.5 h-3.5 text-emerald-400" />}
                    <span>{call.isCallerMuted ? 'Caller Mic Muted (Click to Unmute)' : 'Caller Mic Live (Click to Mute)'}</span>
                  </button>
                ) : (
                  /* Barge-in Interruption Button */
                  <button
                    onClick={call.handleBargeIn}
                    disabled={!call.isPlayingAudio}
                    className={`w-full py-2 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center space-x-2 transition-all ${
                      call.isPlayingAudio
                        ? 'border-amber-500/80 bg-amber-950/50 text-amber-200 animate-pulse cursor-pointer'
                        : 'border-slate-800 bg-slate-900/50 text-slate-500 cursor-not-allowed'
                    }`}
                  >
                    <MicOff className="w-3.5 h-3.5" />
                    <span>{call.isPlayingAudio ? 'Barge-In (Interrupt AI Speech)' : 'AI Not Speaking'}</span>
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
                  disabled={call.callState !== 'IN_CALL' || call.awaitingResponse}
                  onClick={() => call.sendDtmf(digit)}
                  className="py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 active:bg-indigo-600 text-slate-200 font-mono text-sm font-semibold disabled:opacity-40 transition-all cursor-pointer"
                >
                  {digit}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Real-Time Sub-Second Latency Telemetry Badge */}
        {call.latestLatency && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <span>Turn Latency Budget</span>
              </span>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                call.latestLatency.total_turn_ms <= 1000
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                  : 'bg-amber-950 text-amber-300 border border-amber-800'
              }`}>
                {call.latestLatency.total_turn_ms} ms (SLO: ≤1000ms)
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center text-[11px]">
              <div className="bg-slate-950 p-2 rounded-lg border border-slate-800/60">
                <div className="text-slate-500">STT ASR</div>
                <div className="font-semibold text-slate-300">{call.latestLatency.stt_ms} ms</div>
              </div>
              <div className="bg-slate-950 p-2 rounded-lg border border-slate-800/60">
                <div className="text-slate-500">NLU / FSM</div>
                <div className="font-semibold text-indigo-300">{call.latestLatency.nlu_ms} ms</div>
              </div>
              <div className="bg-slate-950 p-2 rounded-lg border border-slate-800/60">
                <div className="text-slate-500">Neural TTS</div>
                <div className="font-semibold text-cyan-300">{call.latestLatency.tts_ms} ms</div>
              </div>
            </div>
          </div>
        )}

        {/* Post-Call CSAT */}
        {call.callState === 'ENDED' && call.sessionId && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <CsatPrompt sessionId={call.sessionId} />
          </div>
        )}
      </div>

      {/* Right Column: Live Conversation Transcript & Interactive Utterance Prompts */}
      <div className="lg:col-span-8 flex flex-col space-y-4">
        {/* Caller Context Banner */}
        {call.callerProfile ? (
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-3.5 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center font-bold">
                {call.callerProfile.customer_name[0]}
              </div>
              <div>
                <div className="font-semibold text-slate-200 flex items-center space-x-1.5">
                  <span>{call.callerProfile.customer_name}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border flex items-center space-x-1 ${
                    call.callerProfile.auth_status === 'OTP_VERIFIED' ? 'bg-purple-950 text-purple-300 border-purple-800' :
                    call.callerProfile.auth_status === 'KBA_VERIFIED' ? 'bg-emerald-950 text-emerald-300 border-emerald-800' :
                    'bg-indigo-950 text-indigo-300 border-indigo-800'
                  }`}>
                    <ShieldCheck className="w-2.5 h-2.5" />
                    <span>{call.callerProfile.auth_status}</span>
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 flex items-center space-x-1">
                    <Globe className="w-2.5 h-2.5 text-cyan-400" />
                    <span>{call.callLanguage}</span>
                  </span>
                </div>
                <div className="text-slate-400 text-[11px]">
                  Acc: {call.callerProfile.account_number} · {call.callerProfile.plan_name} · Bal: ${call.callerProfile.current_balance.toFixed(2)}
                </div>
              </div>
            </div>
            <div className="text-right text-[11px] text-slate-400 hidden sm:block">
              <div>Zip: {call.callerProfile.zip_code}</div>
              <div className={call.callerProfile.has_active_outage ? 'text-rose-400 font-semibold' : 'text-slate-400'}>
                {call.callerProfile.has_active_outage ? '⚠ Area Outage Active' : 'Network Nominal'}
              </div>
            </div>
          </div>
        ) : call.callState === 'IN_CALL' ? (
          <div className="bg-amber-950/40 border border-amber-900/60 rounded-2xl p-3.5 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2 text-amber-300">
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              <span>
                <strong>Unregistered ANI ({activeAni}):</strong> Awaiting Verification (say Name, Account #, Phone, Email, or Zip Code).
              </span>
            </div>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 flex items-center space-x-1">
              <Globe className="w-2.5 h-2.5 text-cyan-400" />
              <span>{call.callLanguage}</span>
            </span>
          </div>
        ) : null}

        {/* Escalated to Live Agent Queue Banner */}
        {call.callState === 'ESCALATED' && !call.connectedAgent && (
          <div className="bg-indigo-950/70 border border-indigo-700/80 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3 text-xs shadow-xl shadow-indigo-950/40 animate-pulse">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-indigo-600/30 text-indigo-400 flex items-center justify-center font-bold">
                <Headphones className="w-5 h-5 animate-bounce" />
              </div>
              <div>
                <div className="font-bold text-indigo-200 flex items-center space-x-2">
                  <span>Call Escalated to Live Care Specialist</span>
                  <span className="bg-indigo-800/80 text-indigo-100 text-[10px] px-2 py-0.5 rounded-full font-semibold">
                    In Priority Queue
                  </span>
                </div>
                <div className="text-[11px] text-indigo-300/80 mt-0.5">
                  AI handoff complete. Handoff context & verified records sent to Tier 2 specialist (Sarah J.).
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => window.open('/agent', '_blank')}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer"
                title="Open Agent Workspace in a separate tab to accept call"
              >
                <ExternalLink className="w-3.5 h-3.5 text-indigo-400" />
                <span>Open Agent Tab</span>
              </button>

              <button
                type="button"
                onClick={call.acceptAsAgent}
                className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold flex items-center space-x-1.5 shadow-md shadow-emerald-950/50 transition-all cursor-pointer"
                title="Answer call as care specialist immediately"
              >
                <UserCheck className="w-3.5 h-3.5 text-white" />
                <span>Answer Call as Agent</span>
              </button>
            </div>
          </div>
        )}

        {/* Connected to Live Agent Banner */}
        {call.connectedAgent && (
          <div className="bg-emerald-950/60 border border-emerald-800/90 rounded-2xl p-3.5 flex flex-wrap items-center justify-between gap-2 text-xs shadow-lg shadow-emerald-950/30">
            <div className="flex items-center space-x-2.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              <div>
                <div className="font-bold text-emerald-300 flex items-center space-x-1.5">
                  <span>Connected to Live Care Specialist</span>
                  <span className="text-white bg-emerald-800/80 px-2 py-0.5 rounded-md text-[11px]">
                    {call.connectedAgent.name}
                  </span>
                </div>
                <div className="text-[11px] text-emerald-400/80 flex items-center space-x-2">
                  <span>Two-way voice connection active · You can speak directly to the specialist</span>
                  <span className={`px-1.5 py-0.2 rounded text-[10px] border ${
                    call.webrtcConnectionState === 'connected' ? 'bg-emerald-900/60 text-emerald-300 border-emerald-700' :
                    call.webrtcConnectionState === 'connecting' ? 'bg-amber-900/60 text-amber-300 border-amber-700 animate-pulse' :
                    call.webrtcConnectionState === 'failed' ? 'bg-rose-900/60 text-rose-300 border-rose-700' :
                    'bg-slate-800 text-slate-400 border-slate-700'
                  }`}>
                    {call.webrtcConnectionState === 'connected' ? 'P2P Audio: Live' :
                     call.webrtcConnectionState === 'connecting' ? 'Connecting Audio...' :
                     call.webrtcConnectionState === 'failed' ? 'Audio Traversal Failed' : 'Audio: Standby'}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {call.isAutoplayBlocked && (
                <button
                  type="button"
                  onClick={call.unlockAudio}
                  className="px-2.5 py-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg text-[11px] flex items-center space-x-1 animate-bounce transition-all cursor-pointer shadow-md shadow-amber-950/40"
                  title="Click to allow audio playback from agent"
                >
                  <Volume2 className="w-3 h-3" />
                  <span>Tap to Hear Agent</span>
                </button>
              )}

              <span className={`px-2.5 py-1 rounded-lg border text-[11px] font-semibold flex items-center space-x-1.5 ${
                call.isCallerMicActive
                  ? (call.isCallerMuted ? 'bg-amber-950 text-amber-300 border-amber-800' : 'bg-emerald-900/80 text-emerald-200 border-emerald-700')
                  : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}>
                {call.isCallerMuted ? <MicOff className="w-3 h-3 text-amber-400" /> : <Mic className="w-3 h-3 text-emerald-400 animate-pulse" />}
                <span>{call.isCallerMuted ? 'Mic: Muted' : 'Mic: Live (Active)'}</span>
              </span>

              <button
                type="button"
                onClick={call.toggleCallerMute}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-[11px] font-medium transition-all cursor-pointer"
              >
                {call.isCallerMuted ? 'Unmute' : 'Mute'}
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
            {call.isPlayingAudio && (
              <span className="text-[11px] text-cyan-400 flex items-center space-x-1.5 animate-pulse">
                <Volume2 className="w-3.5 h-3.5" />
                <span>VoiceNexus is speaking...</span>
              </span>
            )}
            {call.awaitingResponse && !call.isPlayingAudio && (
              <span className="text-[11px] text-indigo-300 flex items-center space-x-1.5 animate-pulse">
                <Radio className="w-3.5 h-3.5" />
                <span>VoiceNexus is thinking...</span>
              </span>
            )}
            {call.audioDegraded && (
              <span
                className="text-[11px] text-amber-400 flex items-center space-x-1.5"
                title="Neural voice synthesis is temporarily unavailable. Continuing in degraded text/DTMF mode per reliability SLO."
              >
                <MicOff className="w-3.5 h-3.5" />
                <span>Degraded mode: voice audio unavailable, text/DTMF still active</span>
              </span>
            )}
          </div>

          {/* Transcript Scroll Area */}
          <div className="flex-1 overflow-y-auto space-y-3.5 pr-2">
            {call.turns.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs">
                <Phone className="w-8 h-8 mb-2 text-slate-600 stroke-[1.5]" />
                <p>Click <strong className="text-emerald-400">Dial Care Line</strong> to simulate an inbound customer call.</p>
              </div>
            ) : (
              <TranscriptList turns={call.turns} variant="bubble-detailed" />
            )}
            <div ref={chatBottomRef} />
          </div>

          {/* Custom Caller Speech Input with Microphone */}
          <div className="mt-3 pt-3 border-t border-slate-800 flex flex-col space-y-1.5">
            {speech.isListening && (
              <div className="text-[11px] text-indigo-300">Listening — I'll respond as soon as you finish speaking.</div>
            )}
            {speech.error && (
              <div className="text-[11px] text-rose-400">{speech.error}</div>
            )}
            <div className="flex space-x-2">
              <button
                type="button"
                disabled={call.callState !== 'IN_CALL'}
                onClick={speech.toggleListening}
                className={`px-3 py-2 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all ${
                  speech.isListening
                    ? 'bg-rose-600 text-white animate-pulse'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                } disabled:opacity-40 cursor-pointer`}
                title="Speak into microphone via Web Speech API"
              >
                <Mic className="w-3.5 h-3.5" />
                <span>{speech.isListening ? 'Listening...' : 'Voice Mic'}</span>
              </button>

              <input
                type="text"
                disabled={call.callState !== 'IN_CALL' || call.awaitingResponse}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendUtterance(inputText)}
                placeholder={call.callState === 'IN_CALL' ? (call.awaitingResponse ? "Waiting for VoiceNexus to respond..." : "Speak or type as caller (e.g., 'How much is my bill?')...") : call.callState === 'ESCALATED' ? "Call transferred: In queue for live care specialist (click Answer above)..." : "Start call to speak"}
                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
              />
              <button
                disabled={call.callState !== 'IN_CALL' || call.awaitingResponse || !inputText.trim()}
                onClick={() => sendUtterance(inputText)}
                className="px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Send</span>
              </button>
            </div>
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
                disabled={call.callState !== 'IN_CALL' || call.awaitingResponse}
                onClick={(e) => { sendUtterance(u.text); e.currentTarget.blur(); }}
                className="text-left p-2 rounded-xl bg-slate-850 hover:bg-indigo-950/60 border border-slate-800 hover:border-indigo-700/60 text-slate-300 hover:text-white text-[11px] transition-all disabled:opacity-40 disabled:hover:bg-slate-850 disabled:hover:border-slate-800 cursor-pointer"
              >
                <div className="font-semibold text-indigo-400">{u.label}</div>
                <div className="text-[10px] text-slate-400 truncate mt-0.5">"{u.text}"</div>
              </button>
            ))}
          </div>
        </div>

        {/* Test Accounts Cheat Sheet (Clear Data for Testing) */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-indigo-300">
              <Users className="w-4 h-4 text-indigo-400" />
              <span>Verified Test Data Cheat Sheet (Click to insert & copy)</span>
            </div>
            <button
              type="button"
              onClick={() => setShowCheatSheet(!showCheatSheet)}
              className="text-xs text-slate-400 hover:text-slate-200 flex items-center space-x-1 cursor-pointer"
            >
              <span>{showCheatSheet ? 'Hide' : 'Show'}</span>
              {showCheatSheet ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>

          <p className="text-[11px] text-slate-400 leading-relaxed">
            The AI can locate any subscriber using their <strong>Full Name</strong>, <strong>Account ID</strong>, <strong>Phone Number</strong>, <strong>Billing ZIP</strong>, or <strong>Email</strong>. Click any cell to copy and fill the input box:
          </p>

          {showCheatSheet && (
            <div className="space-y-2 pt-1 max-h-96 overflow-y-auto pr-1">
              {cheatSheetAccounts.map((acc) => (
                <div
                  key={acc.account}
                  className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-3 text-xs space-y-2 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={() => copyOrInsert(acc.name, `name-${acc.account}`)}
                        className="font-semibold text-slate-100 hover:text-indigo-300 text-left flex items-center space-x-1.5 cursor-pointer"
                        title="Click to insert name into input"
                      >
                        <span>{acc.name}</span>
                        {copiedKey === `name-${acc.account}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-2.5 h-2.5 text-slate-500" />}
                      </button>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                        {acc.balance}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-400 italic">{acc.scenario}</span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 text-[11px]">
                    {/* Account ID */}
                    <button
                      type="button"
                      onClick={() => copyOrInsert(acc.account, `acc-${acc.account}`)}
                      className="text-left bg-slate-900/90 hover:bg-indigo-950/50 p-1.5 rounded-lg border border-slate-800 hover:border-indigo-700/60 transition-colors cursor-pointer group"
                      title="Click to insert account ID"
                    >
                      <div className="text-[9px] uppercase text-slate-500 font-medium">Account ID</div>
                      <div className="font-mono text-indigo-300 font-semibold truncate flex items-center justify-between">
                        <span>{acc.account}</span>
                        {copiedKey === `acc-${acc.account}` ? <Check className="w-2.5 h-2.5 text-emerald-400 shrink-0" /> : <Copy className="w-2.5 h-2.5 text-slate-600 group-hover:text-slate-400 shrink-0" />}
                      </div>
                    </button>

                    {/* Phone */}
                    <button
                      type="button"
                      onClick={() => copyOrInsert(acc.phone, `phone-${acc.account}`)}
                      className="text-left bg-slate-900/90 hover:bg-indigo-950/50 p-1.5 rounded-lg border border-slate-800 hover:border-indigo-700/60 transition-colors cursor-pointer group"
                      title="Click to insert phone number"
                    >
                      <div className="text-[9px] uppercase text-slate-500 font-medium">Phone (ANI)</div>
                      <div className="font-mono text-slate-200 truncate flex items-center justify-between">
                        <span>{acc.phone}</span>
                        {copiedKey === `phone-${acc.account}` ? <Check className="w-2.5 h-2.5 text-emerald-400 shrink-0" /> : <Copy className="w-2.5 h-2.5 text-slate-600 group-hover:text-slate-400 shrink-0" />}
                      </div>
                    </button>

                    {/* Zip */}
                    <button
                      type="button"
                      onClick={() => copyOrInsert(acc.zip, `zip-${acc.account}`)}
                      className="text-left bg-slate-900/90 hover:bg-indigo-950/50 p-1.5 rounded-lg border border-slate-800 hover:border-indigo-700/60 transition-colors cursor-pointer group"
                      title="Click to insert ZIP code"
                    >
                      <div className="text-[9px] uppercase text-slate-500 font-medium">Billing Zip</div>
                      <div className="font-mono text-cyan-300 font-semibold truncate flex items-center justify-between">
                        <span>{acc.zip}</span>
                        {copiedKey === `zip-${acc.account}` ? <Check className="w-2.5 h-2.5 text-emerald-400 shrink-0" /> : <Copy className="w-2.5 h-2.5 text-slate-600 group-hover:text-slate-400 shrink-0" />}
                      </div>
                    </button>

                    {/* Email */}
                    <button
                      type="button"
                      onClick={() => copyOrInsert(acc.email, `email-${acc.account}`)}
                      className="text-left bg-slate-900/90 hover:bg-indigo-950/50 p-1.5 rounded-lg border border-slate-800 hover:border-indigo-700/60 transition-colors cursor-pointer group"
                      title="Click to insert email"
                    >
                      <div className="text-[9px] uppercase text-slate-500 font-medium">Email</div>
                      <div className="text-slate-300 truncate flex items-center justify-between">
                        <span className="truncate">{acc.email}</span>
                        {copiedKey === `email-${acc.account}` ? <Check className="w-2.5 h-2.5 text-emerald-400 shrink-0" /> : <Copy className="w-2.5 h-2.5 text-slate-600 group-hover:text-slate-400 shrink-0" />}
                      </div>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
