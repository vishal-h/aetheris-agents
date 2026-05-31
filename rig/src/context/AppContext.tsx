import { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';

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

interface AppContextValue extends AppState {
  setActiveModule: (module: string) => void;
  setActiveSidebarItem: (item: string) => void;
  setRightPanelOpen: (open: boolean) => void;
  setTheme: (theme: Theme) => void;
}

// Initial state
const initialState: AppState = {
  activeModule: 'f2',
  activeSidebarItem: 'f2-operations',
  rightPanelOpen: false,
  theme: 'system',
};

// Reducer
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_ACTIVE_MODULE':
      return { ...state, activeModule: action.payload };
    case 'SET_ACTIVE_SIDEBAR_ITEM':
      return { ...state, activeSidebarItem: action.payload };
    case 'SET_RIGHT_PANEL_OPEN':
      return { ...state, rightPanelOpen: action.payload };
    case 'SET_THEME':
      return { ...state, theme: action.payload };
    default:
      return state;
  }
}

// Context
const AppContext = createContext<AppContextValue | undefined>(undefined);

// Helper to resolve actual theme from "system"
function resolveTheme(theme: Theme): 'light' | 'dark' {
  if (theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return theme;
}

// Provider
export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Apply theme to document.documentElement
  useEffect(() => {
    const actualTheme = resolveTheme(state.theme);
    document.documentElement.setAttribute('data-theme', actualTheme);
  }, [state.theme]);

  // Listen for system theme changes when theme is "system"
  useEffect(() => {
    if (state.theme !== 'system') {
      return;
    }

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      const actualTheme = resolveTheme('system');
      document.documentElement.setAttribute('data-theme', actualTheme);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [state.theme]);

  const value: AppContextValue = {
    ...state,
    setActiveModule: (module: string) =>
      dispatch({ type: 'SET_ACTIVE_MODULE', payload: module }),
    setActiveSidebarItem: (item: string) =>
      dispatch({ type: 'SET_ACTIVE_SIDEBAR_ITEM', payload: item }),
    setRightPanelOpen: (open: boolean) =>
      dispatch({ type: 'SET_RIGHT_PANEL_OPEN', payload: open }),
    setTheme: (theme: Theme) =>
      dispatch({ type: 'SET_THEME', payload: theme }),
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

// Hook
export function useApp(): AppContextValue {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
