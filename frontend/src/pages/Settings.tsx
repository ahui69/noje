import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '../store/auth';
import { useSettingsStore } from '../store/settings';
import { ModelList } from '../api/types';
import { apiClient } from '../api/client';

export default function SettingsPage() {
  const auth = useAuthStore();
  const settings = useSettingsStore();
  const [token, setToken] = useState(auth.token);
  const [apiBase, setApiBase] = useState(settings.apiBase);
  const [model, setModel] = useState(settings.model);
  const [stream, setStream] = useState(settings.stream);
  const [saveDrafts, setSaveDrafts] = useState(settings.saveDrafts);
  const [saved, setSaved] = useState('');

  const {
    data: modelList,
    isLoading: loadingModels,
    error: modelsError,
  } = useQuery({
    queryKey: ['models', token],
    queryFn: () => apiClient.get<ModelList>('/v1/models'),
    refetchInterval: 60000,
    enabled: !!token,
  });

  const modelOptions = useMemo(() => modelList?.data || [], [modelList]);

  useEffect(() => {
    if (modelOptions.length > 0 && (!model || model === 'default')) {
      setModel(modelOptions[0].id);
    }
  }, [modelOptions, model]);

  const save = () => {
    auth.setToken(token.trim());
    settings.setApiBase(apiBase.trim());
    settings.setModel(model.trim() || 'default');
    settings.setStream(stream);
    settings.setSaveDrafts(saveDrafts);
    setSaved('Zapisano ustawienia.');
    setTimeout(() => setSaved(''), 2500);
  };

  return (
    <div className="flex-1 p-6 space-y-6">
      <div>
        <p className="text-sm text-gray-400">Ustawienia</p>
        <h1 className="text-2xl font-bold">Konto i API</h1>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="border border-subtle rounded-lg p-4 space-y-3 bg-panel">
          <h2 className="font-semibold">Token</h2>
          <input
            className="w-full bg-subtle border border-subtle rounded px-3 py-2"
            value={token}
            onChange={(e) => setToken(e.target.value)}
          />
          <p className="text-xs text-gray-400">AUTH_TOKEN używany w nagłówku Authorization</p>
        </div>
        <div className="border border-subtle rounded-lg p-4 space-y-3 bg-panel">
          <h2 className="font-semibold">API Base</h2>
          <input
            className="w-full bg-subtle border border-subtle rounded px-3 py-2"
            placeholder="http://localhost:8000"
            value={apiBase}
            onChange={(e) => setApiBase(e.target.value)}
          />
          <p className="text-xs text-gray-400">Opcjonalne nadpisanie adresu backendu</p>
        </div>
        <div className="border border-subtle rounded-lg p-4 space-y-3 bg-panel">
          <h2 className="font-semibold">Model</h2>
          {loadingModels && <p className="text-xs text-gray-400">Ładowanie modeli…</p>}
          {modelsError && (
            <p className="text-xs text-red-400">Błąd pobierania modeli: {(modelsError as Error).message}</p>
          )}
          {modelOptions.length > 0 && (
            <select
              className="w-full bg-subtle border border-subtle rounded px-3 py-2 text-sm"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              {modelOptions.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.id}
                </option>
              ))}
            </select>
          )}
          <input
            className="w-full bg-subtle border border-subtle rounded px-3 py-2"
            placeholder="np. NousResearch/Hermes-3"
            value={model}
            onChange={(e) => setModel(e.target.value)}
          />
          <p className="text-xs text-gray-400">Model preferowany przez frontend; pobierany z /v1/models lub wpisany ręcznie.</p>
        </div>
        <div className="border border-subtle rounded-lg p-4 space-y-3 bg-panel">
          <h2 className="font-semibold">Streaming i drafty</h2>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={stream} onChange={(e) => setStream(e.target.checked)} />
            Włącz streaming SSE
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={saveDrafts} onChange={(e) => setSaveDrafts(e.target.checked)} />
            Zachowuj drafty per sesja
          </label>
          <p className="text-xs text-gray-400">Wyłączenie streamingu przełączy czat na tryb synchroniczny</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button onClick={save} className="px-4 py-2 rounded bg-accent text-white font-semibold">
          Zapisz
        </button>
        {saved && <span className="text-xs text-green-300">{saved}</span>}
      </div>
    </div>
  );
}
