import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { DuplicateGroup as DuplicateGroupType } from '@/hooks/types';
import { formatBytes, formatDate } from '@/lib/utils';

interface DuplicateGroupProps {
  group: DuplicateGroupType;
}

export function DuplicateGroup({ group }: DuplicateGroupProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Find the file to keep (oldest by modified_at)
  const fileToKeep = group.files.reduce((oldest, current) => {
    if (!oldest.modified_at) return current;
    if (!current.modified_at) return oldest;
    return current.modified_at < oldest.modified_at ? current : oldest;
  });

  // Truncate hash to 12 characters
  const truncateHash = (hash: string): string => {
    return hash.substring(0, 12);
  };

  // Extract last 2 path segments for display
  const getShortPath = (fullPath: string): string => {
    const segments = fullPath.split('/').filter(Boolean);
    if (segments.length <= 2) return fullPath;
    return '.../' + segments.slice(-2).join('/');
  };

  return (
    <div className="border rounded-lg bg-card">
      {/* Header - clickable to expand/collapse */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
          <div className="flex flex-col items-start gap-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-muted-foreground">
                {truncateHash(group.sha256)}
              </span>
              <span className="text-xs text-muted-foreground">•</span>
              <span className="text-sm text-muted-foreground">
                {formatBytes(group.files[0].size_bytes)}
              </span>
            </div>
            <span className="text-sm text-foreground">
              {group.file_count} copies ({formatBytes(group.wasted_bytes)} wasted)
            </span>
          </div>
        </div>
      </button>

      {/* Expanded file list */}
      {isExpanded && (
        <div className="border-t">
          <div className="px-4 py-2 bg-muted/30">
            <div className="grid grid-cols-[1fr_auto] gap-4 text-xs font-medium text-muted-foreground">
              <div>Path</div>
              <div>Modified</div>
            </div>
          </div>
          <div className="divide-y">
            {group.files.map((file) => (
              <div
                key={file.id}
                className="px-4 py-2 grid grid-cols-[1fr_auto] gap-4 items-center text-sm hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span
                    className="font-mono truncate"
                    title={file.path}
                  >
                    {getShortPath(file.path)}
                  </span>
                  {file.id === fileToKeep.id && (
                    <span className="text-xs text-muted-foreground border rounded px-1 py-0.5 whitespace-nowrap">
                      Keep
                    </span>
                  )}
                </div>
                <div className="tabular-nums text-muted-foreground whitespace-nowrap">
                  {formatDate(file.modified_at)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
