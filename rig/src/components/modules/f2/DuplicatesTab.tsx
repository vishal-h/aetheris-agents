import { useMemo } from 'react';
import { ScanSearch, AlertCircle } from 'lucide-react';
import { useDuplicates } from '@/hooks/useDuplicates';
import { formatBytes } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { DuplicateGroup } from './DuplicateGroup';

export function DuplicatesTab() {
  const { groups, loading, error, refetch } = useDuplicates();

  // Calculate total wasted space
  const totalWasted = useMemo(() => {
    return groups.reduce((sum, group) => sum + group.wasted_bytes, 0);
  }, [groups]);

  // Error state
  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <p className="text-sm text-muted-foreground">
            Failed to load duplicates: {error}
          </p>
          <Button variant="outline" onClick={refetch}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="flex h-full flex-col">
        <div className="border-b p-4">
          <div className="h-8 w-64 animate-pulse rounded bg-muted" />
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-20 animate-pulse rounded bg-muted" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Empty state
  if (groups.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <ScanSearch className="h-12 w-12 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            No duplicates found. Add a watched folder and click Sync.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Summary bar */}
      <div className="border-b p-4">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-foreground">
            {groups.length} duplicate group{groups.length !== 1 ? 's' : ''}
          </span>
          <span className="text-muted-foreground">—</span>
          <span className="text-muted-foreground">
            {formatBytes(totalWasted)} wasted
          </span>
        </div>
      </div>

      {/* Duplicate groups list */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-3">
          {groups.map((group) => (
            <DuplicateGroup key={group.sha256} group={group} />
          ))}
        </div>
      </div>
    </div>
  );
}
