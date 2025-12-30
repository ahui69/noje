import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { DEFAULT_TOKEN } from '../config';

interface AuthState {
  token: string;
  setToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: DEFAULT_TOKEN,
      setToken: (token: string) => set({ token }),
    }),
    { name: 'mrd-auth' },
  ),
);
