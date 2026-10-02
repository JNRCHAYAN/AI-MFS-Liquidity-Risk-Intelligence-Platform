"use client";

import { useId, useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface TooltipProps {
  /** The tooltip text, also used as the accessible description. */
  content: string;
  children: ReactNode;
  className?: string;
}

/**
 * Lightweight tooltip. The trigger is keyboard-focusable and the text is wired
 * through aria-describedby, so the information is reachable without a mouse.
 * Escape dismisses it.
 */
export function Tooltip({ content, children, className }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const tooltipId = useId();

  return (
    <span
      className={cn("relative inline-flex", className)}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          setVisible(false);
        }
      }}
    >
      <span tabIndex={0} aria-describedby={visible ? tooltipId : undefined}>
        {children}
      </span>
      {visible ? (
        <span
          role="tooltip"
          id={tooltipId}
          className="absolute bottom-full left-1/2 z-40 mb-2 w-max max-w-64 -translate-x-1/2 rounded-lg bg-navy px-3 py-1.5 text-xs font-medium text-white shadow-raised"
        >
          {content}
        </span>
      ) : null}
    </span>
  );
}
