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
  run_id:         string;
  label:          string;
  status:         'idle' | 'running' | 'paused' | 'done' | 'failed' | string;
  provider:       string;
  model:          string;
  started_at:     string;
  finished_at:    string | null;
  step_count:     number;
  event_count:    number;
  last_event_at:  string | null;
  total_cost_usd: number | null;
}

export interface EventRow {
  id:          string;
  run_id:      string;
  step:        number;
  seq:         number;
  event_type:  string;
  /** Raw JSON string from SQLite payload_json column — parse before use. */
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

// ============================================================================
// Trajectory types — matching commands/trajectory.rs
// ============================================================================

export interface TrajectoryMeta {
  model:           string;
  provider:        string;
  mode:            string;
  step_count:      number;
  max_steps:       number;
  started_at:      string;
  /** Empty string when the run was interrupted before completion (Rust unwrap_or default). */
  finished_at:     string;
  tools:           string[];
  system_prompt:   string;
  user_prompt:     string;
  /** `config.sandbox_path` — `Map.get(map, "sandbox_path")` with no default and a
   *  `nil` config default (run_config.ex:171,88), so null whenever unset. Verified:
   *  null in 22,726 / 23,729 dev-store artifacts (e.g. every fresh-overlay fork). */
  sandbox_path:    string | null;
  /** Harness writes `config.seed` (an integer or nil) — server.ex:668,939. */
  seed:            number | null;
  overlay_changes: unknown[];
  /** Only present when true — written by the harness for resumed runs. */
  resumed?:        boolean;
  /** Only present on forked runs — server.ex:720 `maybe_add_fork_meta` writes
   *  `fork_from`/`fork_step` together (or omits both). `fork_from`, when present, is
   *  always a non-nil string (the nil guard at server.ex:717). `fork_step` carries
   *  `config.fork_step` (`non_neg_integer() | nil`, run_config.ex:197), so its value
   *  may be null; the banner guards for that. */
  fork_from?:      string;
  fork_step?:      number | null;
}

export interface TrajectoryEvent {
  id:          string;
  run_id:      string;
  seq:         number;
  step:        number;
  event_type:  string;
  /** Inlined JSON object from the trajectory file — NOT a raw string (contrast with EventRow.payload). */
  payload:     Record<string, unknown>;
  timestamp:   string;
}

/**
 * Shape of TrajectoryEvent.payload / parsed EventRow.payload
 * when event_type === 'llm_responded'.
 *
 * Cast opt-in: `event.payload as LlmRespondedPayload`.
 * input_tokens / output_tokens / cost_usd are null for stub/Ollama runs
 * or pre-instrumentation Anthropic runs.
 */
export interface LlmRespondedPayload {
  response_type:      string;
  resolved_model:     string | null;
  input_tokens:       number | null;
  output_tokens:      number | null;
  cost_usd:           number | null;
  latency_ms:         number;
  tool_name?:         string | null;
  tool_input?:        Record<string, unknown> | null;
  raw_response:       string | null;
  system_fingerprint: string | null;
}

export interface TrajectoryFile {
  run_id:         string;
  schema_version: string;
  meta:           TrajectoryMeta;
  events:         TrajectoryEvent[];
}

// ============================================================================
// Diff types — p4-002
// ============================================================================

export interface MetaDiffRow {
  field:   string;
  a:       string;
  b:       string;
  differs: boolean;
}

export interface StepDiffEntry {
  step:      number;
  tools_a:   string[];
  tools_b:   string[];
  differs:   boolean;
  only_in_a: boolean;
  only_in_b: boolean;
}

export interface RunDiff {
  meta_rows:   MetaDiffRow[];
  step_rows:   StepDiffEntry[];
  any_differs: boolean;
}

// ============================================================================
// Orchestrator types — matching protocol.md
// ============================================================================

export interface PlanStep {
  id:          string;
  agent:       string;
  description: string;
  context?:    string;
}

export interface OrchestratorPlan {
  type:    'plan';
  request: string;
  steps:   PlanStep[];
  params?: Record<string, string>;
}

export interface PollResult {
  messages: Record<string, unknown>[];
  done:     boolean;
}

export type OrchestratorPhase =
  | 'idle'
  | 'planning'
  | 'plan_ready'
  | 'executing'
  | 'done'
  | 'cancelled'
  | 'error';

export type StepStatus = 'pending' | 'running' | 'done' | 'failed';

// ============================================================================
// Capability matrix types — matching commands/capability_matrix.rs
// ============================================================================

export interface MatrixAgent {
  file:  string;
  label: string;
  tools: string[];
}

export interface MatrixScript {
  file:    string;
  purpose: string;
}

export interface MatrixUseCase {
  title:   string;
  agents:  MatrixAgent[];
  scripts: MatrixScript[];
}

export interface CapabilityMatrix {
  use_cases:    MatrixUseCase[];
  generated_at: string | null;
}

// ============================================================================
// Token / cost summary — p6-001
// ============================================================================

export interface TokenSummary {
  input_tokens:  number | null;
  output_tokens: number | null;
  cost_usd:      number | null;
  llm_calls:     number;
}

// ============================================================================
// Usage stats — p6-002
// ============================================================================

export interface ModelUsageRow {
  model:          string;
  run_count:      number;
  input_tokens:   number;
  output_tokens:  number;
  total_cost_usd: number;
  avg_cost_usd:   number;
}

export interface UseCaseUsageRow {
  use_case:       string;
  run_count:      number;
  total_cost_usd: number;
}

// ============================================================================
// Agent config — p7-001
// ============================================================================

export interface AgentConfigEntry {
  key:          string;
  label:        string;
  group:        string;
  masked:       boolean;
  placeholder?: string;
  linkPrefix?:  string;
  value?:       string;
}

export interface UsageStats {
  total_cost_usd:      number;
  total_runs:          number;
  instrumented_runs:   number;
  total_input_tokens:  number;
  total_output_tokens: number;
  by_model:            ModelUsageRow[];
  by_use_case:         UseCaseUsageRow[];
}

// ============================================================================
// Tools inventory — p4-002
// ============================================================================

export interface EnvDep {
  key:         string;
  label:       string;
  group:       string;
  masked:      boolean;
  placeholder: string;
}

export interface ManifestArg {
  name:        string;
  flag?:       string;
  arg_type:    string;
  required:    boolean;
  default:     string | null;
  description: string;
}

export interface ManifestScript {
  name:        string;
  file:        string;
  description: string;
  args:        ManifestArg[];
  output:      'json' | 'text' | 'files';
  example:     string;
  undeclared?: boolean;
  env?:        EnvDep[];
}

export interface UseCaseGroup {
  use_case:    string;
  description: string;
  scripts:     ManifestScript[];
}

export interface HarnessToolArg {
  name:        string;
  arg_type:    string;
  required:    boolean;
  description: string;
}

export interface HarnessTool {
  name:        string;
  description: string;
  args:        HarnessToolArg[];
  notes:       string | null;
}

export interface McpTool {
  server_id:    string;
  server_label: string;
  name:         string;
  description:  string;
  input_schema: Record<string, unknown> | null;
  auth:         string;
  notes:        string | null;
}

export interface McpServerGroup {
  server_id:    string;
  server_label: string;
  auth:         string;
  notes:        string | null;
  tools:        McpTool[];
  reachable:    boolean;
}

export interface ToolsInventory {
  use_cases: UseCaseGroup[];
  harness:   HarnessTool[];
  mcp:       McpTool[];
  env_deps:  EnvDep[];
}

export interface ScriptResult {
  stdout:    string;
  stderr:    string;
  exit_code: number;
}

export interface McpCallResult {
  content:  unknown;
  is_error: boolean;
}

export type SelectedTool =
  | { kind: 'script';  use_case: string; script: ManifestScript }
  | { kind: 'harness'; tool: HarnessTool }
  | { kind: 'mcp';     tool: McpTool };

// ============================================================================
// Playground types — matching src-tauri/src/commands/playground.rs
// Token is never present in any of these types (read server-side in Rust only).
// ============================================================================

export interface PlaygroundStatus {
  connected: boolean;
  api_url:   string | null;
  error:     string | null;
}

export interface PolicyCaps {
  max_steps:        number | null;
  max_spawn_depth:  number | null;
  max_tokens:       number | null;
  max_prompt_chars: number | null;
}

export interface PolicyDefaults {
  max_steps:        number | null;
  max_spawn_depth:  number | null;
  context_strategy: string | null;
  tools:            string[] | null;
  user_prompt:      string | null;
}

export interface PlaygroundPolicy {
  providers: string[];
  models:    Record<string, string[]>;
  tools:     string[];
  caps:      PolicyCaps;
  defaults:  PolicyDefaults;
}

export interface SandboxEntry {
  id:          string;
  description: string;
}

export interface PlaygroundSandboxes {
  sandboxes: SandboxEntry[];
}

export interface PlaygroundSubmitRequest {
  sandbox_id:        string;
  provider:          string;
  model:             string;
  system_prompt:     string;
  user_prompt?:      string;
  tools?:            string[];
  max_steps?:        number;
  max_spawn_depth?:  number;
  max_tokens?:       number;
  label?:            string;
  context_strategy?: string;
  max_context_steps?: number;
  temperature?:      number;
  top_p?:            number;
}

export interface PlaygroundSubmitResult {
  run_id: string;
}

export interface PlaygroundRunStatus {
  run_id:      string;
  status:      string;
  step_count:  number;
  started_at:  string;
  finished_at: string | null;
  label:       string | null;
}

/** Structured error body returned by the API on 422 policy violations. */
export interface PlaygroundApiError {
  error: {
    code:        string;
    message:     string;
    violations?: PlaygroundViolation[];
  };
}

export interface PlaygroundViolation {
  field:   string;
  code:    string;
  message: string;
}
