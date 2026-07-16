import { useReducer, useEffect, ReactNode } from 'react';

import {
  AppContext,
  type AppState,
  type AppAction,
  type AppContextValue,
  type Theme,
} from './app-context';

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
