import { Outlet, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Sidebar from '../components/Sidebar';
import { useAuthStore } from '../store/auth';
import RightPanel from '../components/RightPanel';

export default function AppShell() {
  const navigate = useNavigate();
  const [isDesktop, setIsDesktop] = useState(() =>
    typeof window !== 'undefined' ? window.innerWidth >= 1024 : true,
  );
  const [sidebarOpen, setSidebarOpen] = useState(() =>
    typeof window !== 'undefined' ? window.innerWidth >= 1024 : false,
  );
  const [panelOpen, setPanelOpen] = useState(() =>
    typeof window !== 'undefined' ? window.innerWidth >= 1024 : false,
  );

  useEffect(() => {
    const onResize = () => {
      const desktop = window.innerWidth >= 1024;
      setIsDesktop(desktop);
      setSidebarOpen(desktop);
      setPanelOpen(desktop);
    };
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const logout = () => {
    useAuthStore.getState().setToken('');
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex bg-bg relative">
      {!isDesktop && sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-30"
          aria-label="Zamknij panel sesji"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      {!isDesktop && panelOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-30"
          aria-label="Zamknij panel statusu"
          onClick={() => setPanelOpen(false)}
        />
      )}

      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} isDesktop={isDesktop} />
      <main className="flex-1 flex flex-col bg-bg relative z-10">
        <header className="h-14 border-b border-subtle/60 px-4 flex items-center justify-between bg-panel sticky top-0 z-20">
          <div className="flex items-center gap-3 text-sm text-gray-300">
            <button
              onClick={() => setSidebarOpen((v) => !v)}
              className="lg:hidden px-2 py-1 rounded border border-subtle hover:bg-subtle/50"
              aria-label="Przełącz panel sesji"
            >
              ☰
            </button>
            <span>MRD FastAPI</span>
          </div>
          <div className="flex gap-3 items-center text-sm">
            <button
              className="px-3 py-1 rounded border border-subtle hover:bg-subtle/50"
              onClick={() => navigate('/app/settings')}
            >
              Ustawienia
            </button>
            <button
              className="px-3 py-1 rounded border border-subtle hover:bg-subtle/50"
              onClick={() => setPanelOpen((v) => !v)}
            >
              {panelOpen ? 'Schowaj panel' : 'Pokaż panel'}
            </button>
            <button className="px-3 py-1 rounded border border-subtle hover:bg-subtle/50" onClick={logout}>
              Wyloguj
            </button>
          </div>
        </header>
        <div className="flex-1 flex overflow-hidden">
          <Outlet context={{ panelOpen, isDesktop, openPanel: () => setPanelOpen(true) }} />
        </div>
      </main>
      <RightPanel isOpen={panelOpen} onClose={() => setPanelOpen(false)} isDesktop={isDesktop} />
    </div>
  );
}
