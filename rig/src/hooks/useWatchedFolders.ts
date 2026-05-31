import { useEffect, useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { WatchedFolder } from './types';

export interface UseWatchedFoldersResult {
  folders: WatchedFolder[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
  addFolder: (path: string) => Promise<void>;
  toggleFolder: (id: number, enabled: boolean) => Promise<void>;
  removeFolder: (id: number) => Promise<void>;
}

export function useWatchedFolders(): UseWatchedFoldersResult {
  const [folders, setFolders] = useState<WatchedFolder[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const watchedFolders = await invoke<WatchedFolder[]>('f2_get_watched_folders');
      setFolders(watchedFolders);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
      console.error('Failed to fetch watched folders:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const addFolder = useCallback(async (path: string) => {
    try {
      await invoke('f2_add_watched_folder', { path });
      await fetchData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
      console.error('Failed to add watched folder:', err);
      throw err;
    }
  }, [fetchData]);

  const toggleFolder = useCallback(async (id: number, enabled: boolean) => {
    try {
      await invoke('f2_toggle_watched_folder', { id, enabled });
      await fetchData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
      console.error('Failed to toggle watched folder:', err);
      throw err;
    }
  }, [fetchData]);

  const removeFolder = useCallback(async (id: number) => {
    try {
      await invoke('f2_remove_watched_folder', { id });
      await fetchData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
      console.error('Failed to remove watched folder:', err);
      throw err;
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    folders,
    loading,
    error,
    refetch: fetchData,
    addFolder,
    toggleFolder,
    removeFolder,
  };
}
