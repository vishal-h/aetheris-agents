import { useEffect, useState } from 'react';
import { listen } from '@tauri-apps/api/event';
import { invoke } from '@tauri-apps/api/core';
import { ScanProgress } from './types';

export interface ScanStatus {
  scanning: boolean;
  progress: ScanProgress | null;
  triggerScan: () => Promise<void>;
}

export function useScanStatus(): ScanStatus {
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState<ScanProgress | null>(null);

  const triggerScan = async () => {
    try {
      setScanning(true);
      await invoke('f2_trigger_scan');
    } catch (error) {
      console.error('Failed to trigger scan:', error);
      setScanning(false);
      setProgress(null);
    }
  };

  useEffect(() => {
    // Listen for scan-progress events
    const progressUnlisten = listen<ScanProgress>('scan-progress', (event) => {
      setProgress(event.payload);
    });

    // Listen for scan-complete events
    const completeUnlisten = listen('scan-complete', () => {
      setScanning(false);
      setProgress(null);
    });

    // Cleanup listeners on unmount
    return () => {
      progressUnlisten.then((fn) => fn());
      completeUnlisten.then((fn) => fn());
    };
  }, []);

  return {
    scanning,
    progress,
    triggerScan,
  };
}
