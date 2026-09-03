import React, { useState, useEffect } from 'react';
import { 
  BarChart3, TrendingUp, Clock, PhoneForwarded, 
  ShieldCheck, RefreshCw, Eye, X
} from 'lucide-react';
import type { TelemetrySummary, CallRecord } from '../types';

export const OpsDashboard: React.FC = () => {
  const [summary, setSummary] = useState<TelemetrySummary | null>(null);
  const [cdrs, setCdrs] = useState<CallRecord[]>([]);
  const [selectedCdr, setSelectedCdr] = useState<CallRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchMetrics = () => {
    setLoading(true);
    Promise.all([
      fetch('/api/telemetry/summary').then(r => r.json()),
      fetch('/api/telemetry/cdrs').then(r => r.json())
    ])
      .then(([sumData, cdrData]) => {
        setSummary(sumData);
        setCdrs(cdrData);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Top Controls Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-indigo-400" />
            <span>Care-Ops Telemetry & Performance (VN-6)</span>
          </h2>
          <p className="text-xs text-slate-400">
            Real-time containment, handle time, and intent distribution metrics for contact center operations.
          </p>
        </div>
        <button
          onClick={fetchMetrics}
          disabled={loading}
          className="py-1.5 px-3 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 text-xs flex items-center space-x-1.5 transition-all cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Feed</span>
        </button>
      </div>

      {/* KPI Cards Grid */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Containment Rate */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>Containment Rate</span>
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-black text-emerald-400">
              {summary.containment_rate_pct}%
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              {summary.contained_calls} of {summary.total_calls} calls resolved in-flow
            </div>
          </div>

          {/* Transfer Rate */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>Agent Transfer Rate</span>
              <PhoneForwarded className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-black text-amber-400">
              {summary.transfer_rate_pct}%
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              {summary.escalated_calls} calls sent to agent queue
            </div>
          </div>

          {/* Automated AHT */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>AHT (Automated)</span>
              <Clock className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-black text-indigo-300">
              {summary.avg_handle_time_automated_sec}s
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Average handle time for contained calls
            </div>
          </div>

          {/* Escalated AHT in IVR */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>AHT (To Escalation)</span>
              <Clock className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-2xl font-black text-slate-200">
              {summary.avg_handle_time_escalated_sec}s
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Time to live transfer handoff
            </div>
          </div>

          {/* Median Response Latency */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>Median Turn Latency</span>
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-black text-cyan-300">
              {summary.median_latency_ms} ms
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              SLO: ≤1000ms response to caller
            </div>
          </div>
        </div>
      )}

      {/* Analytics Breakdown Grid: Intent Distribution & Escalation Reasons */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Intent Distribution */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">
              Care Intent Volume Distribution
            </h3>
            <div className="space-y-3">
              {Object.entries(summary.intent_distribution).map(([intent, count]) => {
                const pct = summary.total_calls > 0 ? (count / summary.total_calls) * 100 : 0;
                return (
                  <div key={intent} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-200">{intent}</span>
                      <span className="text-slate-400">{count} calls ({pct.toFixed(0)}%)</span>
                    </div>
                    <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-850">
                      <div 
                        className="bg-indigo-500 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${Math.max(5, pct)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Escalation Drivers */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">
              Agent Escalation Root Causes
            </h3>
            <div className="space-y-3">
              {Object.keys(summary.escalation_reasons).length === 0 ? (
                <div className="text-slate-500 text-xs py-6 text-center">No escalations recorded.</div>
              ) : (
                Object.entries(summary.escalation_reasons).map(([reason, count]) => {
                  const pct = summary.escalated_calls > 0 ? (count / summary.escalated_calls) * 100 : 0;
                  return (
                    <div key={reason} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-medium text-amber-300">{reason}</span>
                        <span className="text-slate-400">{count} transfers ({pct.toFixed(0)}%)</span>
                      </div>
                      <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-850">
                        <div 
                          className="bg-amber-500 h-full rounded-full transition-all duration-500" 
                          style={{ width: `${Math.max(5, pct)}%` }}
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}

      {/* Call Detail Records (CDR) Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Recent Call Detail Records (CDR)
          </span>
          <span className="text-[11px] text-slate-500">Showing last {cdrs.length} completed sessions</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="text-slate-400 border-b border-slate-800/80 pb-2">
                <th className="py-2.5 font-semibold">Session ID</th>
                <th className="py-2.5 font-semibold">Subscriber</th>
                <th className="py-2.5 font-semibold">Intent</th>
                <th className="py-2.5 font-semibold">Outcome</th>
                <th className="py-2.5 font-semibold">Duration</th>
                <th className="py-2.5 font-semibold">Latency</th>
                <th className="py-2.5 font-semibold text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-850">
              {cdrs.map((cdr) => (
                <tr key={cdr.session_id} className="hover:bg-slate-850/50 transition-colors">
                  <td className="py-3 font-mono text-slate-400 text-[11px]">{cdr.session_id}</td>
                  <td className="py-3">
                    <div className="font-medium text-slate-200">{cdr.customer_name}</div>
                    <div className="text-[10px] text-slate-500">{cdr.ani}</div>
                  </td>
                  <td className="py-3 text-slate-300">{cdr.intent}</td>
                  <td className="py-3">
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                      cdr.final_state === 'RESOLVED_CONTAINED'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : 'bg-amber-950 text-amber-400 border border-amber-800'
                    }`}>
                      {cdr.final_state === 'RESOLVED_CONTAINED' ? 'Contained' : 'Escalated'}
                    </span>
                  </td>
                  <td className="py-3 text-slate-400">{cdr.duration_sec}s</td>
                  <td className="py-3 text-slate-400">{cdr.avg_latency_ms} ms</td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => setSelectedCdr(cdr)}
                      className="p-1 rounded-lg hover:bg-slate-800 text-indigo-400 hover:text-indigo-300 transition-colors cursor-pointer"
                      title="Inspect Full Call Transcript"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* CDR Modal Inspector */}
      {selectedCdr && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="font-bold text-slate-100 text-sm">
                  Call Detail Record: {selectedCdr.session_id}
                </h3>
                <div className="text-xs text-slate-400">
                  {selectedCdr.customer_name} ({selectedCdr.ani}) · Duration: {selectedCdr.duration_sec}s
                </div>
              </div>
              <button
                onClick={() => setSelectedCdr(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div>
                <span className="text-slate-500">Outcome: </span>
                <span className="font-semibold text-slate-200">{selectedCdr.final_state}</span>
              </div>
              <div>
                <span className="text-slate-500">Primary Intent: </span>
                <span className="font-semibold text-slate-200">{selectedCdr.intent}</span>
              </div>
              {selectedCdr.escalation_reason && (
                <div className="col-span-2">
                  <span className="text-slate-500">Escalation Reason: </span>
                  <span className="font-semibold text-amber-400">{selectedCdr.escalation_reason}</span>
                </div>
              )}
            </div>

            {/* Transcript */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-300">Recorded Dialogue Transcript:</span>
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 max-h-60 overflow-y-auto space-y-2 text-xs">
                {selectedCdr.transcript.length === 0 ? (
                  <div className="text-slate-500 text-center py-4">No dialogue turns recorded.</div>
                ) : (
                  selectedCdr.transcript.map((t, i) => (
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

            <div className="text-right pt-2 border-t border-slate-800">
              <button
                onClick={() => setSelectedCdr(null)}
                className="py-1.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition-all cursor-pointer"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
