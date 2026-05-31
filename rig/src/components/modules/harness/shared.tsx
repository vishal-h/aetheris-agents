import { Server } from 'lucide-react';

export function NotConnected() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="flex flex-col items-center gap-3 text-center">
        <Server className="h-12 w-12 text-muted-foreground" />
        <p className="text-sm font-medium">Not connected to Aetheris harness.</p>
        <p className="text-sm text-muted-foreground">
          Set <code className="rounded bg-muted px-1">AETHERIS_DB_PATH</code> to the path of
          aetheris/priv/aetheris.db and restart.
        </p>
      </div>
    </div>
  );
}

export function LoadingShell({ rows = 5 }: { rows?: number }) {
  return (
    <div className="p-4 space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-10 animate-pulse rounded bg-muted" />
      ))}
    </div>
  );
}
