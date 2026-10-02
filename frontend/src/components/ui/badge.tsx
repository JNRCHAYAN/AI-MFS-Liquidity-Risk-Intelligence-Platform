import type { ComponentProps } from "react";

import { getRiskPresentation, type RiskLevel } from "@/lib/risk";
import { cn } from "@/lib/utils";

export type BadgeVariant =
  | "neutral"
  | "teal"
  | "navy"
  | "outline"
  | "low"
  | "medium"
  | "high"
  | "unknown";

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  neutral: "border-border-strong bg-canvas text-muted",
  teal: "border-teal/30 bg-teal-soft text-teal-strong",
  navy: "border-transparent bg-navy text-white",
  outline: "border-border-strong bg-transparent text-muted",
  low: "border-risk-low/30 bg-risk-low-bg text-risk-low",
  medium: "border-risk-medium/30 bg-risk-medium-bg text-risk-medium",
  high: "border-risk-high/30 bg-risk-high-bg text-risk-high",
  unknown: "border-risk-unknown/30 bg-risk-unknown-bg text-risk-unknown",
};

export interface BadgeProps extends ComponentProps<"span"> {
  variant?: BadgeVariant;
}

export function Badge({
  className,
  variant = "neutral",
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        VARIANT_CLASSES[variant],
        className,
      )}
      {...props}
    />
  );
}

export interface RiskBadgeProps extends Omit<ComponentProps<"span">, "children"> {
  level: RiskLevel;
  /** Optional override for the visible label. */
  label?: string;
}

/**
 * Risk is never colour-only: this always renders an icon and a text label in
 * addition to the tint, so it stays meaningful for colour-blind users and in
 * greyscale.
 */
export function RiskBadge({ level, label, className, ...props }: RiskBadgeProps) {
  const { Icon, label: defaultLabel, badgeClassName } =
    getRiskPresentation(level);

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold",
        badgeClassName,
        className,
      )}
      {...props}
    >
      <Icon aria-hidden="true" className="size-3.5 shrink-0" />
      {label ?? defaultLabel}
    </span>
  );
}
