import { useState, useEffect, useCallback } from 'react';
import { Server, CheckSquare, Square, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  usePlaygroundStatus,
  usePlaygroundPolicy,
  usePlaygroundSandboxes,
  usePlaygroundSubmit,
  usePlaygroundRunStatus,
  usePlaygroundHistory,
  PlaygroundMruEntry,
} from '@/hooks/usePlayground';
import { PlaygroundApiError, PlaygroundSubmitRequest } from '@/hooks/types';

// ============================================================================
// Constants
// ============================================================================

const SELECT_CLASS =
  'h-9 w-full rounded-md border border-input bg-background px-3 text-sm ' +
  'outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50';

const INPUT_CLASS =
  'flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm ' +
  'outline-none focus-visible:ring-2 focus-visible:ring-ring placeholder:text-muted-foreground ' +
  'disabled:opacity-50';

const TEXTAREA_CLASS =
  'flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ' +
  'outline-none focus-visible:ring-2 focus-visible:ring-ring placeholder:text-muted-foreground ' +
  'disabled:opacity-50 resize-y';

// ============================================================================
// Not-connected state — shows playground-specific error
// ============================================================================

interface PlaygroundNotConnectedProps {
  error: string | null;
}

function PlaygroundNotConnected({ error }: PlaygroundNotConnectedProps) {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="flex flex-col items-center gap-3 text-center max-w-md">
        <Server className="h-12 w-12 text-muted-foreground" />
        <p className="text-sm font-medium">Playground API not connected.</p>
        {error ? (
          <p className="text-sm text-muted-foreground font-mono bg-muted rounded px-3 py-2 text-left w-full">
            {error}
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">
            Set <code className="rounded bg-muted px-1">PLAYGROUND_API_URL</code> and{' '}
            <code className="rounded bg-muted px-1">PLAYGROUND_API_TOKEN</code> and restart.
          </p>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Tools checklist
// ============================================================================

interface ToolsChecklistProps {
  available: string[];
  selected:  string[];
  onChange:  (selected: string[]) => void;
}

function ToolsChecklist({ available, selected, onChange }: ToolsChecklistProps) {
  const toggle = useCallback((tool: string) => {
    if (selected.includes(tool)) {
      onChange(selected.filter((t) => t !== tool));
    } else {
      onChange([...selected, tool]);
    }
  }, [selected, onChange]);

  if (available.length === 0) {
    return <p className="text-xs text-muted-foreground">No tools available.</p>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {available.map((tool) => {
        const checked = selected.includes(tool);
        return (
          <button
            key={tool}
            type="button"
            onClick={() => toggle(tool)}
            className="flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs transition-colors hover:bg-muted"
            aria-pressed={checked}
          >
            {checked
              ? <CheckSquare className="h-3.5 w-3.5 text-primary" />
              : <Square className="h-3.5 w-3.5 text-muted-foreground" />}
            {tool}
          </button>
        );
      })}
    </div>
  );
}

// ============================================================================
// Violation list
// ============================================================================

interface ViolationsProps {
  errorString: string;
}

function ViolationList({ errorString }: ViolationsProps) {
  // Attempt to parse as PlaygroundApiError with violations array.
  // Fall back to raw string display for non-422 errors.
  let parsed: PlaygroundApiError | null = null;
  try {
    const candidate = JSON.parse(errorString) as PlaygroundApiError;
    if (
      candidate &&
      typeof candidate === 'object' &&
      'error' in candidate &&
      candidate.error &&
      typeof candidate.error === 'object'
    ) {
      parsed = candidate;
    }
  } catch {
    // not JSON — fall through to raw display
  }

  if (parsed && parsed.error.violations && parsed.error.violations.length > 0) {
    return (
      <div className="rounded-md border border-destructive/40 bg-destructive/5 p-3 space-y-2">
        <p className="text-sm font-medium text-destructive">Policy violations:</p>
        <ul className="space-y-1">
          {parsed.error.violations.map((v, i) => (
            <li key={i} className="text-xs text-destructive">
              <span className="font-medium">{v.field}</span>
              {' — '}
              {v.message}
            </li>
          ))}
        </ul>
      </div>
    );
  }

  // Non-422 or non-structured error: show message directly
  const message = parsed ? parsed.error.message : errorString;
  return (
    <div className="rounded-md border border-destructive/40 bg-destructive/5 p-3">
      <p className="text-sm text-destructive">{message}</p>
    </div>
  );
}

// ============================================================================
// Run status panel — on-demand only, no background polling
// ============================================================================

interface RunStatusPanelProps {
  runId: string;
}

function RunStatusPanel({ runId }: RunStatusPanelProps) {
  const status = usePlaygroundRunStatus(runId);

  return (
    <div className="rounded-md border bg-muted/30 p-3 space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-muted-foreground">
          Run submitted: <span className="font-mono text-foreground">{runId}</span>
        </p>
        <Button variant="outline" size="sm" onClick={status.refetch} disabled={status.loading}>
          {status.loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Check status'}
        </Button>
      </div>
      {status.error && (
        <p className="text-xs text-destructive">{status.error}</p>
      )}
      {status.data && (
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <Badge variant={
            status.data.status === 'done'    ? 'success'     :
            status.data.status === 'running' ? 'warning'     :
            status.data.status === 'failed'  ? 'destructive' : 'default'
          }>
            {status.data.status}
          </Badge>
          <span className="text-muted-foreground">
            steps: {status.data.step_count}
          </span>
          {status.data.label && (
            <span className="text-muted-foreground truncate max-w-xs" title={status.data.label}>
              {status.data.label}
            </span>
          )}
          {status.data.finished_at && (
            <span className="text-muted-foreground">
              finished: {new Date(status.data.finished_at).toLocaleString()}
            </span>
          )}
        </div>
      )}
      <p className="text-xs text-muted-foreground">
        View full trajectory in the{' '}
        <span className="font-medium text-foreground">Harness → Runs</span> tab.
      </p>
    </div>
  );
}

// ============================================================================
// Recent submissions (MRU list)
// ============================================================================

interface MruListProps {
  history: PlaygroundMruEntry[];
}

function MruList({ history }: MruListProps) {
  if (history.length === 0) return null;

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-muted-foreground">Recent submissions</p>
      <div className="space-y-1">
        {history.map((entry) => (
          <div
            key={entry.run_id}
            className="flex items-center justify-between rounded-md border px-3 py-2 text-xs"
          >
            <div className="flex flex-col gap-0.5 min-w-0">
              <span className="font-mono text-foreground truncate" title={entry.run_id}>
                {entry.run_id}
              </span>
              {entry.label && (
                <span className="text-muted-foreground truncate" title={entry.label}>
                  {entry.label}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 shrink-0 ml-3">
              <span className="text-muted-foreground">
                {entry.provider} / {entry.model.split('/').pop() ?? entry.model}
              </span>
              <span className="text-muted-foreground">
                {new Date(entry.submitted_at).toLocaleString()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// Composer form
// ============================================================================

function ComposerForm() {
  const policy    = usePlaygroundPolicy();
  const sandboxes = usePlaygroundSandboxes();
  const { submit, loading: submitting, error: submitError, clearError } = usePlaygroundSubmit();
  const { history, add: addToHistory } = usePlaygroundHistory();

  // --- Form state ---
  const [provider,       setProvider]       = useState('');
  const [model,          setModel]          = useState('');
  const [sandboxId,      setSandboxId]      = useState('');
  const [systemPrompt,   setSystemPrompt]   = useState('');
  const [userPrompt,     setUserPrompt]     = useState('');
  const [label,          setLabel]          = useState('');
  const [selectedTools,  setSelectedTools]  = useState<string[]>([]);
  const [maxSteps,       setMaxSteps]       = useState('');
  const [maxSpawnDepth,  setMaxSpawnDepth]  = useState('');
  const [maxTokens,      setMaxTokens]      = useState('');
  const [temperature,    setTemperature]    = useState('');
  const [topP,           setTopP]           = useState('');
  const [contextStrategy, setContextStrategy] = useState('');
  const [submittedRunId, setSubmittedRunId] = useState<string | null>(null);

  // Seed form defaults from policy once loaded
  useEffect(() => {
    if (!policy.data) return;
    const { providers, defaults, tools } = policy.data;

    if (providers.length > 0 && !provider) {
      setProvider(providers[0]);
    }

    if (defaults.tools && defaults.tools.length > 0 && selectedTools.length === 0) {
      setSelectedTools(defaults.tools);
    } else if (tools.length > 0 && selectedTools.length === 0) {
      setSelectedTools([]);
    }

    if (defaults.max_steps != null && !maxSteps) {
      setMaxSteps(String(defaults.max_steps));
    }

    if (defaults.max_spawn_depth != null && !maxSpawnDepth) {
      setMaxSpawnDepth(String(defaults.max_spawn_depth));
    }

    if (defaults.context_strategy && !contextStrategy) {
      setContextStrategy(defaults.context_strategy);
    }

    if (defaults.user_prompt && !userPrompt) {
      setUserPrompt(defaults.user_prompt);
    }
  // We only want to seed once on policy load, not on every form-state change
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [policy.data]);

  // Reset model when provider changes
  useEffect(() => {
    setModel('');
  }, [provider]);

  // Seed first model when provider + policy are available
  useEffect(() => {
    if (!policy.data || !provider) return;
    const models = policy.data.models[provider] ?? [];
    if (models.length > 0) {
      setModel(models[0]);
    }
  }, [provider, policy.data]);

  // Seed first sandbox when sandboxes are loaded
  useEffect(() => {
    if (!sandboxes.data) return;
    if (sandboxes.data.sandboxes.length > 0 && !sandboxId) {
      setSandboxId(sandboxes.data.sandboxes[0].id);
    }
  }, [sandboxes.data, sandboxId]);

  const availableModels = policy.data?.models[provider] ?? [];
  const availableTools  = policy.data?.tools ?? [];
  const caps            = policy.data?.caps;

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setSubmittedRunId(null);

    const request: PlaygroundSubmitRequest = {
      sandbox_id:    sandboxId,
      provider,
      model,
      system_prompt: systemPrompt,
    };

    if (userPrompt.trim())          request.user_prompt      = userPrompt;
    if (selectedTools.length > 0)   request.tools            = selectedTools;
    if (label.trim())               request.label            = label;
    if (maxSteps.trim())            request.max_steps        = parseInt(maxSteps, 10);
    if (maxSpawnDepth.trim())       request.max_spawn_depth  = parseInt(maxSpawnDepth, 10);
    if (maxTokens.trim())           request.max_tokens       = parseInt(maxTokens, 10);
    if (temperature.trim())         request.temperature      = parseFloat(temperature);
    if (topP.trim())                request.top_p            = parseFloat(topP);
    if (contextStrategy.trim())     request.context_strategy = contextStrategy;

    try {
      const result = await submit(request);
      setSubmittedRunId(result.run_id);

      const entry: PlaygroundMruEntry = {
        run_id:       result.run_id,
        label:        label.trim() || model,
        provider,
        model,
        submitted_at: new Date().toISOString(),
      };
      addToHistory(entry);
    } catch {
      // error is surfaced via submitError from usePlaygroundSubmit
    }
  }, [
    sandboxId, provider, model, systemPrompt, userPrompt, selectedTools,
    label, maxSteps, maxSpawnDepth, maxTokens, temperature, topP,
    contextStrategy, submit, addToHistory, clearError,
  ]);

  if (policy.loading || sandboxes.loading) {
    return (
      <div className="p-4 space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-10 animate-pulse rounded bg-muted" />
        ))}
      </div>
    );
  }

  if (policy.error) {
    return (
      <div className="p-6">
        <p className="text-sm text-destructive">Failed to load policy: {policy.error}</p>
      </div>
    );
  }

  if (sandboxes.error) {
    return (
      <div className="p-6">
        <p className="text-sm text-destructive">Failed to load sandboxes: {sandboxes.error}</p>
      </div>
    );
  }

  return (
    <div className="flex h-full overflow-y-auto">
      <div className="w-full max-w-2xl mx-auto p-6 space-y-6">

        {/* Submitted run result */}
        {submittedRunId && (
          <RunStatusPanel runId={submittedRunId} />
        )}

        {/* Submit error / violations */}
        {submitError && (
          <ViolationList errorString={submitError} />
        )}

        <form onSubmit={handleSubmit} className="space-y-5">

          {/* Label */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium" htmlFor="pg-label">
              Label <span className="text-muted-foreground font-normal">(optional)</span>
            </label>
            <input
              id="pg-label"
              className={INPUT_CLASS}
              placeholder="e.g. playground-haiku-echo"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
            />
          </div>

          {/* Provider + Model row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium" htmlFor="pg-provider">Provider</label>
              <select
                id="pg-provider"
                className={SELECT_CLASS}
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                required
              >
                {(policy.data?.providers ?? []).map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium" htmlFor="pg-model">Model</label>
              <select
                id="pg-model"
                className={SELECT_CLASS}
                value={model}
                onChange={(e) => setModel(e.target.value)}
                required
              >
                {availableModels.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Sandbox */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium" htmlFor="pg-sandbox">Sandbox</label>
            <select
              id="pg-sandbox"
              className={SELECT_CLASS}
              value={sandboxId}
              onChange={(e) => setSandboxId(e.target.value)}
              required
            >
              {(sandboxes.data?.sandboxes ?? []).map((s) => (
                <option key={s.id} value={s.id}>{s.id}{s.description ? ` — ${s.description}` : ''}</option>
              ))}
            </select>
          </div>

          {/* System prompt */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium" htmlFor="pg-system">System prompt</label>
            <textarea
              id="pg-system"
              className={TEXTAREA_CLASS}
              placeholder="You are a helpful assistant…"
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              required
              rows={4}
            />
          </div>

          {/* User prompt */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium" htmlFor="pg-user">
              User prompt <span className="text-muted-foreground font-normal">(optional)</span>
            </label>
            <textarea
              id="pg-user"
              className={TEXTAREA_CLASS}
              placeholder="Initial user message…"
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              rows={3}
            />
          </div>

          {/* Tools */}
          {availableTools.length > 0 && (
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Tools</label>
              <ToolsChecklist
                available={availableTools}
                selected={selectedTools}
                onChange={setSelectedTools}
              />
            </div>
          )}

          {/* Numeric caps */}
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium" htmlFor="pg-max-steps">
                Max steps
                {caps?.max_steps != null && (
                  <span className="ml-1 text-xs text-muted-foreground font-normal">
                    (cap {caps.max_steps})
                  </span>
                )}
              </label>
              <input
                id="pg-max-steps"
                type="number"
                min="1"
                max={caps?.max_steps ?? undefined}
                className={INPUT_CLASS}
                placeholder="default"
                value={maxSteps}
                onChange={(e) => setMaxSteps(e.target.value)}
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium" htmlFor="pg-max-depth">
                Max spawn depth
                {caps?.max_spawn_depth != null && (
                  <span className="ml-1 text-xs text-muted-foreground font-normal">
                    (cap {caps.max_spawn_depth})
                  </span>
                )}
              </label>
              <input
                id="pg-max-depth"
                type="number"
                min="0"
                max={caps?.max_spawn_depth ?? undefined}
                className={INPUT_CLASS}
                placeholder="default"
                value={maxSpawnDepth}
                onChange={(e) => setMaxSpawnDepth(e.target.value)}
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium" htmlFor="pg-max-tokens">
                Max tokens
                {caps?.max_tokens != null && (
                  <span className="ml-1 text-xs text-muted-foreground font-normal">
                    (cap {caps.max_tokens})
                  </span>
                )}
              </label>
              <input
                id="pg-max-tokens"
                type="number"
                min="1"
                max={caps?.max_tokens ?? undefined}
                className={INPUT_CLASS}
                placeholder="default"
                value={maxTokens}
                onChange={(e) => setMaxTokens(e.target.value)}
              />
            </div>
          </div>

          {/* Sampling params */}
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium" htmlFor="pg-temperature">
                Temperature <span className="text-muted-foreground font-normal">(optional)</span>
              </label>
              <input
                id="pg-temperature"
                type="number"
                min="0"
                max="2"
                step="0.01"
                className={INPUT_CLASS}
                placeholder="e.g. 0.7"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium" htmlFor="pg-top-p">
                Top P <span className="text-muted-foreground font-normal">(optional)</span>
              </label>
              <input
                id="pg-top-p"
                type="number"
                min="0"
                max="1"
                step="0.01"
                className={INPUT_CLASS}
                placeholder="e.g. 0.9"
                value={topP}
                onChange={(e) => setTopP(e.target.value)}
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium" htmlFor="pg-context-strategy">
                Context strategy <span className="text-muted-foreground font-normal">(optional)</span>
              </label>
              <input
                id="pg-context-strategy"
                className={INPUT_CLASS}
                placeholder="e.g. rolling"
                value={contextStrategy}
                onChange={(e) => setContextStrategy(e.target.value)}
              />
            </div>
          </div>

          {/* Submit */}
          <div className="pt-2">
            <Button
              type="submit"
              disabled={submitting || !provider || !model || !sandboxId || !systemPrompt.trim()}
              className="w-full"
            >
              {submitting ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Submitting…
                </span>
              ) : (
                'Submit run'
              )}
            </Button>
          </div>
        </form>

        {/* MRU list below the form */}
        <MruList history={history} />
      </div>
    </div>
  );
}

// ============================================================================
// PlaygroundView — connection gate + composer
// ============================================================================

export function PlaygroundView() {
  const status = usePlaygroundStatus();

  // While loading connection status, show nothing (avoids flashing form).
  if (status.loading && !status.data) {
    return (
      <div className="p-4 space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-10 animate-pulse rounded bg-muted" />
        ))}
      </div>
    );
  }

  // Connection gate: show error state, not the form, when not connected.
  if (!status.data?.connected) {
    return <PlaygroundNotConnected error={status.data?.error ?? status.error} />;
  }

  return <ComposerForm />;
}
