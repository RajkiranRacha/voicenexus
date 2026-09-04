import { useState, useEffect, useCallback } from 'react';
import { apiGet } from '../api/client';
import type { TelemetrySummary, CallRecord } from '../types';

/** Polls the Care-Ops telemetry summary + CDRs on an interval. */
export function useTelemetryPolling(intervalMs: number = 5000) {
  const [summary, setSummary] = useState<TelemetrySummary | null>(null);
  const [cdrs, setCdrs] = useState<CallRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchMetrics = useCallback(() => {
    setLoading(true);
    Promise.all([
      apiGet<TelemetrySummary>('/api/telemetry/summary'),
      apiGet<CallRecord[]>('/api/telemetry/cdrs'),
    ])
      .then(([sumData, cdrData]) => {
        setSummary(sumData);
        setCdrs(cdrData);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, intervalMs);
    return () => clearInterval(interval);
  }, [fetchMetrics, intervalMs]);

  return { summary, cdrs, loading, fetchMetrics };
}
