import {
  CircleHelp,
  ShieldAlert,
  ShieldCheck,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";

import type { ClassValue } from "@/lib/utils";

/**
 * Risk presentation. Risk is NEVER colour-only: every level carries a short
 * label and an icon, and the tinted background is paired with a dark,
 * AA-contrast foreground. Consumers must render label + icon, not just a dot.
 */
export type RiskLevel = "low" | "medium" | "high" | "unknown";

export interface RiskPresentation {
  level: RiskLevel;
  label: string;
  /** Plain-language meaning, used in tooltips and accessible descriptions. */
  description: string;
  Icon: LucideIcon;
  /** Tinted badge classes (background + border + text). */
  badgeClassName: ClassValue;
  /** Foreground-only class for inline text or icon. */
  textClassName: ClassValue;
}

const PRESENTATIONS: Record<RiskLevel, RiskPresentation> = {
  low: {
    level: "low",
    label: "Low risk",
    description:
      "No policy trigger and a low model score. Recorded, not escalated.",
    Icon: ShieldCheck,
    badgeClassName:
      "border-risk-low/30 bg-risk-low-bg text-risk-low",
    textClassName: "text-risk-low",
  },
  medium: {
    level: "medium",
    label: "Medium risk",
    description:
      "One strong or several modest concerns. Suggested simulated step-up verification or analyst review.",
    Icon: TriangleAlert,
    badgeClassName:
      "border-risk-medium/30 bg-risk-medium-bg text-risk-medium",
    textClassName: "text-risk-medium",
  },
  high: {
    level: "high",
    label: "High risk",
    description:
      "A strong validated score or corroborated multi-source evidence. Suggested simulated hold and urgent review.",
    Icon: ShieldAlert,
    badgeClassName:
      "border-risk-high/30 bg-risk-high-bg text-risk-high",
    textClassName: "text-risk-high",
  },
  unknown: {
    level: "unknown",
    label: "Insufficient data",
    description:
      "Missing data or a model that is unavailable. Uncertainty is reported explicitly rather than guessed.",
    Icon: CircleHelp,
    badgeClassName:
      "border-risk-unknown/30 bg-risk-unknown-bg text-risk-unknown",
    textClassName: "text-risk-unknown",
  },
};

export function getRiskPresentation(level: RiskLevel): RiskPresentation {
  return PRESENTATIONS[level];
}

export const RISK_LEVELS: readonly RiskLevel[] = [
  "low",
  "medium",
  "high",
  "unknown",
];
