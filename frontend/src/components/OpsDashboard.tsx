import React, { useState } from 'react';
import {
  BarChart3, TrendingUp, Clock, PhoneForwarded,
  ShieldCheck, RefreshCw, Eye, X, PhoneOff, Star, Download
} from 'lucide-react';
import type { CallRecord } from '../types';
import { useTelemetryPolling } from '../hooks/useTelemetryPolling';
import { DistributionBarList } from './shared/DistributionBarList';
import { TranscriptList } from './shared/TranscriptList';

export const OpsDashboard: React.FC = () => {
  const { summary, cdrs, loading, fetchMetrics } = useTelemetryPolling(5000);
  const [selectedCdr, setSelectedCdr] = useState<CallRecord | null>(null);

  const latencyOnTarget = summary ? summary.median_latency_ms <= (summary.latency_slo_target_ms || 1000) : true;

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
        <div className="flex items-center space-x-2">
          <a
            href="/api/telemetry/export?format=csv"
            className="py-1.5 px-3 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 text-xs flex items-center space-x-1.5 transition-all cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </a>
          <button
            onClick={() => fetchMetrics(true)}
            disabled={loading}
            className="py-1.5 px-3 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 text-xs flex items-center space-x-1.5 transition-all cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Feed</span>
          </button>
        </div>
      </div>

      {/* Initial Load Skeleton */}
      {!summary && loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg animate-pulse">
              <div className="h-3 w-24 bg-slate-800 rounded mb-3" />
              <div className="h-7 w-16 bg-slate-800 rounded mb-2" />
              <div className="h-2.5 w-32 bg-slate-800/70 rounded" />
            </div>
          ))}
        </div>
      )}

      {/* KPI Cards Grid */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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

          {/* Abandonment Rate */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>Abandonment Rate</span>
              <PhoneOff className="w-4 h-4 text-rose-400" />
            </div>
            <div className="text-2xl font-black text-rose-400">
              {summary.abandonment_rate_pct}%
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              {summary.abandoned_calls} calls dropped before resolution
            </div>
          </div>

          {/* Care CSAT */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>Avg Care CSAT</span>
              <Star className="w-4 h-4 text-amber-300" />
            </div>
            <div className="text-2xl font-black text-amber-300">
              {summary.avg_csat != null ? summary.avg_csat.toFixed(1) : '—'}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              {summary.csat_response_count} post-call ratings collected
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

          {/* Median Response Latency (SLO-aware) */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>Median Turn Latency</span>
              <ShieldCheck className={`w-4 h-4 ${latencyOnTarget ? 'text-cyan-400' : 'text-rose-400'}`} />
            </div>
            <div className={`text-2xl font-black ${latencyOnTarget ? 'text-cyan-300' : 'text-rose-400'}`}>
              {summary.median_latency_ms} ms
            </div>
            <div className={`text-[11px] mt-1 ${latencyOnTarget ? 'text-slate-500' : 'text-rose-400 font-semibold'}`}>
              SLO: ≤{summary.latency_slo_target_ms || 1000}ms · {summary.latency_slo_breach_pct}% of calls breached
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
            <DistributionBarList
              items={Object.entries(summary.intent_distribution)}
              total={summary.total_calls}
              unitLabel="calls"
              barColorClass="bg-indigo-500"
              labelColorClass="text-slate-200"
            />
          </div>

          {/* Escalation Drivers */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">
              Agent Escalation Root Causes
            </h3>
            <DistributionBarList
              items={Object.entries(summary.escalation_reasons)}
              total={summary.escalated_calls}
              unitLabel="transfers"
              barColorClass="bg-amber-500"
              labelColorClass="text-amber-300"
              emptyMessage="No escalations recorded."
            />
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
                        : cdr.final_state === 'ABANDONED'
                        ? 'bg-rose-950 text-rose-400 border border-rose-800'
                        : 'bg-amber-950 text-amber-400 border border-amber-800'
                    }`}>
                      {cdr.final_state === 'RESOLVED_CONTAINED' ? 'Contained' : cdr.final_state === 'ABANDONED' ? 'Abandoned' : 'Escalated'}
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
                  <TranscriptList turns={selectedCdr.transcript} variant="label-row" />
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
