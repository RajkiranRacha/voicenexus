/**
 * Thin shared wrappers around fetch()/WebSocket so every component talks to
 * the backend the same way instead of rolling its own protocol-detection
 * and JSON parsing.
 */

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`GET ${path} failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function apiPost<T = unknown>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    throw new Error(`POST ${path} failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function apiDelete<T = unknown>(path: string): Promise<T> {
  const res = await fetch(path, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error(`DELETE ${path} failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

/** Builds a same-origin ws:// or wss:// URL matching the page's protocol. */
export function wsUrl(path: string): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}${path}`;
}
