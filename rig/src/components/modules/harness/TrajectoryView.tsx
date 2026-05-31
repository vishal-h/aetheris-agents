import { useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { ChevronDown, ChevronRight, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTrajectory } from '@/hooks/useTrajectory';
import type { TrajectoryEvent } from '@/hooks/types';

const EVENT_COLOURS: Record<string, string> = {
  prompt_built:           'bg-blue-100 text-blue-800',
  llm_called:             'bg-purple-100 text-purple-800',
  llm_responded:          'bg-violet-100 text-violet-800',
  tool_called:            'bg-amber-100 text-amber-800',
  tool_result:            'bg-orange-100 text-orange-800',
  step_complete:          'bg-green-100 text-green-800',
  run_complete:           'bg-green-200 text-green-900',
  error:                  'bg-red-100 text-red-800',
  agent_message_sent:     'bg-sky-100 text-sky-800',
  agent_message_received: 'bg-sky-100 text-sky-800',
};

function eventColour(type: string): string {
  return EVENT_COLOURS[type] ?? 'bg-muted text-muted-foreground';
}

function EventRow({ event }: { event: TrajectoryEvent }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b last:border-b-0">
      <button
        className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-muted/50 transition-colors"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="text-xs font-mono text-muted-foreground w-8 shrink-0">
          {event.seq}
        </span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${eventColour(event.event_type)}`}>
          {event.event_type}
        </span>
        <span className="text-xs text-muted-foreground ml-auto shrink-0">
          {new Date(event.timestamp).toISOString().replace('T', ' ').slice(0, 23)}
        </span>
        {open
          ? <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0" />
          : <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />}
      </button>
      {open && (
        <pre className="px-4 py-3 text-xs font-mono bg-muted/30 overflow-x-auto whitespace-pre-wrap break-all">
          {JSON.stringify(event.payload, null, 2)}
        </pre>
      )}
    </div>
  );
}

function StepGroup({ step, events }: { step: number; events: TrajectoryEvent[] }) {
  const [open, setOpen] = useState(true);

  return (
    <div className="border rounded-md mb-2">
      <button
        className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-muted/50 transition-colors font-medium text-sm"
        onClick={() => setOpen((o) => !o)}
      >
        {open
          ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
          : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
        Step {step}
        <span className="ml-2 text-xs text-muted-foreground font-normal">
          {events.length} event{events.length !== 1 ? 's' : ''}
        </span>
      </button>
      {open && (
        <div className="border-t">
          {events.map((e) => <EventRow key={e.id} event={e} />)}
        </div>
      )}
    </div>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2">
      <span className="text-muted-foreground shrink-0 w-24">{label}</span>
      <span className="font-mono truncate">{value}</span>
    </div>
  );
}

function ExpandableText({ label, text }: { label: string; text: string }) {
  const [open, setOpen] = useState(false);
  const preview = text?.slice(0, 120);

  return (
    <div className="mb-1">
      <button
        className="text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
        onClick={() => setOpen((o) => !o)}
      >
        {open
          ? <ChevronDown className="h-3 w-3" />
          : <ChevronRight className="h-3 w-3" />}
        {label}
      </button>
      {open
        ? <pre className="mt-1 text-xs font-mono bg-muted/30 rounded p-2 whitespace-pre-wrap break-all">{text}</pre>
        : <p className="mt-0.5 text-xs text-muted-foreground truncate">{preview}{text?.length > 120 ? '…' : ''}</p>
      }
    </div>
  );
}

interface Props {
  runId: string | null;
}

export function TrajectoryView({ runId }: Props) {
  const { trajectory, loading, error } = useTrajectory(runId);
  const [metaOpen, setMetaOpen] = useState(true);

  if (!runId) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        Select a run to view its trajectory.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        Loading…
      </div>
    );
  }

  if (error) {
    return <div className="p-4 text-sm text-red-600">{error}</div>;
  }

  if (!trajectory) return null;

  const { meta, events } = trajectory;

  const steps = events.reduce<Map<number, TrajectoryEvent[]>>((acc, e) => {
    const group = acc.get(e.step) ?? [];
    group.push(e);
    acc.set(e.step, group);
    return acc;
  }, new Map());

  const duration = meta.started_at && meta.finished_at
    ? Math.round(
        (new Date(meta.finished_at).getTime() - new Date(meta.started_at).getTime()) / 1000
      )
    : null;

  async function handleExport() {
    try {
      await invoke('trajectory_export', { runId: trajectory!.run_id });
    } catch (e) {
      console.error('export failed', e);
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Meta panel */}
      <div className="border-b shrink-0">
        <div className="flex items-center justify-between px-4 py-2">
          <button
            className="flex items-center gap-2 text-sm font-medium hover:text-foreground text-muted-foreground transition-colors"
            onClick={() => setMetaOpen((o) => !o)}
          >
            {metaOpen
              ? <ChevronDown className="h-4 w-4" />
              : <ChevronRight className="h-4 w-4" />}
            Run metadata
          </button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-3.5 w-3.5 mr-1.5" />
            Export JSON
          </Button>
        </div>

        {metaOpen && (
          <div className="px-4 pb-3 grid grid-cols-2 gap-x-8 gap-y-1 text-xs">
            <MetaRow label="Model"    value={meta.model} />
            <MetaRow label="Provider" value={meta.provider} />
            <MetaRow label="Mode"     value={meta.mode} />
            <MetaRow label="Steps"    value={`${meta.step_count} / ${meta.max_steps}`} />
            {duration !== null &&
              <MetaRow label="Duration" value={`${duration}s`} />}
            <MetaRow label="Tools" value={meta.tools.join(', ') || '—'} />
            <div className="col-span-2 mt-1">
              <ExpandableText label="System prompt" text={meta.system_prompt} />
            </div>
            <div className="col-span-2">
              <ExpandableText label="User prompt" text={meta.user_prompt} />
            </div>
          </div>
        )}
      </div>

      {/* Event stream */}
      <div className="flex-1 overflow-y-auto p-4">
        {Array.from(steps.entries())
          .sort(([a], [b]) => a - b)
          .map(([step, evts]) => (
            <StepGroup key={step} step={step} events={evts} />
          ))}
      </div>
    </div>
  );
}
