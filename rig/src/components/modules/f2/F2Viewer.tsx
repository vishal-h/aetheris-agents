import { FolderTree, Tag } from 'lucide-react';
import { Tab } from '@/components/shell/TabBar';

// Placeholder component for Views tab
function ViewsPlaceholder() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <FolderTree className="h-12 w-12 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          No views yet. Files will appear here once indexed.
        </p>
      </div>
    </div>
  );
}

// Placeholder component for Labels tab
function LabelsPlaceholder() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <Tag className="h-12 w-12 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          No labels applied yet.
        </p>
      </div>
    </div>
  );
}

// F2Viewer component - defines the tabs for the Viewer view
export function F2Viewer() {
  const tabs: Tab[] = [
    {
      id: 'views',
      label: 'Views',
      content: <ViewsPlaceholder />,
    },
    {
      id: 'labels',
      label: 'Labels',
      content: <LabelsPlaceholder />,
    },
  ];

  return tabs;
}
