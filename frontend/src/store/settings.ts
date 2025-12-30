import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { API_BASE, DEFAULT_MODEL, DEFAULT_SAVE_DRAFTS, DEFAULT_STREAM } from '../config';

interface SettingsState {
  apiBase: string;
  model: string;
  stream: boolean;
  saveDrafts: boolean;
  setApiBase: (url: string) => void;
  setModel: (model: string) => void;
  setStream: (val: boolean) => void;
  setSaveDrafts: (val: boolean) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      apiBase: API_BASE,
      model: DEFAULT_MODEL,
      stream: DEFAULT_STREAM,
      saveDrafts: DEFAULT_SAVE_DRAFTS,
      setApiBase: (apiBase: string) => set({ apiBase }),
      setModel: (model: string) => set({ model }),
      setStream: (stream: boolean) => set({ stream }),
      setSaveDrafts: (saveDrafts: boolean) => set({ saveDrafts }),
    }),
    { name: 'mrd-settings' },
  ),
);
