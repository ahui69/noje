import { API_BASE } from '../config';
import { useAuthStore } from '../store/auth';
import { useSettingsStore } from '../store/settings';

export function buildApiUrl(base: string, path: string): string {
  const trimmedBase = (base || '').replace(/\/$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;

  if (trimmedBase.endsWith('/api') && normalizedPath.startsWith('/api/')) {
    return `${trimmedBase}${normalizedPath.replace(/^\/api/, '')}`;
  }
  return `${trimmedBase}${normalizedPath}`;
}

export function resolveApiBase(customBase?: string): string {
  const base = customBase && customBase.trim().length > 0 ? customBase.trim() : API_BASE;
  return buildApiUrl(base, '');
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = useAuthStore.getState().token;
  const customBase = useSettingsStore.getState().apiBase?.trim();
  const base = resolveApiBase(customBase);
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(buildApiUrl(base, path), {
    ...options,
    headers,
  });

  if (res.status === 401) {
    useAuthStore.getState().setToken('');
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`HTTP ${res.status}: ${body || res.statusText}`);
  }

  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) {
    return (await res.json()) as T;
  }
  return (await res.text()) as unknown as T;
}

export const apiClient = {
  get: request,
  post: async <T>(path: string, body: any, init: RequestInit = {}): Promise<T> =>
    request<T>(path, { ...init, method: 'POST', body: JSON.stringify(body) }),
  delete: async <T>(path: string): Promise<T> => request<T>(path, { method: 'DELETE' }),
};
