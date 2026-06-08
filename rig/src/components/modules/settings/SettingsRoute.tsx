import { MainArea } from '@/components/shell/MainArea';
import { WatchedFoldersSettings } from '@/components/modules/f2';
import { useTools } from '@/hooks/useTools';
import { AgentConfigTab } from './AgentConfigTab';

export function SettingsRoute() {
  const { inventory } = useTools();

  const tabs = [
    {
      id:      'watched-folders',
      label:   'Watched Folders',
      content: <WatchedFoldersSettings />,
    },
    {
      id:      'agent-config',
      label:   'Agent Config',
      content: <AgentConfigTab envDeps={inventory?.env_deps ?? []} />,
    },
  ];

  return <MainArea tabs={tabs} />;
}
