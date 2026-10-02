import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends ComponentProps<"select"> {
  label: string;
  options: readonly SelectOption[];
  hint?: string;
  error?: string;
  hideLabel?: boolean;
  placeholder?: string;
}

export function Select({
  label,
  options,
  hint,
  error,
  hideLabel = false,
  placeholder,
  id,
  className,
  required,
  ...props
}: SelectProps) {
  const selectId = id ?? props.name;
  const hintId = hint && selectId ? `${selectId}-hint` : undefined;
  const errorId = error && selectId ? `${selectId}-error` : undefined;
  const describedBy =
    [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={selectId}
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
      <select
        id={selectId}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cn(
          "min-h-11 w-full rounded-lg border bg-surface px-3 text-sm text-navy",
          "focus-visible:border-teal",
          "disabled:cursor-not-allowed disabled:bg-canvas disabled:text-muted",
          error ? "border-risk-high" : "border-border-strong",
          className,
        )}
        {...props}
      >
        {placeholder ? (
          <option value="" disabled>
            {placeholder}
          </option>
        ) : null}
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </option>
        ))}
      </select>
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
