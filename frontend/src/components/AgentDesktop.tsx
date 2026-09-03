import React, { useState, useEffect } from 'react';
import { 
  Headphones, ShieldCheck, UserCheck, 
  MessageSquare, CheckCircle2, Sparkles, Inbox
} from 'lucide-react';
import type { EscalationPayload } from '../types';

export const AgentDesktop: React.FC = () => {
  const [escalations, setEscalations] = useState<EscalationPayload[]>([]);
  const [selectedEscalation, setSelectedEscalation] = useState<EscalationPayload | null>(null);
  const [acceptedCalls, setAcceptedCalls] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);

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

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'NEW_ESCALATION') {
        const payload: EscalationPayload = data.payload;
        setEscalations(prev => {
          const exists = prev.some(e => e.session_id === payload.session_id);
          if (exists) return prev;
          return [payload, ...prev];
        });
        setSelectedEscalation(prev => prev || payload);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  const acceptCall = (sessionId: string) => {
    fetch('/api/agent/accept', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, agent_id: 'agent-sarah-j' })
    })
      .then(res => res.json())
      .then(() => {
        setAcceptedCalls(prev => [...prev, sessionId]);
      });
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center justify-between shadow-xl">
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
              Zero-repetition customer handoff with verified identity and AI-prepared care context.
            </p>
          </div>
        </div>
        <div className="text-right text-xs">
          <div className="text-slate-400">Agent: <span className="font-semibold text-slate-200">Sarah Jenkins</span></div>
          <div className="text-[11px] text-indigo-400 font-medium">Queue: CARE_BILLING_TIER1</div>
        </div>
      </div>

      {/* Main Workspace Layout */}
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
                    {!acceptedCalls.includes(selectedEscalation.session_id) ? (
                      <button
                        onClick={() => acceptCall(selectedEscalation.session_id)}
                        className="py-2 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl text-xs flex items-center space-x-2 shadow-lg shadow-emerald-950/40 transition-all cursor-pointer"
                      >
                        <UserCheck className="w-4 h-4" />
                        <span>Accept & Answer Call</span>
                      </button>
                    ) : (
                      <div className="text-xs font-semibold text-emerald-400 flex items-center space-x-1.5 py-1.5 px-3 bg-emerald-950/60 border border-emerald-800 rounded-xl">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Call Active with Agent</span>
                      </div>
                    )}
                  </div>
                </div>

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

                {/* Live Transcript Overlay (VN-10) */}
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                    <MessageSquare className="w-3.5 h-3.5 text-indigo-400" />
                    <span>IVR Transcript & Pre-Handoff Dialogue</span>
                  </div>
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 max-h-[260px] overflow-y-auto space-y-2.5 text-xs">
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
    </div>
  );
};
