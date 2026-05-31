import { X } from "lucide-react";
import { useApp } from "@/context/AppContext";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface RightPanelProps {
  title?: string;
  children: React.ReactNode;
}

export function RightPanel({ title, children }: RightPanelProps) {
  const { rightPanelOpen, setRightPanelOpen } = useApp();

  if (!rightPanelOpen) {
    return null;
  }

  return (
    <div
      className={cn(
        "w-80 border-l border-border bg-background",
        "transition-all duration-200",
        "flex flex-col"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between h-12 px-4 border-b border-border">
        {title && (
          <h2 className="text-sm font-medium text-foreground">{title}</h2>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setRightPanelOpen(false)}
          className="ml-auto"
        >
          <X className="size-4" />
        </Button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-auto p-4">
        {children}
      </div>
    </div>
  );
}
