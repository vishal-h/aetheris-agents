import { useEffect, useState } from 'react';
import { Download, Eye, EyeOff, ExternalLink, Upload, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAgentConfig } from '@/hooks/useAgentConfig';
import { AGENT_CONFIG_DEFS } from './agentConfigDefs';

// ── Single config row ─────────────────────────────────────────────────────────

interface ConfigRowProps {
  label:        string;
  envKey:       string;
  masked:       boolean;
  placeholder:  string | undefined;
  linkPrefix?:  string;
  value:        string | undefined;
  onSave:       (key: string, value: string) => void;
  onClear:      (key: string) => void;
}

function ConfigRow({ label, envKey, masked, placeholder, linkPrefix, value, onSave, onClear }: ConfigRowProps) {
  const [draft,   setDraft]   = useState(value ?? '');
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setDraft(value ?? '');
  }, [value]);

  const isSet   = value !== undefined && value !== '';
  const isDirty = draft !== (value ?? '');

  return (
    <div className="flex items-center gap-3 py-2.5 border-b last:border-b-0">
      <div className="w-40 shrink-0">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground font-mono">{envKey}</p>
      </div>

      <div className="flex-1 relative">
        <input
          type={masked && !visible ? 'password' : 'text'}
          className="w-full rounded-md border border-input bg-background px-3 py-1.5 pr-8
                     text-sm font-mono focus-visible:outline-none
                     focus-visible:ring-2 focus-visible:ring-ring"
          placeholder={isSet ? '••••••••' : (placeholder ?? 'Not set')}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
        {masked && (
          <button
            type="button"
            className="absolute right-2 top-1/2 -translate-y-1/2
                       text-muted-foreground hover:text-foreground transition-colors"
            onClick={() => setVisible((v) => !v)}
          >
            {visible
              ? <EyeOff className="h-3.5 w-3.5" />
              : <Eye    className="h-3.5 w-3.5" />}
          </button>
        )}
      </div>

      <div className="flex gap-1 shrink-0 items-center">
        {linkPrefix && isSet && value && (
          <a
            href={`${linkPrefix}${value}`}
            target="_blank"
            rel="noreferrer"
            className="shrink-0 text-muted-foreground hover:text-foreground
                       transition-colors"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        )}
        {isDirty && draft !== '' && (
          <Button size="sm" onClick={() => { onSave(envKey, draft); }}>
            Save
          </Button>
        )}
        {isSet && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { onClear(envKey); setDraft(''); }}
          >
            <X className="h-3.5 w-3.5" />
          </Button>
        )}
      </div>
    </div>
  );
}

// ── Group section ─────────────────────────────────────────────────────────────

function ConfigGroup({
  group,
  defs,
  values,
  onSave,
  onClear,
}: {
  group:   string;
  defs:    typeof AGENT_CONFIG_DEFS;
  values:  Record<string, string>;
  onSave:  (key: string, value: string) => void;
  onClear: (key: string) => void;
}) {
  return (
    <section className="mb-6">
      <h3 className="text-xs font-semibold uppercase tracking-wide
                     text-muted-foreground mb-2">{group}</h3>
      <div className="rounded-md border">
        {defs.map((def) => (
          <ConfigRow
            key={def.key}
            label={def.label}
            envKey={def.key}
            masked={def.masked}
            placeholder={def.placeholder}
            linkPrefix={def.linkPrefix}
            value={values[def.key]}
            onSave={onSave}
            onClear={onClear}
          />
        ))}
      </div>
    </section>
  );
}

// ── Main tab ──────────────────────────────────────────────────────────────────

export function AgentConfigTab() {
  const { values, loading, error, set, remove, exportConfig, importConfig } = useAgentConfig();
  const [importMessage, setImportMessage] = useState<string | null>(null);
  const [exporting,     setExporting]     = useState(false);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32
                      text-muted-foreground text-sm">
        Loading…
      </div>
    );
  }

  if (error) {
    return <div className="p-4 text-sm text-red-600">{error}</div>;
  }

  async function handleExport() {
    setExporting(true);
    const json = await exportConfig();
    const blob = new Blob([json], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = 'agent-config.json';
    a.click();
    URL.revokeObjectURL(url);
    setTimeout(() => setExporting(false), 2000);
  }

  async function handleImport() {
    const input   = document.createElement('input');
    input.type    = 'file';
    input.accept  = '.json,application/json';
    input.onchange = async () => {
      const file = input.files?.[0];
      if (!file) return;
      const text = await file.text();
      try {
        const count = await importConfig(text);
        setImportMessage(`${count} value${count !== 1 ? 's' : ''} imported.`);
        setTimeout(() => setImportMessage(null), 3000);
      } catch (e) {
        setImportMessage(`Import failed: ${String(e)}`);
      }
    };
    input.click();
  }

  const groups = Array.from(new Set(AGENT_CONFIG_DEFS.map((d) => d.group)));

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">

        <div className="rounded-md border border-amber-200 bg-amber-50
                        px-4 py-3 text-xs text-amber-800 mb-6">
          Values are stored in plaintext on disk in the app data directory.
          Do not store production credentials on shared machines.
        </div>

        <div className="flex gap-2 mb-6">
          <Button variant="outline" size="sm" onClick={handleExport} disabled={exporting}>
            <Download className="h-3.5 w-3.5 mr-1.5" />
            {exporting ? 'Exported' : 'Export'}
          </Button>
          <Button variant="outline" size="sm" onClick={handleImport}>
            <Upload className="h-3.5 w-3.5 mr-1.5" />
            Import
          </Button>
          {importMessage && (
            <span className="text-xs text-muted-foreground self-center">
              {importMessage}
            </span>
          )}
        </div>

        {groups.map((group) => (
          <ConfigGroup
            key={group}
            group={group}
            defs={AGENT_CONFIG_DEFS.filter((d) => d.group === group)}
            values={values}
            onSave={set}
            onClear={remove}
          />
        ))}

      </div>
    </div>
  );
}
