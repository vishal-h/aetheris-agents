// Custom React hooks for Tauri commands
export { useFileIndex } from './useFileIndex';
export { useDuplicates } from './useDuplicates';
export { useWatchedFolders } from './useWatchedFolders';
export { useScanStatus } from './useScanStatus';
export { useProvenanceStatus } from './useProvenanceStatus';
export { useCorpusSummary, useClientBreakdown, useScanRuns, useDuplicateGroups } from './useCorpusOverview';

// Type exports
export type {
  WatchedFolder,
  FileEntry,
  DuplicateGroup,
  ScanProgress,
  DuplicateStats,
  CorpusSummary,
  ClientRow,
  ScanRun,
  ClassificationRow,
  MigrationClientRow,
  MigrationSummary,
  ZipRow,
  ZipInventory,
  CorpusDuplicateGroup,
} from './types';

export type { UseFileIndexResult } from './useFileIndex';
export type { UseDuplicatesResult } from './useDuplicates';
export type { UseWatchedFoldersResult } from './useWatchedFolders';
export type { ScanStatus } from './useScanStatus';
export type { UseProvenanceStatusResult } from './useProvenanceStatus';

export { useHarnessStatus, useRunList, useRunEvents, useRunDetail } from './useHarness';
export type { HarnessStatus, RunSummary, EventRow, RunDetail } from './types';
export type { TrajectoryMeta, TrajectoryEvent, TrajectoryFile } from './types';
export type { PlanStep, OrchestratorPlan, PollResult, OrchestratorPhase, StepStatus } from './types';
export { useOrchestrator } from './useOrchestrator';
export { useTrajectory } from './useTrajectory';
export type { MetaDiffRow, StepDiffEntry, RunDiff } from './types';
export { useRunDiff } from './useRunDiff';
export { useCapabilityMatrix } from './useCapabilityMatrix';
export type { MatrixAgent, MatrixScript, MatrixUseCase, CapabilityMatrix } from './types';
