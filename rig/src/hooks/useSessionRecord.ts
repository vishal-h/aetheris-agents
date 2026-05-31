import { useState } from 'react';

export function useSessionRecord(key: string, defaultValue: boolean) {
  const stored = sessionStorage.getItem(key);
  const [state, setState] = useState<Record<string, boolean>>(
    stored ? (JSON.parse(stored) as Record<string, boolean>) : {}
  );

  function get(label: string): boolean {
    return state[label] ?? defaultValue;
  }

  function set(label: string, value: boolean) {
    const next = { ...state, [label]: value };
    setState(next);
    sessionStorage.setItem(key, JSON.stringify(next));
  }

  function setAll(labels: string[], value: boolean) {
    const next = Object.fromEntries(labels.map((l) => [l, value]));
    setState(next);
    sessionStorage.setItem(key, JSON.stringify(next));
  }

  return { get, set, setAll };
}
