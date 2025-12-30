import { useQuery } from '@tanstack/react-query';
import { apiClient, buildApiUrl, resolveApiBase } from '../api/client';
import { API_BASE } from '../config';
import { HealthPayload, TTSStatus } from '../api/types';
import { useSettingsStore } from '../store/settings';

async function fetchHealth(): Promise<HealthPayload> {
  return apiClient.get<HealthPayload>('/health');
}

async function fetchTTS(): Promise<TTSStatus> {
  return apiClient.get<TTSStatus>('/api/tts/status');
}

async function fetchSTTProviders(): Promise<{ ok: boolean; providers: any[] }> {
  return apiClient.get<{ ok: boolean; providers: any[] }>('/api/stt/providers');
}

interface RightPanelProps {
  isOpen: boolean;
  onClose: () => void;
  isDesktop: boolean;
}

export default function RightPanel({ isOpen, onClose, isDesktop }: RightPanelProps) {
  const apiBase = resolveApiBase(useSettingsStore((s) => s.apiBase?.trim()) || API_BASE || window.location.origin);
  const { data: health } = useQuery({ queryKey: ['health', apiBase], queryFn: fetchHealth, refetchInterval: 20000 });
  const { data: tts } = useQuery({ queryKey: ['tts', apiBase], queryFn: fetchTTS, refetchInterval: 60000 });
  const { data: stt } = useQuery({ queryKey: ['stt', apiBase], queryFn: fetchSTTProviders, refetchInterval: 60000 });

  if (!isDesktop && !isOpen) {
    return null;
  }

  return (
    <aside
      className={
        isDesktop
          ? 'w-80 border-l border-subtle/60 bg-panel p-4 space-y-4'
          : 'fixed inset-y-0 right-0 w-80 max-w-[calc(100vw-48px)] border-l border-subtle/60 bg-panel p-4 space-y-4 z-40 shadow-xl'
      }
    >
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-400">Status</p>
        {!isDesktop && (
          <button
            onClick={onClose}
            className="text-xs text-gray-300 hover:text-white border border-subtle px-2 py-1 rounded"
          >
            Zamknij
          </button>
        )}
      </div>
      <div className="mt-2 text-sm space-y-1">
        <p className="font-semibold text-white">{health?.status || 'unknown'}</p>
        {health?.version && <p className="text-gray-400">Version: {health.version}</p>}
        {health?.env && (
          <p className="text-gray-400 text-xs">Env: {Object.entries(health.env).map(([k, v]) => `${k}=${v}`).join(', ')}</p>
        )}
      </div>
      <div className="border-t border-subtle/60 pt-4">
        <p className="text-sm text-gray-400">Audio</p>
        <div className="mt-2 text-sm space-y-1">
          <p>TTS: {tts?.ok ? 'gotowy' : 'brak'} ({tts?.provider || '-'})</p>
          <p>STT: {stt?.ok ? `${stt.providers.length} dost.` : 'brak kluczy'}</p>
        </div>
      </div>
      <div className="border-t border-subtle/60 pt-4 text-sm text-gray-400">
        <p className="text-white font-semibold mb-2">Debug</p>
        <p>API Base: {apiBase}</p>
      </div>
    </aside>
  );
}
