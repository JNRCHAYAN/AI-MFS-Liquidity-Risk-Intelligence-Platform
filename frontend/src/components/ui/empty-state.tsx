import type { ReactNode } from "react";
import { Inbox, type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

export interface EmptyStateProps {
  title: string;
  description: string;
  Icon?: LucideIcon;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  description,
  Icon = Inbox,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-3 rounded-card border border-dashed border-border-strong bg-surface p-8 text-center",
        className,
      )}
    >
      <Icon aria-hidden="true" className="size-8 text-muted" />
      <div className="space-y-1">
        <p className="text-sm font-semibold text-navy">{title}</p>
        <p className="text-sm text-muted">{description}</p>
      </div>
      {action}
    </div>
  );
}
