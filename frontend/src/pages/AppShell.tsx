import { Outlet, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { useAuthStore } from '../store/auth';

export default function AppShell() {
  const navigate = useNavigate();
  const logout = () => {
    useAuthStore.getState().setToken('');
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex">
      <Sidebar />
      <main className="flex-1 flex flex-col bg-bg">
        <header className="h-14 border-b border-subtle/60 px-4 flex items-center justify-between bg-panel">
          <div className="text-sm text-gray-300">MRD FastAPI</div>
          <div className="flex gap-3 items-center text-sm">
            <button
              className="px-3 py-1 rounded border border-subtle hover:bg-subtle/50"
              onClick={() => navigate('/app/settings')}
            >
              Ustawienia
            </button>
            <button className="px-3 py-1 rounded border border-subtle hover:bg-subtle/50" onClick={logout}>
              Wyloguj
            </button>
          </div>
        </header>
        <div className="flex-1 flex overflow-hidden">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
