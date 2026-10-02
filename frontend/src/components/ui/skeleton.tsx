import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export interface SkeletonProps extends ComponentProps<"div"> {
  /** Accessible label announced while content loads. */
  label?: string;
}

export function Skeleton({
  className,
  label = "Loading",
  ...props
}: SkeletonProps) {
  return (
    <div
      role="status"
      aria-label={label}
      className={cn(
        "animate-pulse rounded-md bg-navy/10",
        "motion-reduce:animate-none",
        className,
      )}
      {...props}
    />
  );
}
