import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import type { ToolsInventory, SelectedTool, ManifestScript, ScriptResult } from './types';

export function useTools() {
  const [inventory,  setInventory]  = useState<ToolsInventory | null>(null);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState<string | null>(null);
  const [selected,   setSelected]   = useState<SelectedTool | null>(null);
  const [running,    setRunning]    = useState(false);
  const [result,     setResult]     = useState<ScriptResult | null>(null);
  const [runError,   setRunError]   = useState<string | null>(null);

  useEffect(() => {
    invoke<ToolsInventory>('tools_list_inventory')
      .then(setInventory)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  const selectScript = useCallback((use_case: string, script: ManifestScript) => {
    setSelected({ kind: 'script', use_case, script });
    setResult(null);
    setRunError(null);
  }, []);

  const selectHarness = useCallback((name: string) => {
    const tool = inventory?.harness.find((t) => t.name === name);
    if (tool) {
      setSelected({ kind: 'harness', tool });
      setResult(null);
      setRunError(null);
    }
  }, [inventory]);

  const runScript = useCallback(async (
    use_case: string,
    file:     string,
    args:     string[],
  ) => {
    setRunning(true);
    setResult(null);
    setRunError(null);
    try {
      const res = await invoke<ScriptResult>('tools_run_script', {
        useCase: use_case, file, args,
      });
      setResult(res);
    } catch (e) {
      setRunError(String(e));
    } finally {
      setRunning(false);
    }
  }, []);

  const refresh = useCallback(() => {
    setLoading(true);
    setError(null);
    invoke<ToolsInventory>('tools_list_inventory')
      .then(setInventory)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return {
    inventory, loading, error,
    selected, selectScript, selectHarness,
    running, result, runError, runScript,
    refresh,
  };
}
