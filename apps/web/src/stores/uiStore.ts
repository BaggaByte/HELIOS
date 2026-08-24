// uistore.ts
import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';

export type Theme = 'light' | 'dark' | 'system';

interface UiState {
  // State
  sidebarOpen: boolean;
  theme: Theme;

  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: Theme) => void;
}

export const useUiStore = create<UiState>()(
  devtools(
    persist(
      (set) => ({
        // Default values (used on first load before localStorage is read)
        sidebarOpen: true,
        theme: 'system', // 'system' is a great modern default

        toggleSidebar: () =>
          set((state) => ({ sidebarOpen: !state.sidebarOpen }), false, 'toggleSidebar'),

        setSidebarOpen: (open) =>
          set({ sidebarOpen: open }, false, 'setSidebarOpen'),

        setTheme: (theme) =>
          set({ theme }, false, 'setTheme'),
      }),
      {
        name: 'ui-preferences', // Key used in localStorage
      }
    ),
    { name: 'UI Store' } // Name shown in Redux DevTools
  )
);