import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';

export type BackendStatus = 'CHECKING' | 'ONLINE' | 'OFFLINE';

/** Polls /api/health so the navbar status pill reflects the real backend state instead of a decorative dot. */
export function useHealthCheck(intervalMs: number = 8000): BackendStatus {
  const [status, setStatus] = useState<BackendStatus>('CHECKING');

  useEffect(() => {
    let cancelled = false;

    const check = () => {
      apiGet('/api/health')
        .then(() => { if (!cancelled) setStatus('ONLINE'); })
        .catch(() => { if (!cancelled) setStatus('OFFLINE'); });
    };

    check();
    const interval = setInterval(check, intervalMs);
    return () => { cancelled = true; clearInterval(interval); };
  }, [intervalMs]);

  return status;
}
