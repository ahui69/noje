import { Outlet, useNavigate } from 'react-router-dom';
import { useEffect, useMemo, useState } from 'react';
import Sidebar from '../components/Sidebar';
import { useAuthStore } from '../store/auth';
import RightPanel from '../components/RightPanel';

export default function AppShell() {
  const navigate = useNavigate();
  const initialDesktop = useMemo(
    () => (typeof window !== 'undefined' ? window.matchMedia('(min-width: 1024px)').matches : false),
    [],
  );
  const [isDesktop, setIsDesktop] = useState(initialDesktop);
  const [sidebarOpen, setSidebarOpen] = useState(initialDesktop);
  const [panelOpen, setPanelOpen] = useState(false);

  useEffect(() => {
    const media = window.matchMedia('(min-width: 1024px)');
    const update = (matches: boolean) => {
      setIsDesktop(matches);
      if (matches) {
        setSidebarOpen(true);
        setPanelOpen(false);
      } else {
        setSidebarOpen(false);
        setPanelOpen(false);
      }
    };
    update(media.matches);
    const listener = (event: MediaQueryListEvent) => update(event.matches);
    media.addEventListener('change', listener);

    const escHandler = (ev: KeyboardEvent) => {
      if (ev.key === 'Escape') {
        setSidebarOpen(false);
        setPanelOpen(false);
      }
    };
    window.addEventListener('keydown', escHandler);

    return () => {
      media.removeEventListener('change', listener);
      window.removeEventListener('keydown', escHandler);
    };
  }, []);

  useEffect(() => {
    if (!isDesktop && (sidebarOpen || panelOpen)) {
      document.body.classList.add('overflow-hidden');
    } else {
      document.body.classList.remove('overflow-hidden');
    }
    return () => document.body.classList.remove('overflow-hidden');
  }, [isDesktop, sidebarOpen, panelOpen]);

  const logout = () => {
    useAuthStore.getState().setToken('');
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex bg-bg relative overflow-hidden w-full max-w-full">
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
      <main className="flex-1 flex flex-col bg-bg relative z-10 w-full max-w-full">
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
        <div className="flex-1 flex overflow-hidden max-w-full">
          <Outlet context={{ panelOpen, isDesktop, openPanel: () => setPanelOpen(true) }} />
        </div>
      </main>
      <RightPanel isOpen={panelOpen} onClose={() => setPanelOpen(false)} isDesktop={isDesktop} />
    </div>
  );
}
