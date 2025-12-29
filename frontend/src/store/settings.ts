import { create } from 'zustand';
import { persist } from 'zustand/middleware';

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
      apiBase: '',
      model: 'default',
      stream: true,
      saveDrafts: true,
      setApiBase: (apiBase: string) => set({ apiBase }),
      setModel: (model: string) => set({ model }),
      setStream: (stream: boolean) => set({ stream }),
      setSaveDrafts: (saveDrafts: boolean) => set({ saveDrafts }),
    }),
    { name: 'mrd-settings' },
  ),
);
