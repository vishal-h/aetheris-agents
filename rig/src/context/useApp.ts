import { useContext } from 'react';

import { AppContext, type AppContextValue } from './app-context';

// Access the app context. Extracted from AppContext.tsx so that file exports
// only the <AppProvider> component (react-refresh/only-export-components,
// BL-018 #69).
export function useApp(): AppContextValue {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
