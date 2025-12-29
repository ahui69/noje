import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { SessionSummary } from '../api/types';
import { useSessionStore } from '../store/sessions';

async function fetchSessions(): Promise<SessionSummary[]> {
  const data = await apiClient.get<{ ok: boolean; sessions: SessionSummary[] }>('/api/chat/sessions');
  return data.sessions || [];
}

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  isDesktop: boolean;
}

export default function Sidebar({ isOpen, onClose, isDesktop }: SidebarProps) {
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const queryClient = useQueryClient();
  const setCurrentSession = useSessionStore((s) => s.setCurrentSession);

  const { data, isLoading, error } = useQuery({
    queryKey: ['sessions'],
    queryFn: fetchSessions,
    refetchInterval: 15000,
  });

  const sessions = data || [];

  const handleNew = () => {
    setCurrentSession(undefined);
    navigate('/app/chat');
    if (!isDesktop) onClose();
  };

  const handleRefresh = () => queryClient.invalidateQueries({ queryKey: ['sessions'] });

  if (!isDesktop && !isOpen) {
    return null;
  }

  return (
    <aside
      className={
        isDesktop
          ? 'w-72 bg-panel border-r border-subtle/60 flex flex-col'
          : 'fixed inset-y-0 left-0 w-72 bg-panel border-r border-subtle/60 flex flex-col z-40 shadow-xl'
      }
    >
      <div className="p-4 flex items-center justify-between border-b border-subtle/60">
        <div>
          <p className="text-sm text-gray-400">MRD Console</p>
          <p className="text-lg font-semibold">Sesje</p>
        </div>
        <div className="flex items-center gap-2">
          {!isDesktop && (
            <button
              onClick={onClose}
              className="text-xs text-gray-300 hover:text-white border border-subtle px-2 py-1 rounded"
            >
              Zamknij
            </button>
          )}
          <button
            onClick={handleRefresh}
            className="text-xs text-gray-300 hover:text-white border border-subtle px-2 py-1 rounded"
          >
            Odśwież
          </button>
        </div>
      </div>
      <div className="p-3 flex gap-2">
        <button
          onClick={handleNew}
          className="flex-1 bg-accent text-white rounded px-3 py-2 text-sm font-semibold hover:opacity-90"
        >
          Nowy czat
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {isLoading && <p className="text-sm text-gray-400 px-4">Ładowanie…</p>}
        {error && <p className="text-sm text-red-400 px-4">{(error as Error).message}</p>}
        {!isLoading && !error && sessions.length === 0 && (
          <p className="text-sm text-gray-400 px-4">Brak sesji.</p>
        )}
        <ul className="space-y-1 px-2 pb-4">
          {sessions.map((s) => {
            const active = sessionId === s.id;
            const title = s.title?.trim() || 'Bez tytułu';
            return (
              <li key={s.id}>
                <button
                  onClick={() => {
                    setCurrentSession(s.id);
                    navigate(`/app/chat/${s.id}`);
                    if (!isDesktop) onClose();
                  }}
                  className={`w-full text-left px-3 py-2 rounded-md border border-transparent hover:border-subtle/80 hover:bg-subtle/60 ${
                    active ? 'bg-subtle border-subtle/80' : ''
                  }`}
                >
                  <p className="text-sm font-semibold text-white truncate">{title}</p>
                  <p className="text-xs text-gray-400">{s.messages} wiadomości</p>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </aside>
  );
}
