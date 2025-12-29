import { useState } from 'react';
import { useAuthStore } from '../store/auth';
import { useSettingsStore } from '../store/settings';

export default function SettingsPage() {
  const auth = useAuthStore();
  const settings = useSettingsStore();
  const [token, setToken] = useState(auth.token);
  const [apiBase, setApiBase] = useState(settings.apiBase);

  const save = () => {
    auth.setToken(token.trim());
    settings.setApiBase(apiBase.trim());
    alert('Zapisano');
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
      </div>
      <button onClick={save} className="px-4 py-2 rounded bg-accent text-white font-semibold">
        Zapisz
      </button>
    </div>
  );
}
