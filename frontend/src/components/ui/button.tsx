import type { ComponentProps } from "react";

import { cn, type ClassValue } from "@/lib/utils";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "outline"
  | "ghost"
  | "danger";
export type ButtonSize = "sm" | "md" | "lg";

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "bg-teal text-white hover:bg-teal-strong border border-transparent",
  secondary: "bg-navy text-white hover:bg-navy/90 border border-transparent",
  outline:
    "bg-surface text-navy border border-border-strong hover:border-teal hover:text-teal",
  ghost: "bg-transparent text-navy border border-transparent hover:bg-navy/5",
  danger: "bg-risk-high text-white border border-transparent hover:bg-risk-high/90",
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  // Touch targets: md and lg are >= 44px. `sm` is for dense desktop toolbars.
  sm: "min-h-9 px-3 text-sm gap-1.5",
  md: "min-h-11 px-4 text-sm gap-2",
  lg: "min-h-12 px-6 text-base gap-2",
};

/**
 * Shared button styling. Use this to style a link as a button — never nest an
 * anchor inside a <button>, which is invalid and breaks keyboard interaction.
 */
export function buttonClassName(options?: {
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: ClassValue;
}): string {
  const { variant = "primary", size = "md", className } = options ?? {};
  return cn(
    "inline-flex items-center justify-center rounded-lg font-medium transition-colors",
    "disabled:pointer-events-none disabled:opacity-50",
    VARIANT_CLASSES[variant],
    SIZE_CLASSES[size],
    className,
  );
}

export interface ButtonProps extends ComponentProps<"button"> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export function Button({
  className,
  variant = "primary",
  size = "md",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button type={type} className={buttonClassName({ variant, size, className })} {...props} />
  );
}
