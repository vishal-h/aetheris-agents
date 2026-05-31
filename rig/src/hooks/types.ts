// TypeScript interfaces matching Rust structs from src-tauri/src/commands/f2.rs
// Note: Field names use snake_case to match Rust serialization

export interface WatchedFolder {
  id: number;
  path: string;
  enabled: boolean;
  ignore_globs: string | null;
  added_at: string | null;
  last_scan: string | null;
}

export interface FileEntry {
  id: number;
  path: string;
  size_bytes: number | null;
  modified_at: number | null;
  mime_type: string | null;
  sha256: string | null;
  status: string;
  last_scanned: string | null;
}

export interface DuplicateGroup {
  sha256: string;
  file_count: number;
  total_size: number;
  wasted_bytes: number;
  files: FileEntry[];
}

export interface ScanProgress {
  scanned: number;
  total_estimate: number;
  current_path: string;
  duplicates_found: number;
}

export interface DuplicateStats {
  duplicate_count: number;
  wasted_bytes: number;
}

// ============================================================================
// Provenance types — matching src-tauri/src/commands/provenance.rs
// ============================================================================

export interface CorpusSummary {
  total_files: number;
  unique_files: number;
  duplicate_files: number;
  total_size_bytes: number;
  unique_size_bytes: number;
  wasted_bytes: number;
  classified_files: number;
  migrated_files: number;
  zip_files: number;
  last_scan_at: string | null;
}

export interface ClientRow {
  client: string;
  file_count: number;
  total_size_bytes: number;
  migrated_count: number;
  doc_types: string[];
}

export interface ScanRun {
  id: string;
  root_path: string;
  status: string;
  files_scanned: number;
  duplicates_found: number;
  started_at: string;
  finished_at: string | null;
  duration_secs: number | null;
}

export interface ClassificationRow {
  path: string;
  client: string;
  financial_year: string;
  doc_type: string;
  confidence: number;
  status: string;
  raw_excerpt: string;
  classified_at: string;
  reviewed_by: string | null;
}

export interface MigrationClientRow {
  client: string;
  migrated: number;
  failed: number;
  pending: number;
}

export interface MigrationSummary {
  total: number;
  migrated: number;
  failed: number;
  pending: number;
  by_client: MigrationClientRow[];
}

export interface ZipRow {
  path: string;
  size_bytes: number;
  status: string;
  contents_count: number | null;
  new_to_corpus: number | null;
}

export interface ZipInventory {
  total: number;
  processed: number;
  encrypted: number;
  pending: number;
  failed: number;
  new_to_corpus: number;
  largest_zips: ZipRow[];
}

export interface CorpusDuplicateGroup {
  sha256: string;
  copy_count: number;
  size_each: number;
  wasted_bytes: number;
}

export interface FailedMigration {
  path: string;
  dest_path: string;
  error: string | null;
  proposed_at: string;
  migrated_at: string | null;
}

export interface EncryptedZipRow {
  path: string;
  size_bytes: number;
  parent_zip: string | null;
  depth: number;
}

// ============================================================================
// Harness types — matching src-tauri/src/commands/harness.rs
// ============================================================================

export interface HarnessStatus {
  connected:  boolean;
  db_path:    string | null;
  run_count:  number;
  error:      string | null;
}

export interface RunSummary {
  run_id:      string;
  label:       string;
  status:      'idle' | 'running' | 'paused' | 'done' | 'failed' | string;
  provider:    string;
  model:       string;
  started_at:  string;
  finished_at: string | null;
  step_count:  number;
  event_count: number;
}

export interface EventRow {
  id:          string;
  run_id:      string;
  step:        number;
  seq:         number;
  event_type:  string;
  payload:     string;
  timestamp:   string;
}

export interface RunDetail {
  run_id:      string;
  label:       string;
  status:      string;
  config:      string;
  started_at:  string;
  finished_at: string | null;
}
