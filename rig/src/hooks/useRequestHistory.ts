import { useState, useCallback } from 'react';

const STORAGE_KEY = 'rig:orchestrator:history';
const MAX_STORED  = 20;

export function useRequestHistory() {
  const [history, setHistory] = useState<string[]>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as string[]) : [];
    } catch {
      return [];
    }
  });

  const add = useCallback((request: string) => {
    setHistory((prev) => {
      const deduped = [request, ...prev.filter((r) => r !== request)].slice(0, MAX_STORED);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(deduped));
      return deduped;
    });
  }, []);

  return { history, add };
}
