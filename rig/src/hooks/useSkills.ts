import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import type { SkillCatalog } from './types';

export function useSkills() {
  const [catalog, setCatalog] = useState<SkillCatalog | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    invoke<SkillCatalog>('skills_catalog_load')
      .then((c) => { setCatalog(c); setLoading(false); })
      .catch((e) => { setError(String(e)); setLoading(false); });
  }

  useEffect(() => { load(); }, []);

  return { catalog, loading, error, refresh: load };
}
