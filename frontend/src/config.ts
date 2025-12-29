// Vite udostępnia import.meta.env; fallback do localhost gdy zmienna nie ustawiona
const metaEnv: any = (import.meta as any).env || {};
export const API_BASE = (metaEnv.VITE_API_BASE as string | undefined)?.replace(/\/$/, '') || 'http://localhost:8000';
export const DEFAULT_MODEL = 'default';
