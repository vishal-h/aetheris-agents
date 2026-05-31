import { useState } from 'react';
import { Folder, Plus, Trash2, AlertCircle } from 'lucide-react';
import { useWatchedFolders } from '@/hooks/useWatchedFolders';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';

export function WatchedFoldersSettings() {
  const { folders, loading, error, addFolder, toggleFolder, removeFolder } = useWatchedFolders();
  const [newPath, setNewPath] = useState('');
  const [addError, setAddError] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);

  const handleAddFolder = async () => {
    if (!newPath.trim()) return;

    setIsAdding(true);
    setAddError(null);

    try {
      await addFolder(newPath.trim());
      setNewPath('');
    } catch (err) {
      setAddError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemoveFolder = async (id: number, path: string) => {
    const confirmed = window.confirm(
      `Are you sure you want to remove the watched folder?\n\n${path}`
    );

    if (confirmed) {
      try {
        await removeFolder(id);
      } catch (err) {
        // Error is already set in the hook
        console.error('Failed to remove folder:', err);
      }
    }
  };

  const handleToggleFolder = async (id: number, currentEnabled: boolean) => {
    try {
      await toggleFolder(id, !currentEnabled);
    } catch (err) {
      // Error is already set in the hook
      console.error('Failed to toggle folder:', err);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && newPath.trim()) {
      handleAddFolder();
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex h-full flex-col p-6">
        <div className="mb-6 space-y-2">
          <div className="h-6 w-48 animate-pulse rounded bg-muted" />
          <div className="h-4 w-96 animate-pulse rounded bg-muted" />
        </div>
        <div className="space-y-4">
          <div className="h-10 w-full animate-pulse rounded bg-muted" />
          <div className="h-16 animate-pulse rounded bg-muted" />
          <div className="h-16 animate-pulse rounded bg-muted" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Watched Folders</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Add folders to monitor for file indexing and duplicate detection.
        </p>
      </div>

      {/* Add Folder Section */}
      <div className="mb-6 space-y-3">
        <div className="space-y-2">
          <Label htmlFor="folder-path">Add Folder</Label>
          <div className="flex gap-2">
            <Input
              id="folder-path"
              type="text"
              placeholder="/path/to/folder"
              value={newPath}
              onChange={(e) => setNewPath(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isAdding}
              className="flex-1"
            />
            <Button
              onClick={handleAddFolder}
              disabled={!newPath.trim() || isAdding}
              size="default"
            >
              <Plus className="mr-1.5" />
              Add
            </Button>
          </div>
        </div>

        {/* Add error message */}
        {addError && (
          <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{addError}</span>
          </div>
        )}

        {/* Global error message */}
        {error && !addError && (
          <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Watched Folders List */}
      <div className="flex-1 overflow-y-auto">
        {folders.length === 0 ? (
          <div className="flex h-48 items-center justify-center rounded-md border border-dashed">
            <div className="flex flex-col items-center gap-2 text-center">
              <Folder className="h-10 w-10 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                No watched folders. Add a folder path above to start scanning.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            {folders.map((folder) => (
              <div
                key={folder.id}
                className="flex items-center justify-between rounded-md border bg-background p-4 transition-colors hover:bg-muted/50"
              >
                {/* Left: Folder icon and path */}
                <div className="flex min-w-0 flex-1 items-center gap-3">
                  <Folder className="h-5 w-5 shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-mono text-sm" title={folder.path}>
                      {folder.path}
                    </p>
                    {folder.last_scan && (
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        Last scanned: {new Date(folder.last_scan).toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>

                {/* Right: Toggle and Remove button */}
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <Label
                      htmlFor={`folder-${folder.id}-enabled`}
                      className="text-sm text-muted-foreground"
                    >
                      Enabled
                    </Label>
                    <Switch
                      id={`folder-${folder.id}-enabled`}
                      checked={folder.enabled}
                      onCheckedChange={() => handleToggleFolder(folder.id, folder.enabled)}
                    />
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleRemoveFolder(folder.id, folder.path)}
                    title="Remove folder"
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
