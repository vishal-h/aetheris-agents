import { useState } from 'react';
import { GitCompare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useRunList } from '@/hooks/useHarness';
import { useRunDiff } from '@/hooks/useRunDiff';
import type { RunSummary } from '@/hooks/types';

export function DiffView() {
  const runList = useRunList();

  const [runIdA, setRunIdA] = useState('');
  const [runIdB, setRunIdB] = useState('');
  const [comparing, setComparing] = useState(false);
  const [activeA,   setActiveA]   = useState<string | null>(null);
  const [activeB,   setActiveB]   = useState<string | null>(null);

  const { diff, loading, error } = useRunDiff(
    comparing ? activeA : null,
    comparing ? activeB : null,
  );

  function handleCompare() {
    setActiveA(runIdA);
    setActiveB(runIdB);
    setComparing(true);
  }

  function handleReset() {
    setComparing(false);
    setActiveA(null);
    setActiveB(null);
  }

  const runs = runList.data ?? [];

  // ── Selection phase ─────────────────────────────────────────────────────────
  const selectionPanel = (
    <div className="flex flex-col gap-6 max-w-xl">
      <div className="flex items-center gap-2 text-lg font-semibold">
        <GitCompare className="h-5 w-5" />
        Compare runs
      </div>

      <RunPicker
        label="Run A"
        value={runIdA}
        onChange={setRunIdA}
        runs={runs}
        exclude={runIdB}
      />
      <RunPicker
        label="Run B"
        value={runIdB}
        onChange={setRunIdB}
        runs={runs}
        exclude={runIdA}
      />

      <Button
        onClick={handleCompare}
        disabled={!runIdA || !runIdB || runIdA === runIdB}
      >
        Compare
      </Button>
    </div>
  );

  // ── Comparison phase ─────────────────────────────────────────────────────────
  if (comparing) {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
          Loading trajectories…
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-6 flex flex-col gap-3">
          <p className="text-sm text-red-600">{error}</p>
          <Button variant="outline" onClick={handleReset}>Back</Button>
        </div>
      );
    }

    if (!diff) return null;

    return (
      <div className="p-6 flex flex-col gap-6 overflow-y-auto">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-semibold">
            <GitCompare className="h-5 w-5" />
            <span className="font-mono text-sm">{activeA}</span>
            <span className="text-muted-foreground">vs</span>
            <span className="font-mono text-sm">{activeB}</span>
          </div>
          <Button variant="outline" size="sm" onClick={handleReset}>
            New comparison
          </Button>
        </div>

        {/* Metadata table */}
        <section>
          <h3 className="text-sm font-semibold mb-2">Metadata</h3>
          <div className="rounded-md border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left px-3 py-2 font-medium text-muted-foreground w-36">Field</th>
                  <th className="text-left px-3 py-2 font-medium">Run A</th>
                  <th className="text-left px-3 py-2 font-medium">Run B</th>
                </tr>
              </thead>
              <tbody>
                {diff.meta_rows.map((row) => (
                  <tr
                    key={row.field}
                    className={`border-b last:border-b-0 ${row.differs ? 'bg-amber-50' : ''}`}
                  >
                    <td className="px-3 py-2 text-muted-foreground">{row.field}</td>
                    <td className={`px-3 py-2 font-mono ${row.differs ? 'font-medium' : ''}`}>
                      {row.a}
                    </td>
                    <td className={`px-3 py-2 font-mono ${row.differs ? 'font-medium' : ''}`}>
                      {row.b}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Step path */}
        <section>
          <h3 className="text-sm font-semibold mb-2">Step path</h3>
          <div className="rounded-md border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left px-3 py-2 font-medium text-muted-foreground w-20">Step</th>
                  <th className="text-left px-3 py-2 font-medium">Run A — tools</th>
                  <th className="text-left px-3 py-2 font-medium">Run B — tools</th>
                </tr>
              </thead>
              <tbody>
                {diff.step_rows.map((row) => (
                  <tr
                    key={row.step}
                    className={`border-b last:border-b-0 ${row.differs ? 'bg-amber-50' : ''}`}
                  >
                    <td className="px-3 py-2 text-muted-foreground font-mono">{row.step}</td>
                    <td className={`px-3 py-2 font-mono text-xs ${row.only_in_b ? 'text-muted-foreground italic' : ''}`}>
                      {row.only_in_b ? '—' : (row.tools_a.join(', ') || 'no tools')}
                    </td>
                    <td className={`px-3 py-2 font-mono text-xs ${row.only_in_a ? 'text-muted-foreground italic' : ''}`}>
                      {row.only_in_a ? '—' : (row.tools_b.join(', ') || 'no tools')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    );
  }

  return <div className="p-6">{selectionPanel}</div>;
}

// ── Run picker ────────────────────────────────────────────────────────────────

interface RunPickerProps {
  label:    string;
  value:    string;
  onChange: (id: string) => void;
  runs:     RunSummary[];
  exclude:  string;
}

function RunPicker({ label, value, onChange, runs, exclude }: RunPickerProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-medium">{label}</label>
      <select
        className="rounded-md border border-input bg-background px-3 py-2 text-sm
                   focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">Select a run…</option>
        {runs
          .filter((r) => r.run_id !== exclude)
          .map((r) => (
            <option key={r.run_id} value={r.run_id}>
              {r.run_id} — {r.label} ({r.model}, {r.status})
            </option>
          ))}
      </select>
    </div>
  );
}
