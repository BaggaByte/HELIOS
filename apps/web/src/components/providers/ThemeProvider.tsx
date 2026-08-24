import { useEffect } from 'react';
import type { ReactNode } from 'react';
import { useUiStore } from '../../stores/uiStore'; // Adjust path as needed

export function ThemeProvider({ children }: { children: ReactNode }) {
  const theme = useUiStore((state) => state.theme);

  useEffect(() => {
    const root = window.document.documentElement;
    
    // Remove existing theme classes to prevent conflicts
    root.classList.remove('light', 'dark');

    if (theme === 'system') {
      // Check OS preference if 'system' is selected
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
      root.classList.add(systemTheme);
    } else {
      // Apply 'light' or 'dark' explicitly
      root.classList.add(theme);
    }
  }, [theme]);

  return <>{children}</>;
}
