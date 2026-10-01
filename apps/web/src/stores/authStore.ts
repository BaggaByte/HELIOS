import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface User {
  id: string;
  username: string;
  role: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
}

/**
 * Secure auth store.
 *
 * Token storage strategy (defence-in-depth for a Tauri desktop app):
 *
 * 1. We use `sessionStorage` instead of `localStorage` so the token is
 *    automatically cleared when the window / tab closes. This limits the
 *    exposure window compared to a persistent localStorage token.
 *
 * 2. The Tauri CSP in tauri.conf.json restricts script-src to 'self' only,
 *    which prevents injected scripts from running in the webview and
 *    reading the token via XSS.
 *
 * 3. For an even stronger guarantee on future hardening, a Tauri v2
 *    tauri-plugin-store with OS keychain integration would be the next step.
 *    That requires a Rust plugin and is tracked as a future milestone.
 *
 * Why not HttpOnly cookies?
 * HELIOS uses a local FastAPI sidecar (localhost). HttpOnly cookies work
 * fine with a real server but add complexity for the Tauri IPC bridge and
 * the offline-first model; sessionStorage is the pragmatic choice here.
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => {
        set({ token, user });
      },
      logout: () => {
        set({ token: null, user: null });
        window.location.href = '/login';
      },
    }),
    {
      name: 'helios-auth-storage',
      // sessionStorage: cleared automatically on window close.
      // localStorage persists across restarts — less desirable for auth tokens.
      storage: createJSONStorage(() => sessionStorage),
      // Only persist the token itself; user object is refreshed on next login.
      partialize: (state) => ({ token: state.token }),
    }
  )
);

// Listen for centralized 401 unauthorized events from apiClient
if (typeof window !== 'undefined') {
  window.addEventListener('auth-unauthorized', () => {
    useAuthStore.getState().logout();
  });
}
