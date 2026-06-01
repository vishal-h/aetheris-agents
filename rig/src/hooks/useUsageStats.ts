import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import type { UsageStats } from './types';

export function useUsageStats() {
  const [stats,   setStats]   = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    invoke<UsageStats>('usage_stats_load')
      .then((s) => { setStats(s);  setLoading(false); })
      .catch((e) => { setError(String(e)); setLoading(false); });
  }

  useEffect(() => { load(); }, []);

  return { stats, loading, error, refresh: load };
}
