import { useTools } from '@/hooks/useTools';
import { ToolTree }   from './ToolTree';
import { ToolDetail } from './ToolDetail';

export function ToolsView() {
  const tools = useTools();

  return (
    <div className="flex flex-1 h-full overflow-hidden">
      <div className="w-64 shrink-0 border-r overflow-y-auto p-3">
        <ToolTree tools={tools} />
      </div>
      <div className="flex-1 overflow-y-auto p-6">
        <ToolDetail tools={tools} />
      </div>
    </div>
  );
}
