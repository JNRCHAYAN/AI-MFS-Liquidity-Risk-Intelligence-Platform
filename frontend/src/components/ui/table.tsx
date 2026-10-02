import type { ComponentProps, ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface TableProps extends ComponentProps<"table"> {
  /** Accessible name for the scrollable region that wraps the table. */
  captionLabel: string;
}

/**
 * Large tables scroll horizontally inside a labelled, focusable region so the
 * page itself never overflows and keyboard users can reach the scroll area.
 */
export function Table({
  captionLabel,
  className,
  children,
  ...props
}: TableProps) {
  return (
    <div
      role="region"
      aria-label={captionLabel}
      tabIndex={0}
      className="w-full overflow-x-auto rounded-card border border-border"
    >
      <table
        className={cn("w-full min-w-[36rem] border-collapse text-sm", className)}
        {...props}
      >
        {children}
      </table>
    </div>
  );
}

export function TableHeader({ className, ...props }: ComponentProps<"thead">) {
  return <thead className={cn("bg-canvas", className)} {...props} />;
}

export function TableBody({ className, ...props }: ComponentProps<"tbody">) {
  return <tbody className={className} {...props} />;
}

export function TableRow({ className, ...props }: ComponentProps<"tr">) {
  return (
    <tr
      className={cn("border-b border-border last:border-0", className)}
      {...props}
    />
  );
}

export function TableHead({ className, ...props }: ComponentProps<"th">) {
  return (
    <th
      scope="col"
      className={cn(
        "px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted",
        className,
      )}
      {...props}
    />
  );
}

export function TableCell({ className, ...props }: ComponentProps<"td">) {
  return <td className={cn("px-4 py-3 align-top", className)} {...props} />;
}

export function TableCaption({
  className,
  children,
  ...props
}: ComponentProps<"caption"> & { children: ReactNode }) {
  return (
    <caption
      className={cn("px-4 py-2 text-left text-xs text-muted", className)}
      {...props}
    >
      {children}
    </caption>
  );
}
