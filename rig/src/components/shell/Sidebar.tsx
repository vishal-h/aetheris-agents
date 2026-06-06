import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Activity,
  FolderSearch,
  GitCompare,
  Library,
  ScanSearch,
  ListTree,
  LayoutDashboard,
  BarChart2,
  ClipboardCheck,
  ChevronDown,
  Plus,
  Sparkles,
  TrendingUp,
  Wrench,
  type LucideIcon,
} from 'lucide-react';
import { modules } from '@/modules/registry';
import { useApp } from '@/context/AppContext';
import { cn } from '@/lib/utils';

// Icon resolution map - maps string icon names to lucide-react components
const iconMap: Record<string, LucideIcon> = {
  Activity,
  FolderSearch,
  GitCompare,
  Library,
  ScanSearch,
  LayoutTree: ListTree,
  LayoutDashboard,
  BarChart2,
  ClipboardCheck,
  Plus,
  Sparkles,
  TrendingUp,
  Wrench,
};

export function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setActiveSidebarItem } = useApp();

  // Track expanded state for each module section (all expanded by default)
  const [expandedModules, setExpandedModules] = useState<Record<string, boolean>>(
    () => {
      const initial: Record<string, boolean> = {};
      modules.forEach((module) => {
        initial[module.id] = true; // Expanded by default
      });
      return initial;
    }
  );

  // Toggle module section expansion
  const toggleModule = (moduleId: string) => {
    setExpandedModules((prev) => ({
      ...prev,
      [moduleId]: !prev[moduleId],
    }));
  };

  // Handle sidebar item click
  const handleItemClick = (itemId: string, path: string) => {
    setActiveSidebarItem(itemId);
    navigate(path);
  };

  // Derive active state from current URL path
  const isItemActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <aside className="w-60 h-full flex flex-col bg-sidebar border-r border-border">
      {/* Module sections */}
      <div className="flex-1 overflow-y-auto">
        {modules.map((module) => {
          const ModuleIcon = iconMap[module.icon];
          const isExpanded = expandedModules[module.id];

          return (
            <div key={module.id} className="border-b border-border/50">
              {/* Module header */}
              <button
                onClick={() => toggleModule(module.id)}
                className="w-full flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-sidebar-foreground hover:bg-muted/50 transition-colors"
                aria-expanded={isExpanded}
              >
                {ModuleIcon && <ModuleIcon className="size-4 shrink-0" />}
                <span className="flex-1 text-left">{module.label}</span>
                <ChevronDown
                  className={cn(
                    'size-4 shrink-0 transition-transform duration-200',
                    isExpanded ? 'rotate-0' : '-rotate-90'
                  )}
                />
              </button>

              {/* Module sub-items */}
              {isExpanded && (
                <div className="pb-2">
                  {module.sections.map((section) => {
                    const SectionIcon = iconMap[section.icon];
                    const active = isItemActive(section.path);

                    return (
                      <button
                        key={section.id}
                        onClick={() => handleItemClick(section.id, section.path)}
                        className={cn(
                          'w-full flex items-center gap-2 px-4 py-2 pl-10 text-sm transition-colors',
                          active
                            ? 'bg-accent text-accent-foreground font-medium'
                            : 'text-sidebar-foreground/80 hover:bg-muted/50 hover:text-sidebar-foreground'
                        )}
                      >
                        {SectionIcon && <SectionIcon className="size-4 shrink-0" />}
                        <span>{section.label}</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Divider and + Module placeholder */}
      <div className="border-t border-border">
        <button
          disabled
          className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-muted-foreground opacity-50 cursor-not-allowed"
        >
          <Plus className="size-4 shrink-0" />
          <span>Module</span>
        </button>
      </div>
    </aside>
  );
}
