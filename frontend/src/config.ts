// Vite udostępnia import.meta.env; fallback do origin serwującego aplikację
const metaEnv: any = (import.meta as any).env || {};

const parseBoolean = (val: any, fallback: boolean): boolean => {
  if (typeof val === 'boolean') return val;
  if (typeof val === 'string') {
    const lowered = val.trim().toLowerCase();
    if (['1', 'true', 'yes', 'on'].includes(lowered)) return true;
    if (['0', 'false', 'no', 'off'].includes(lowered)) return false;
  }
  return fallback;
};

const resolvedBase =
  (metaEnv.VITE_API_BASE as string | undefined) ||
  (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8080');

export const API_BASE = resolvedBase.replace(/\/$/, '');
export const DEFAULT_MODEL = (metaEnv.VITE_DEFAULT_MODEL as string | undefined) || 'default';
export const DEFAULT_STREAM = parseBoolean(metaEnv.VITE_STREAM_DEFAULT, true);
export const DEFAULT_SAVE_DRAFTS = parseBoolean(metaEnv.VITE_SAVE_DRAFTS, true);
export const DEFAULT_TOKEN = (metaEnv.VITE_AUTH_TOKEN as string | undefined) || '';
