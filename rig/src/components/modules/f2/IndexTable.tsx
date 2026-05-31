import { useState, useMemo } from 'react';
import { Database, Search, AlertCircle } from 'lucide-react';
import { FileEntry } from '@/hooks/types';
import { formatBytes, formatDate } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface IndexTableProps {
  entries: FileEntry[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function IndexTable({ entries, loading, error, refetch }: IndexTableProps) {
  const [searchQuery, setSearchQuery] = useState('');

  // Client-side filtering by path
  const filteredEntries = useMemo(() => {
    if (!searchQuery.trim()) return entries;
    const query = searchQuery.toLowerCase();
    return entries.filter((entry) =>
      entry.path.toLowerCase().includes(query)
    );
  }, [entries, searchQuery]);

  // Extract last 2 path segments for display
  const getShortPath = (fullPath: string): string => {
    const segments = fullPath.split('/').filter(Boolean);
    if (segments.length <= 2) return fullPath;
    return '.../' + segments.slice(-2).join('/');
  };

  // Truncate hash to 12 characters
  const truncateHash = (hash: string | null): string => {
    if (!hash) return '—';
    return hash.substring(0, 12);
  };

  // Get status badge variant
  const getStatusVariant = (status: string): "default" | "warning" | "destructive" => {
    switch (status) {
      case 'duplicate':
        return 'warning';
      case 'missing':
        return 'destructive';
      default:
        return 'default';
    }
  };

  // Error state
  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <p className="text-sm text-muted-foreground">
            Failed to load file index: {error}
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
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded bg-muted" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Empty state
  if (entries.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Database className="h-12 w-12 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            No files indexed yet. Add a watched folder and click Sync.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Search bar */}
      <div className="border-b p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by path..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          />
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 border-b bg-background">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                Path
              </th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                Size
              </th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                Modified
              </th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                Type
              </th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                Hash
              </th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredEntries.map((entry) => (
              <tr
                key={entry.id}
                className="border-b transition-colors hover:bg-muted/50"
              >
                <td
                  className="px-4 py-3 font-mono"
                  title={entry.path}
                >
                  {getShortPath(entry.path)}
                </td>
                <td className="px-4 py-3 tabular-nums">
                  {formatBytes(entry.size_bytes)}
                </td>
                <td className="px-4 py-3 tabular-nums">
                  {formatDate(entry.modified_at)}
                </td>
                <td className="px-4 py-3 text-muted-foreground">
                  {entry.mime_type || '—'}
                </td>
                <td
                  className="px-4 py-3 font-mono text-xs text-muted-foreground"
                  title={entry.sha256 || undefined}
                >
                  {truncateHash(entry.sha256)}
                </td>
                <td className="px-4 py-3">
                  <Badge variant={getStatusVariant(entry.status)}>
                    {entry.status}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* No results message */}
        {filteredEntries.length === 0 && searchQuery && (
          <div className="flex items-center justify-center py-12">
            <p className="text-sm text-muted-foreground">
              No files match "{searchQuery}"
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
