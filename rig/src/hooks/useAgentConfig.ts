import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { AGENT_CONFIG_DEFS } from '@/components/modules/settings/agentConfigDefs';

export function useAgentConfig() {
  const [values,  setValues]  = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    invoke<Record<string, string>>('agent_config_get_all')
      .then((v) => { setValues(v);  setLoading(false); })
      .catch((e) => { setError(String(e)); setLoading(false); });
  }, []);

  useEffect(() => { load(); }, [load]);

  const set = useCallback(async (key: string, value: string) => {
    await invoke('agent_config_set', { key, value });
    setValues((prev) => ({ ...prev, [key]: value }));
  }, []);

  const remove = useCallback(async (key: string) => {
    await invoke('agent_config_delete', { key });
    setValues((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }, []);

  const exportConfig = useCallback(async (): Promise<string> => {
    const allKeys: Record<string, string> = {};
    for (const def of AGENT_CONFIG_DEFS) {
      allKeys[def.key] = values[def.key] ?? def.placeholder ?? '';
    }
    const sorted = Object.fromEntries(
      Object.entries(allKeys).sort(([a], [b]) => a.localeCompare(b))
    );
    return JSON.stringify(sorted, null, 2);
  }, [values]);

  const importConfig = useCallback(async (json: string): Promise<number> => {
    const parsed = JSON.parse(json) as Record<string, string>;
    const count = await invoke<number>('agent_config_import', { values: parsed });
    const updated = await invoke<Record<string, string>>('agent_config_get_all');
    setValues(updated);
    return count;
  }, []);

  return { values, loading, error, set, remove, reload: load, exportConfig, importConfig };
}
