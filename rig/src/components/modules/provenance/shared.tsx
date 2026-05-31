import { Server, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function NotConnected() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="flex flex-col items-center gap-3 text-center">
        <Server className="h-12 w-12 text-muted-foreground" />
        <p className="text-sm font-medium">Corpus not connected.</p>
        <p className="text-sm text-muted-foreground">
          Set <code className="rounded bg-muted px-1">PROVENANCE_DB_PATH</code> to the corpus DuckDB path and restart.
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

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <AlertCircle className="h-10 w-10 text-destructive" />
        <p className="text-sm text-muted-foreground">{message}</p>
        <Button variant="outline" size="sm" onClick={onRetry}>Retry</Button>
      </div>
    </div>
  );
}
