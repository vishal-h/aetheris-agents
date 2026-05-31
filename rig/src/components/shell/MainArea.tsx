import { useState, useEffect } from 'react';
import { Tabs, TabsContent } from '@/components/ui/tabs';
import { TabBar, Tab } from './TabBar';
import { cn } from '@/lib/utils';

interface MainAreaProps {
  tabs?: Tab[];
}

export function MainArea({ tabs }: MainAreaProps) {
  const [activeTab, setActiveTab] = useState<string | undefined>(undefined);

  // Reset to first tab when tabs prop changes
  useEffect(() => {
    if (tabs && tabs.length > 0) {
      setActiveTab(tabs[0].id);
    } else {
      setActiveTab(undefined);
    }
  }, [tabs]);

  // If no tabs, show empty state
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
        {/* Tab bar at the top */}
        <TabBar tabs={tabs} />

        {/* Tab content area - scrollable */}
        <div className="flex-1 overflow-y-auto">
          {tabs.map((tab) => (
            <TabsContent
              key={tab.id}
              value={tab.id}
              className={cn(
                "h-full p-4 m-0 ring-offset-0 focus-visible:ring-0"
              )}
            >
              {tab.content}
            </TabsContent>
          ))}
        </div>
      </Tabs>
    </div>
  );
}
