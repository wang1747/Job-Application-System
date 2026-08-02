import { create } from "zustand";
import type { User } from "../types";
import { api } from "../api/client";

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  initialize: () => Promise<void>;
  login: (token: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
}

const TOKEN_KEY = "access_token";

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem(TOKEN_KEY),
  user: null,
  isAuthenticated: Boolean(localStorage.getItem(TOKEN_KEY)),

  initialize: async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      set({ token: null, user: null, isAuthenticated: false });
      return;
    }

    try {
      const res = await api.auth.me();
      if (res.success && res.data) {
        set({ token, user: res.data, isAuthenticated: true });
      } else {
        localStorage.removeItem(TOKEN_KEY);
        set({ token: null, user: null, isAuthenticated: false });
      }
    } catch {
      localStorage.removeItem(TOKEN_KEY);
      set({ token: null, user: null, isAuthenticated: false });
    }
  },

  login: (token) => {
    localStorage.setItem(TOKEN_KEY, token);
    set({ token, isAuthenticated: true });
  },

  setUser: (user) => set({ user }),

  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    set({ token: null, user: null, isAuthenticated: false });
  },
}));
