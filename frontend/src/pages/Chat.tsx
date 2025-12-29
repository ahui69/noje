import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { streamChat, SSEEvent } from '../api/sse';
import { ChatRequest, SessionDetail, UploadResponse } from '../api/types';
import MessageList, { Message } from '../components/MessageList';
import Composer from '../components/Composer';
import RightPanel from '../components/RightPanel';
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
    const res = await fetch(`${base}/api/files/upload`, {
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
  const queryClient = useQueryClient();
  const { currentSessionId, setCurrentSession, drafts, setDraft, clearDraft } = useSessionStore();
  const token = useAuthStore((s) => s.token);
  const apiBase = useSettingsStore((s) => s.apiBase?.trim()) || window.location.origin;

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState<{ id: string; name: string }[]>([]);
  const [streaming, setStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

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
    } else {
      setMessages([]);
    }
  }, [sessionData, activeSessionId, setCurrentSession]);

  useEffect(() => {
    if (!activeSessionId) return;
    const draft = drafts[activeSessionId];
    if (draft) setInput(draft);
  }, [activeSessionId, drafts]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg: Message = { role: 'user', content: input };
    const session = activeSessionId;
    const basePayload: ChatRequest = {
      message: input,
      session_id: session,
      user_id: 'web',
      use_history: true,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    if (session) clearDraft(session);

    setStreaming(true);
    const controller = new AbortController();
    abortRef.current = controller;

    const assistantMsg: Message = { role: 'assistant', content: '' };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
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
          alert(ev.data);
        }
      }, controller.signal);
    } catch (err: any) {
      alert(err.message || 'Stream error');
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
      alert(err.message || 'Upload error');
    } finally {
      setStreaming(false);
    }
  };

  const stopStreaming = () => {
    abortRef.current?.abort();
    setStreaming(false);
  };

  const messagesWithAttachments = useMemo(() => messages, [messages]);

  return (
    <div className="flex flex-1 h-full">
      <div className="flex-1 flex flex-col gap-4 p-6 overflow-hidden">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-400">Strumień SSE z /api/chat/assistant/stream</p>
            <h1 className="text-2xl font-bold">Czat</h1>
          </div>
          {streaming && (
            <button onClick={stopStreaming} className="text-sm text-red-300 border border-red-400 px-3 py-1 rounded">
              Zatrzymaj
            </button>
          )}
        </div>
        <MessageList messages={messagesWithAttachments} onCopy={(txt) => navigator.clipboard.writeText(txt)} />
        <Composer
          value={input}
          onChange={(v) => {
            setInput(v);
            if (activeSessionId) setDraft(activeSessionId, v);
          }}
          onSend={handleSend}
          disabled={streaming}
          uploading={streaming && attachments.length === 0}
          onUpload={handleUpload}
          attachments={attachments}
          onRemoveAttachment={(id) => setAttachments((prev) => prev.filter((a) => a.id !== id))}
        />
      </div>
      <RightPanel />
    </div>
  );
}
