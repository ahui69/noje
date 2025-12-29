import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/auth';

export default function LoginPage() {
  const navigate = useNavigate();
  const setToken = useAuthStore((s) => s.setToken);
  const [token, setTokenLocal] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!token.trim()) {
      setError('Podaj token AUTH_TOKEN z backendu');
      return;
    }
    setToken(token.trim());
    navigate('/app');
  };

  return (
    <div className="min-h-screen bg-bg text-gray-100 flex items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-md p-8 border border-subtle rounded-lg bg-panel space-y-4">
        <div>
          <p className="text-sm text-gray-400">MRD FastAPI</p>
          <h1 className="text-2xl font-bold">Logowanie tokenem</h1>
        </div>
        <label className="block text-sm">
          Token Bearer
          <input
            className="mt-2 w-full bg-subtle border border-subtle rounded px-3 py-2 text-white focus:outline-none focus:border-accent"
            value={token}
            onChange={(e) => setTokenLocal(e.target.value)}
            placeholder="wpisz AUTH_TOKEN"
          />
        </label>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button type="submit" className="w-full bg-accent text-white py-2 rounded font-semibold hover:opacity-90">
          Zaloguj
        </button>
      </form>
    </div>
  );
}
