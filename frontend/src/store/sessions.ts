import { create } from 'zustand';

interface DraftState {
  drafts: Record<string, string>;
  setDraft: (sessionId: string, value: string) => void;
  clearDraft: (sessionId: string) => void;
  currentSessionId?: string;
  setCurrentSession: (id?: string) => void;
}

export const useSessionStore = create<DraftState>((set) => ({
  drafts: {},
  currentSessionId: undefined,
  setDraft: (sessionId: string, value: string) =>
    set((state) => ({ drafts: { ...state.drafts, [sessionId]: value } })),
  clearDraft: (sessionId: string) =>
    set((state) => {
      const next = { ...state.drafts };
      delete next[sessionId];
      return { drafts: next };
    }),
  setCurrentSession: (id?: string) => set({ currentSessionId: id }),
}));
