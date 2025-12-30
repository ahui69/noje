import { API_BASE } from '../config';
import { useAuthStore } from '../store/auth';
import { useSettingsStore } from '../store/settings';
import { buildApiUrl } from './client';

export type SSEEvent = { event: string; data: any };

export async function streamChat(
  path: string,
  body: any,
  onEvent: (ev: SSEEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const token = useAuthStore.getState().token;
  const customBase = useSettingsStore.getState().apiBase?.trim();
  const base = customBase || API_BASE;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(buildApiUrl(base, path), {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
    signal,
  });

  if (!res.ok || !res.body) {
    const text = await res.text();
    throw new Error(`Stream error ${res.status}: ${text}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buf = '';

  while (true) {
    const chunk = await reader.read();
    if (chunk.done) break;
    buf += decoder.decode(chunk.value, { stream: true });

    const parts = buf.split('\n\n');
    buf = parts.pop() || '';

    for (const part of parts) {
      if (!part.trim()) continue;
      if (part.startsWith(':')) continue;
      const line = part.replace(/^data:\s*/, '');
      try {
        const parsed = JSON.parse(line);
        if (parsed.event) {
          onEvent(parsed as SSEEvent);
        }
      } catch (err) {
        console.warn('SSE parse error', err, part);
      }
    }
  }

  if (buf.trim()) {
    try {
      const parsed = JSON.parse(buf.replace(/^data:\s*/, ''));
      if (parsed.event) onEvent(parsed as SSEEvent);
    } catch (err) {
      console.warn('SSE parse tail error', err, buf);
    }
  }
}
