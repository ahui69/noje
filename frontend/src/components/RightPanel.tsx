import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { HealthPayload, TTSStatus } from '../api/types';

async function fetchHealth(): Promise<HealthPayload> {
  return apiClient.get<HealthPayload>('/health');
}

async function fetchTTS(): Promise<TTSStatus> {
  return apiClient.get<TTSStatus>('/api/tts/status');
}

async function fetchSTTProviders(): Promise<{ ok: boolean; providers: any[] }> {
  return apiClient.get<{ ok: boolean; providers: any[] }>('/api/stt/providers');
}

export default function RightPanel() {
  const apiBase = (window.localStorage.getItem('mrd-settings') && JSON.parse(window.localStorage.getItem('mrd-settings') || '{}').state?.apiBase) || window.location.origin;
  const { data: health } = useQuery({ queryKey: ['health'], queryFn: fetchHealth, refetchInterval: 20000 });
  const { data: tts } = useQuery({ queryKey: ['tts'], queryFn: fetchTTS, refetchInterval: 60000 });
  const { data: stt } = useQuery({ queryKey: ['stt'], queryFn: fetchSTTProviders, refetchInterval: 60000 });

  return (
    <aside className="w-80 border-l border-subtle/60 bg-panel p-4 space-y-4">
      <div>
        <p className="text-sm text-gray-400">Status</p>
        <div className="mt-2 text-sm space-y-1">
          <p className="font-semibold text-white">{health?.status || 'unknown'}</p>
          {health?.version && <p className="text-gray-400">Version: {health.version}</p>}
          {health?.env && (
            <p className="text-gray-400 text-xs">Env: {Object.entries(health.env).map(([k, v]) => `${k}=${v}`).join(', ')}</p>
          )}
        </div>
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
