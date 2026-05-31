import { useState, useEffect } from 'react';
import { Tabs, TabsContent } from '@/components/ui/tabs';
import { TabBar, Tab } from './TabBar';
import { cn } from '@/lib/utils';

interface MainAreaProps {
  tabs?: Tab[];
  activeTab?: string;
  onTabChange?: (id: string) => void;
}

export function MainArea({ tabs, activeTab: controlledTab, onTabChange }: MainAreaProps) {
  const [internalTab, setInternalTab] = useState<string>(tabs?.[0]?.id ?? '');

  // In uncontrolled mode, reset to first tab when the tabs array changes (route navigation).
  // In controlled mode the parent owns the active tab — skip this effect.
  useEffect(() => {
    if (controlledTab !== undefined) return;
    setInternalTab(tabs?.[0]?.id ?? '');
  }, [tabs, controlledTab]);

  const activeTab  = controlledTab ?? internalTab;
  const setActiveTab = onTabChange ?? setInternalTab;

  if (!tabs || tabs.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center h-full bg-background">
        <p className="text-sm text-muted-foreground">
          Select an item from the sidebar
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col h-full bg-background">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-col h-full">
        <TabBar tabs={tabs} />
        <div className="flex-1 overflow-y-auto">
          {tabs.map((tab) => (
            <TabsContent
              key={tab.id}
              value={tab.id}
              className={cn('h-full p-4 m-0 ring-offset-0 focus-visible:ring-0')}
            >
              {tab.content}
            </TabsContent>
          ))}
        </div>
      </Tabs>
    </div>
  );
}
