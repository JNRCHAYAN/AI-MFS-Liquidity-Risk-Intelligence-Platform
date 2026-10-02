"use client";

import type { ReactNode } from "react";
import { ServerCrash } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface ErrorStateProps {
  title?: string;
  description: string;
  onRetry?: () => void;
  retryLabel?: string;
  action?: ReactNode;
  className?: string;
}

export function ErrorState({
  title = "Something went wrong",
  description,
  onRetry,
  retryLabel = "Try again",
  action,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-center gap-3 rounded-card border border-risk-high/30 bg-surface p-8 text-center",
        className,
      )}
    >
      <ServerCrash aria-hidden="true" className="size-8 text-risk-high" />
      <div className="space-y-1">
        <p className="text-sm font-semibold text-navy">{title}</p>
        <p className="text-sm text-muted">{description}</p>
      </div>
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          {retryLabel}
        </Button>
      ) : null}
      {action}
    </div>
  );
}
