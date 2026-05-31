import { TabsList, TabsTrigger } from '@/components/ui/tabs';

export interface Tab {
  id: string;
  label: string;
  content: React.ReactNode;
  disabled?: boolean;
}

interface TabBarProps {
  tabs: Tab[];
}

export function TabBar({ tabs }: TabBarProps) {
  return (
    <TabsList className="w-full justify-start rounded-none border-b border-border bg-background h-12 p-0">
      {tabs.map((tab) => (
        <TabsTrigger
          key={tab.id}
          value={tab.id}
          disabled={tab.disabled}
          className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-3 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {tab.label}
        </TabsTrigger>
      ))}
    </TabsList>
  );
}
