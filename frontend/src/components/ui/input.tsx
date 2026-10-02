import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export interface InputProps extends ComponentProps<"input"> {
  label: string;
  /** Helper text shown under the field. */
  hint?: string;
  /** Error message; when present the field is marked invalid and described. */
  error?: string;
  /** Hide the visible label but keep it for assistive tech. */
  hideLabel?: boolean;
}

export function Input({
  label,
  hint,
  error,
  hideLabel = false,
  id,
  className,
  required,
  ...props
}: InputProps) {
  const inputId = id ?? props.name;
  const hintId = hint && inputId ? `${inputId}-hint` : undefined;
  const errorId = error && inputId ? `${inputId}-error` : undefined;
  const describedBy =
    [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={inputId}
        className={cn(
          "text-sm font-medium text-navy",
          hideLabel && "sr-only",
        )}
      >
        {label}
        {required ? (
          <span aria-hidden="true" className="ml-0.5 text-risk-high">
            *
          </span>
        ) : null}
      </label>
      <input
        id={inputId}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cn(
          "min-h-11 w-full rounded-lg border bg-surface px-3 text-sm text-navy",
          "placeholder:text-muted/70",
          "focus-visible:border-teal",
          "disabled:cursor-not-allowed disabled:bg-canvas disabled:text-muted",
          error ? "border-risk-high" : "border-border-strong",
          className,
        )}
        {...props}
      />
      {hint && !error ? (
        <p id={hintId} className="text-xs text-muted">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={errorId} className="text-xs font-medium text-risk-high">
          {error}
        </p>
      ) : null}
    </div>
  );
}
