import { Tab } from '@/components/shell/TabBar';
import { useFileIndex } from '@/hooks/useFileIndex';
import { IndexTable } from './IndexTable';
import { DuplicatesTab } from './DuplicatesTab';

// Index tab content with real data
function IndexContent() {
  const { entries, loading, error, refetch } = useFileIndex();

  return (
    <IndexTable
      entries={entries}
      loading={loading}
      error={error}
      refetch={refetch}
    />
  );
}

// F2Operations component - defines the tabs for the Operations view
export function F2Operations() {
  const tabs: Tab[] = [
    {
      id: 'duplicates',
      label: 'Duplicates',
      content: <DuplicatesTab />,
    },
    {
      id: 'index',
      label: 'Index',
      content: <IndexContent />,
    },
  ];

  return tabs;
}
