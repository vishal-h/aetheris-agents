import { createContext } from 'react';

// Types
export type Theme = 'light' | 'dark' | 'system';

export interface AppState {
  activeModule: string;
  activeSidebarItem: string;
  rightPanelOpen: boolean;
  theme: Theme;
}

export type AppAction =
  | { type: 'SET_ACTIVE_MODULE'; payload: string }
  | { type: 'SET_ACTIVE_SIDEBAR_ITEM'; payload: string }
  | { type: 'SET_RIGHT_PANEL_OPEN'; payload: boolean }
  | { type: 'SET_THEME'; payload: Theme };

export interface AppContextValue extends AppState {
  setActiveModule: (module: string) => void;
  setActiveSidebarItem: (item: string) => void;
  setRightPanelOpen: (open: boolean) => void;
  setTheme: (theme: Theme) => void;
}

// Context object. Lives in this non-component module so AppContext.tsx can
// export only <AppProvider> and useApp.ts can export only the hook — both
// react-refresh/only-export-components clean (BL-018 #69).
export const AppContext = createContext<AppContextValue | undefined>(undefined);
