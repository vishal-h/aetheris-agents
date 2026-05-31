import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, ChevronRight, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useCapabilityMatrix } from '@/hooks/useCapabilityMatrix';
import type { MatrixUseCase, MatrixAgent, MatrixScript } from '@/hooks/types';

// ── Tool badge ────────────────────────────────────────────────────────────────
function ToolBadge({ tool }: { tool: string }) {
  return (
    <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
      {tool}
    </span>
  );
}

// ── Agent row ─────────────────────────────────────────────────────────────────
interface AgentRowProps {
  agent:    MatrixAgent;
  onLaunch: (agent: MatrixAgent) => void;
}

function AgentRow({ agent, onLaunch }: AgentRowProps) {
  return (
    <div className="flex items-start gap-3 px-4 py-3 border-b last:border-b-0 hover:bg-muted/30 transition-colors">
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{agent.label}</p>
        <p className="text-xs text-muted-foreground font-mono mt-0.5">{agent.file}</p>
        <div className="flex flex-wrap gap-1 mt-1.5">
          {agent.tools.map((t) => <ToolBadge key={t} tool={t} />)}
        </div>
      </div>
      <Button
        variant="outline"
        size="sm"
        className="shrink-0 mt-0.5"
        onClick={() => onLaunch(agent)}
      >
        <Play className="h-3.5 w-3.5 mr-1.5" />
        Run
      </Button>
    </div>
  );
}

// ── Script row ────────────────────────────────────────────────────────────────
function ScriptRow({ script }: { script: MatrixScript }) {
  return (
    <div className="flex items-start gap-3 px-4 py-2.5 border-b last:border-b-0">
      <div className="flex-1 min-w-0">
        <p className="text-xs font-mono text-foreground">{script.file}</p>
        <p className="text-xs text-muted-foreground mt-0.5">{script.purpose}</p>
      </div>
    </div>
  );
}

// ── Use case section ──────────────────────────────────────────────────────────
function UseCaseSection({
  useCase,
  onLaunch,
}: {
  useCase:  MatrixUseCase;
  onLaunch: (agent: MatrixAgent) => void;
}) {
  const [open, setOpen] = useState(true);

  return (
    <div className="border rounded-md mb-3">
      <button
        className="w-full flex items-center gap-2 px-4 py-3 text-left hover:bg-muted/50 transition-colors font-medium text-sm"
        onClick={() => setOpen((o) => !o)}
      >
        {open
          ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
          : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
        {useCase.title}
        <span className="ml-2 text-xs text-muted-foreground font-normal">
          {useCase.agents.length} agent{useCase.agents.length !== 1 ? 's' : ''}
          {useCase.scripts.length > 0
            ? `, ${useCase.scripts.length} script${useCase.scripts.length !== 1 ? 's' : ''}`
            : ''}
        </span>
      </button>

      {open && (
        <div className="border-t">
          {useCase.agents.length > 0 && (
            <div>
              <p className="px-4 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide bg-muted/30 border-b">
                Agents
              </p>
              {useCase.agents.map((a) => (
                <AgentRow key={`${a.file}-${a.label}`} agent={a} onLaunch={onLaunch} />
              ))}
            </div>
          )}

          {useCase.scripts.length > 0 && (
            <div className={useCase.agents.length > 0 ? 'border-t' : ''}>
              <p className="px-4 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide bg-muted/30 border-b">
                Scripts
              </p>
              {useCase.scripts.map((s) => (
                <ScriptRow key={s.file} script={s} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main view ─────────────────────────────────────────────────────────────────
export function CapabilityMatrixView() {
  const { matrix, loading, error } = useCapabilityMatrix();
  const navigate = useNavigate();

  function handleLaunch(agent: MatrixAgent) {
    navigate('/orchestrator', { state: { prefill: `${agent.label}: ` } });
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        Loading capability matrix…
      </div>
    );
  }

  if (error) {
    return <div className="p-6 text-sm text-red-600">{error}</div>;
  }

  if (!matrix) return null;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="px-6 py-4 border-b shrink-0">
        <h2 className="text-base font-semibold">Capability Matrix</h2>
        {matrix.generated_at && (
          <p className="text-xs text-muted-foreground mt-0.5">{matrix.generated_at}</p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {matrix.use_cases.map((uc) => (
          <UseCaseSection key={uc.title} useCase={uc} onLaunch={handleLaunch} />
        ))}
      </div>
    </div>
  );
}
