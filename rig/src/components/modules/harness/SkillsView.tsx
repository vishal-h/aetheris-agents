import { useMemo, useState } from 'react';
import { Blocks, ChevronDown, ChevronRight } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useSkills } from '@/hooks/useSkills';
import type { SkillDisposition, SkillRow } from '@/hooks/types';
import { cn } from '@/lib/utils';

// ── Disposition presentation ─────────────────────────────────────────────────
//
// Read-only view (m14 T7). The one thing it may not do is show a superseded or
// retired row as if it were current, so disposition drives the default filter,
// the badge, and a line in the COLLAPSED header — not just a column an operator
// has to go looking for.

type Filter = 'all' | SkillDisposition;

const DISPOSITION_BADGE: Record<SkillDisposition, { label: string; variant: 'success' | 'warning' | 'destructive' }> = {
  active:     { label: 'Active',     variant: 'success' },
  superseded: { label: 'Superseded', variant: 'warning' },
  retired:    { label: 'Retired',    variant: 'destructive' },
};

function formatTimestamp(iso: string): string {
  // The column is harness-written ISO 8601; an unparseable value is shown raw
  // rather than replaced with a plausible date.
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toISOString().replace('T', ' ').slice(0, 19);
}

// ── Field rows in the expanded panel ─────────────────────────────────────────

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      {children}
    </div>
  );
}

function Chips({ values, empty }: { values: string[]; empty: string }) {
  if (values.length === 0) {
    return <p className="text-xs text-muted-foreground italic">{empty}</p>;
  }
  return (
    <div className="flex flex-wrap gap-1">
      {values.map((v, i) => (
        <span key={`${v}-${i}`} className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
          {v}
        </span>
      ))}
    </div>
  );
}

// ── One catalogue entry ──────────────────────────────────────────────────────

function SkillCard({ row }: { row: SkillRow }) {
  const [open, setOpen] = useState(false);
  const badge = DISPOSITION_BADGE[row.disposition];
  const isActive = row.disposition === 'active';

  return (
    <div className={cn('rounded-md border', !isActive && 'border-dashed bg-muted/20')}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-start gap-2 px-3 py-2 text-left hover:bg-muted/30"
      >
        {open
          ? <ChevronDown className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
          : <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />}

        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={cn('text-sm font-medium', !isActive && 'text-muted-foreground')}>
              {row.name}
            </span>
            <Badge variant={badge.variant}>{badge.label}</Badge>
            <Badge>{row.status}</Badge>
            <Badge>{row.use_case ?? 'no scope'}</Badge>
          </div>

          {/* Why this row is not current, in the collapsed header — an operator
              scanning the list never has to expand to find out. */}
          {row.disposition === 'superseded' && (
            <p className="text-xs text-amber-700 dark:text-amber-500">
              Superseded by {row.superseded_by_name ?? '(successor not in this catalogue)'}
              {' '}
              <span className="font-mono">{row.superseded_by}</span> — read the successor, not this row.
            </p>
          )}
          {row.disposition === 'retired' && (
            <p className="text-xs text-red-700 dark:text-red-400">
              Retired by the catalogue cap — kept for reference, not offered.
            </p>
          )}
          {row.parse_errors.length > 0 && (
            <p className="text-xs text-amber-700 dark:text-amber-500">
              Unreadable JSON in: {row.parse_errors.join(', ')} — the fields below are incomplete.
            </p>
          )}

          <p className="line-clamp-2 text-xs text-muted-foreground">{row.description || '(no description)'}</p>

          <p className="text-xs text-muted-foreground tabular-nums">
            {row.step_count} step{row.step_count === 1 ? '' : 's'}
            {' · '}{row.source_run_ids.length} source run{row.source_run_ids.length === 1 ? '' : 's'}
            {' · '}{row.example_count} example{row.example_count === 1 ? '' : 's'}
            {' · '}{formatTimestamp(row.extracted_at)}
          </p>
        </div>
      </button>

      {open && (
        <div className="flex flex-col gap-4 border-t px-3 py-3">
          <Field label="Description">
            <p className="whitespace-pre-wrap break-words text-sm">
              {row.description || '(no description)'}
            </p>
          </Field>

          {/* Rendered in full, never clipped: a prompt template an operator
              cannot read end to end is the one thing this view exists to show. */}
          <Field label="Prompt template">
            {row.prompt_template
              ? (
                <pre className="whitespace-pre-wrap break-words rounded bg-muted/50 p-3 font-mono text-xs">
                  {row.prompt_template}
                </pre>
              )
              : <p className="text-xs italic text-muted-foreground">(empty)</p>}
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Tool sequence">
              <Chips values={row.tool_sequence} empty="(none recorded)" />
            </Field>
            <Field label="Source runs">
              <Chips values={row.source_run_ids} empty="(none recorded)" />
            </Field>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Identity">
              <p className="break-all font-mono text-xs text-muted-foreground">
                id {row.id}
                <br />
                hash {row.content_hash ?? '—'}
              </p>
            </Field>
            <Field label="Lifecycle">
              <p className="break-all font-mono text-xs text-muted-foreground">
                status {row.status}
                <br />
                superseded_by {row.superseded_by ?? '—'}
                <br />
                approved_by {row.approved_by ?? '—'}
                <br />
                approved_at {row.approved_at ?? '—'}
              </p>
            </Field>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Filter bar ───────────────────────────────────────────────────────────────

function FilterTab({
  active, label, count, onClick,
}: { active: boolean; label: string; count: number; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'rounded-md border px-2.5 py-1 text-xs font-medium',
        active ? 'bg-secondary text-secondary-foreground' : 'text-muted-foreground hover:bg-muted/50',
      )}
    >
      {label} <span className="tabular-nums">({count})</span>
    </button>
  );
}

// ── Main view ────────────────────────────────────────────────────────────────

export function SkillsView() {
  const { catalog, loading, error, refresh } = useSkills();
  // Active by default: the list an operator reads is the current one, and the
  // other two are one labelled click away rather than mixed in.
  const [filter,  setFilter]  = useState<Filter>('active');
  const [useCase, setUseCase] = useState<string>('all');

  const rows = useMemo<SkillRow[]>(() => catalog?.rows ?? [], [catalog]);

  const scopes = useMemo(
    () => Array.from(new Set(rows.map((r) => r.use_case ?? '(no scope)'))).sort(),
    [rows],
  );

  const visible = useMemo(
    () => rows.filter((r) =>
      (filter === 'all' || r.disposition === filter) &&
      (useCase === 'all' || (r.use_case ?? '(no scope)') === useCase)),
    [rows, filter, useCase],
  );

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Loading skills…
      </div>
    );
  }

  if (error) return <div className="p-6 text-sm text-red-600">{error}</div>;
  if (!catalog) return null;

  const counts: Record<Filter, number> = {
    all:        catalog.rows.length,
    active:     catalog.active_count,
    superseded: catalog.superseded_count,
    retired:    catalog.retired_count,
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">

      <div className="flex shrink-0 items-center justify-between border-b px-6 py-4">
        <div className="flex items-center gap-2">
          <Blocks className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-base font-semibold">Skills</h2>
        </div>
        <Button variant="outline" size="sm" onClick={refresh}>Refresh</Button>
      </div>

      <div className="flex shrink-0 flex-wrap items-center gap-2 border-b px-6 py-3">
        <FilterTab active={filter === 'active'}     label="Active"     count={counts.active}     onClick={() => setFilter('active')} />
        <FilterTab active={filter === 'superseded'} label="Superseded" count={counts.superseded} onClick={() => setFilter('superseded')} />
        <FilterTab active={filter === 'retired'}    label="Retired"    count={counts.retired}    onClick={() => setFilter('retired')} />
        <FilterTab active={filter === 'all'}        label="All"        count={counts.all}        onClick={() => setFilter('all')} />

        <span className="ml-2 text-xs text-muted-foreground">Scope</span>
        <select
          value={useCase}
          onChange={(e) => setUseCase(e.target.value)}
          className="rounded-md border bg-background px-2 py-1 text-xs"
        >
          <option value="all">all scopes</option>
          {scopes.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <div className="flex flex-1 flex-col gap-2 overflow-y-auto p-6">
        {catalog.rows.length === 0 && (
          <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
            No skills extracted yet. Run the extractor and curator to populate the catalogue.
          </div>
        )}

        {catalog.rows.length > 0 && visible.length === 0 && (
          <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
            No rows match this filter.
          </div>
        )}

        {visible.map((row) => <SkillCard key={row.id} row={row} />)}

        {visible.length > 0 && (
          <p className="pt-2 text-xs text-muted-foreground">
            Read-only. Approval is a decision recorded outside Rig (m14 q3); this view
            has no approve, edit or delete action by design.
          </p>
        )}
      </div>
    </div>
  );
}
