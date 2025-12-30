import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useOutletContext, useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient, buildApiUrl, resolveApiBase } from '../api/client';
import { API_BASE } from '../config';
import { streamChat, SSEEvent } from '../api/sse';
import { AttachmentRef, ChatRequest, ChatResponse, SessionDetail, UploadResponse } from '../api/types';
import MessageList, { Message } from '../components/MessageList';
import Composer from '../components/Composer';
import { useSessionStore } from '../store/sessions';
import { useAuthStore } from '../store/auth';
import { useSettingsStore } from '../store/settings';

async function fetchSession(sessionId: string): Promise<SessionDetail> {
  const res = await apiClient.get<SessionDetail>(`/api/chat/sessions/${sessionId}`);
  return res;
}

async function uploadFile(files: FileList, base: string, token: string): Promise<UploadResponse[]> {
  const uploaded: UploadResponse[] = [];
  for (const file of Array.from(files)) {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(buildApiUrl(base, '/api/files/upload'), {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`Upload failed: ${txt}`);
    }
    uploaded.push((await res.json()) as UploadResponse);
  }
  return uploaded;
}

export default function ChatPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { panelOpen, isDesktop, openPanel } = useOutletContext<{
    panelOpen: boolean;
    isDesktop: boolean;
    openPanel: () => void;
  }>();
  const queryClient = useQueryClient();
  const { currentSessionId, setCurrentSession, drafts, setDraft, clearDraft } = useSessionStore();
  const token = useAuthStore((s) => s.token);
  const apiBase = resolveApiBase(useSettingsStore((s) => s.apiBase?.trim()) || API_BASE);
  const streamEnabled = useSettingsStore((s) => s.stream);
  const saveDrafts = useSettingsStore((s) => s.saveDrafts);
  const preferredModel = useSettingsStore((s) => s.model);

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState<{ id: string; name: string }[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [titleInput, setTitleInput] = useState('');
  const [savingTitle, setSavingTitle] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const [errorBanner, setErrorBanner] = useState('');

  const activeSessionId = sessionId || currentSessionId;

  const { data: sessionData } = useQuery({
    queryKey: ['session', activeSessionId],
    queryFn: () => fetchSession(activeSessionId || ''),
    enabled: !!activeSessionId,
  });

  useEffect(() => {
    if (sessionData) {
      setMessages(sessionData.messages as Message[]);
      setCurrentSession(sessionData.session_id || activeSessionId);
      setTitleInput(sessionData.title || '');
    } else {
      setMessages([]);
      setTitleInput('');
    }
  }, [sessionData, activeSessionId, setCurrentSession]);

  useEffect(() => {
    if (!activeSessionId) return;
    const draft = drafts[activeSessionId];
    if (draft) setInput(draft);
  }, [activeSessionId, drafts]);

  const attachmentPayload: AttachmentRef[] = attachments.map((a) => ({ file_id: a.id, name: a.name }));

  const handleSend = async () => {
    if (!input.trim()) return;
    setErrorBanner('');
    const userMsg: Message = { role: 'user', content: input, attachments: attachmentPayload };
    const session = activeSessionId;
    const basePayload: ChatRequest = {
      message: input,
      session_id: session,
      user_id: 'web',
      use_history: true,
      model: preferredModel,
      attachments: attachmentPayload,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    if (session && saveDrafts) clearDraft(session);
    setAttachments([]);

    setStreaming(true);
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      if (!streamEnabled) {
        const res = await apiClient.post<ChatResponse>('/api/chat/assistant', basePayload);
        const sid = res.session_id || session;
        const assistantMsg: Message = { role: 'assistant', content: res.answer };
        setMessages((prev) => [...prev, assistantMsg]);
        if (sid) {
          setCurrentSession(sid);
          navigate(`/app/chat/${sid}`);
        }
      } else {
        const assistantMsg: Message = { role: 'assistant', content: '' };
        setMessages((prev) => [...prev, assistantMsg]);
        await streamChat('/api/chat/assistant/stream', basePayload, (ev: SSEEvent) => {
          if (ev.event === 'meta') {
            const sid = ev.data.session_id as string;
            if (sid && sid !== activeSessionId) {
              setCurrentSession(sid);
              navigate(`/app/chat/${sid}`);
            }
          }
          if (ev.event === 'delta') {
            assistantMsg.content += String(ev.data || '');
            setMessages((prev) => {
              const copy = [...prev];
              copy[copy.length - 1] = { ...assistantMsg };
              return copy;
            });
          }
          if (ev.event === 'error') {
            setErrorBanner(String(ev.data || 'Błąd strumienia'));
          }
        }, controller.signal);
      }
    } catch (err: any) {
      setErrorBanner(err.message || 'Błąd komunikacji');
    } finally {
      setStreaming(false);
      abortRef.current = null;
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      const sid = sessionData?.session_id || activeSessionId;
      if (sid) queryClient.invalidateQueries({ queryKey: ['session', sid] });
    }
  };

  const handleUpload = async (files: FileList) => {
    try {
      setStreaming(true);
      const res = await uploadFile(files, apiBase.replace(/\/$/, ''), token);
      const mapped = res.map((r) => ({ id: r.file_id, name: r.filename }));
      setAttachments((prev) => [...prev, ...mapped]);
    } catch (err: any) {
      setErrorBanner(err.message || 'Błąd uploadu');
    } finally {
      setStreaming(false);
    }
  };

  const stopStreaming = () => {
    abortRef.current?.abort();
    setStreaming(false);
  };

  const saveTitleHandler = async () => {
    if (!activeSessionId) return;
    setSavingTitle(true);
    try {
      await apiClient.post(`/api/chat/sessions/${activeSessionId}/title`, { title: titleInput.trim() || 'Bez tytułu' });
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['session', activeSessionId] });
    } catch (err: any) {
      setErrorBanner(err.message || 'Błąd zapisu tytułu');
    } finally {
      setSavingTitle(false);
    }
  };

  const deleteSession = async () => {
    if (!activeSessionId) return;
    if (!confirm('Usunąć sesję wraz z historią?')) return;
    try {
      await apiClient.post(`/api/chat/sessions/${activeSessionId}/delete`, {});
      setMessages([]);
      setCurrentSession(undefined);
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      navigate('/app/chat');
    } catch (err: any) {
      setErrorBanner(err.message || 'Błąd usuwania sesji');
    }
  };

  const messagesWithAttachments = useMemo(() => messages, [messages]);

  return (
    <div className="flex flex-1 h-full flex-col lg:flex-row w-full max-w-full">
      <div className="flex-1 flex flex-col gap-4 p-4 md:p-6 overflow-hidden max-w-6xl mx-auto w-full">
        {errorBanner && (
          <div className="rounded-md border border-red-500/60 bg-red-900/30 text-sm text-red-100 px-4 py-3 flex items-start justify-between gap-3">
            <span>{errorBanner}</span>
            <button
              className="text-xs underline hover:no-underline"
              onClick={() => setErrorBanner('')}
              aria-label="Zamknij komunikat błędu"
            >
              Zamknij
            </button>
          </div>
        )}
        <div className="flex items-start flex-wrap justify-between gap-4 rounded-lg border border-subtle bg-panel/80 px-4 py-3 shadow-sm">
          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <span>Endpoint:</span>
              <span className="px-2 py-1 rounded bg-subtle/70 border border-subtle/70">/api/chat/assistant{streamEnabled ? '/stream' : ''}</span>
            </div>
            <h1 className="text-2xl font-bold">Czat</h1>
            {activeSessionId && (
              <div className="flex items-center gap-2 flex-wrap">
                <input
                  className="bg-subtle border border-subtle rounded px-3 py-2 text-sm flex-1 min-w-[220px]"
                  value={titleInput}
                  onChange={(e) => setTitleInput(e.target.value)}
                  placeholder="Tytuł sesji"
                />
                <button
                  onClick={saveTitleHandler}
                  disabled={savingTitle}
                  className="px-3 py-2 text-sm rounded border border-subtle hover:bg-subtle/60"
                >
                  {savingTitle ? 'Zapisywanie…' : 'Zapisz'}
                </button>
                <button
                  onClick={deleteSession}
                  className="px-3 py-2 text-sm rounded border border-red-400 text-red-200 hover:bg-red-900/40"
                >
                  Usuń
                </button>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">{streamEnabled ? 'SSE' : 'Sync'}</span>
            {streaming && (
              <button onClick={stopStreaming} className="text-sm text-red-300 border border-red-400 px-3 py-1 rounded">
                Zatrzymaj
              </button>
            )}
            {!panelOpen && (
              <button
                onClick={openPanel}
                className="text-sm border border-subtle px-3 py-1 rounded hover:bg-subtle/60"
              >
                Panel PRO
              </button>
            )}
          </div>
        </div>
        <MessageList messages={messagesWithAttachments} onCopy={(txt) => navigator.clipboard.writeText(txt)} />
        <Composer
          value={input}
          onChange={(v) => {
            setInput(v);
            if (activeSessionId && saveDrafts) setDraft(activeSessionId, v);
          }}
          onSend={handleSend}
          disabled={streaming}
          uploading={streaming && attachments.length === 0}
          onUpload={handleUpload}
          attachments={attachments}
          onRemoveAttachment={(id) => setAttachments((prev) => prev.filter((a) => a.id !== id))}
        />
      </div>
    </div>
  );
}
