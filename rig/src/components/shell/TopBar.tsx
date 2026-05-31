import { useNavigate } from 'react-router-dom';
import { Wrench, RefreshCw, Settings, Loader2, PanelRight, Sun, Moon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useApp } from '@/context/AppContext';

interface TopBarProps {
  onSync?: () => void;
  syncing?: boolean;
}

export function TopBar({ onSync, syncing = false }: TopBarProps) {
  const navigate = useNavigate();
  const { theme, setTheme, rightPanelOpen, setRightPanelOpen } = useApp();

  return (
    <div className="flex h-12 w-full items-center justify-between border-b border-border bg-background px-4">
      {/* Left: App icon + name */}
      <div className="flex items-center gap-2">
        <Wrench className="h-5 w-5 text-foreground" />
        <span className="text-base font-semibold text-foreground">Rig</span>
      </div>

      {/* Right: Sync + theme toggle + right panel toggle + Settings buttons */}
      <div className="flex items-center gap-2">
        {/* Sync button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={onSync}
          disabled={!onSync || syncing}
          aria-label={syncing ? 'Syncing...' : 'Sync'}
        >
          {syncing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
        </Button>

        {/* Theme toggle button — TODO: move to Settings panel */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>

        {/* Right panel toggle button — TODO: replace with contextual trigger in v0.2 */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setRightPanelOpen(!rightPanelOpen)}
          aria-label={rightPanelOpen ? 'Close right panel' : 'Open right panel'}
        >
          <PanelRight className="h-4 w-4" />
        </Button>

        {/* Settings button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate('/settings')}
          aria-label="Settings"
        >
          <Settings className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
