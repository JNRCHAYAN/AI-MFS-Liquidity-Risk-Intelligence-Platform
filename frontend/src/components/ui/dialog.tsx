"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";
import { X } from "lucide-react";

import { cn } from "@/lib/utils";

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children?: ReactNode;
  footer?: ReactNode;
  className?: string;
}

/**
 * Accessible modal built on the native <dialog> element, which gives us focus
 * trapping, Escape-to-close and focus restoration for free. A visible focus
 * ring is preserved by the global :focus-visible rule.
 */
export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  className,
}: DialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    const node = dialogRef.current;
    if (!node) {
      return;
    }

    if (open && !node.open) {
      node.showModal();
    } else if (!open && node.open) {
      node.close();
    }
  }, [open]);

  useEffect(() => {
    const node = dialogRef.current;
    if (!node) {
      return;
    }

    // Fired by the browser on Escape and on programmatic close.
    const handleClose = () => onClose();
    node.addEventListener("close", handleClose);
    return () => node.removeEventListener("close", handleClose);
  }, [onClose]);

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={titleId}
      aria-describedby={description ? descriptionId : undefined}
      onClick={(event) => {
        // Close when the backdrop (the dialog element itself) is clicked.
        if (event.target === dialogRef.current) {
          onClose();
        }
      }}
      className={cn(
        "m-auto w-[min(32rem,calc(100vw-2rem))] rounded-card border border-border bg-surface p-0 text-navy shadow-raised backdrop:bg-navy/40",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-4 border-b border-border p-5">
        <div className="space-y-1">
          <h2 id={titleId} className="text-base font-semibold">
            {title}
          </h2>
          {description ? (
            <p id={descriptionId} className="text-sm text-muted">
              {description}
            </p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close dialog"
          className="inline-flex size-11 shrink-0 items-center justify-center rounded-lg text-muted hover:bg-navy/5 hover:text-navy"
        >
          <X aria-hidden="true" className="size-5" />
        </button>
      </div>
      {children ? <div className="p-5 text-sm text-muted">{children}</div> : null}
      {footer ? (
        <div className="flex flex-wrap justify-end gap-3 border-t border-border p-5">
          {footer}
        </div>
      ) : null}
    </dialog>
  );
}
