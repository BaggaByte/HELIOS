// uistore.ts
import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';

interface UiState {
  // State
  sidebarOpen: boolean;

  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
}

export const useUiStore = create<UiState>()(
  devtools(
    persist(
      (set) => ({
        // Default values (used on first load before localStorage is read)
        sidebarOpen: true,

        toggleSidebar: () =>
          set((state) => ({ sidebarOpen: !state.sidebarOpen }), false, 'toggleSidebar'),

        setSidebarOpen: (open) =>
          set({ sidebarOpen: open }, false, 'setSidebarOpen'),
      }),
      {
        name: 'ui-preferences', // Key used in localStorage
      }
    ),
    { name: 'UI Store' } // Name shown in Redux DevTools
  )
);