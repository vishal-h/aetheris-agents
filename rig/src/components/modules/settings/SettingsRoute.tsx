import { MainArea } from '@/components/shell/MainArea';
import { WatchedFoldersSettings } from '@/components/modules/f2';
import { AgentConfigTab } from './AgentConfigTab';

export function SettingsRoute() {
  const tabs = [
    {
      id:      'watched-folders',
      label:   'Watched Folders',
      content: <WatchedFoldersSettings />,
    },
    {
      id:      'agent-config',
      label:   'Agent Config',
      content: <AgentConfigTab />,
    },
  ];

  return <MainArea tabs={tabs} />;
}
