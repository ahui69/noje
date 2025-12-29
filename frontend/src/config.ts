// Vite udostępnia import.meta.env; fallback do origin serwującego aplikację
const metaEnv: any = (import.meta as any).env || {};
const resolvedBase =
  (metaEnv.VITE_API_BASE as string | undefined) ||
  (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8080');

export const API_BASE = resolvedBase.replace(/\/$/, '');
export const DEFAULT_MODEL = 'default';
