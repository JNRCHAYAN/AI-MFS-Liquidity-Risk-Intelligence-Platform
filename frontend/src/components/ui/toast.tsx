"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { CircleAlert, CircleCheck, Info, TriangleAlert, X } from "lucide-react";

import { cn } from "@/lib/utils";

export type ToastVariant = "info" | "success" | "warning" | "danger";

export interface ToastInput {
  title: string;
  description?: string;
  variant?: ToastVariant;
  /** Milliseconds before auto-dismiss; 0 keeps the toast until dismissed. */
  duration?: number;
}

interface ToastRecord extends Required<Pick<ToastInput, "title" | "variant">> {
  id: string;
  description?: string;
  duration: number;
}

interface ToastContextValue {
  toast: (input: ToastInput) => string;
  dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const TOAST_STYLES: Record<
  ToastVariant,
  { container: string; Icon: typeof Info }
> = {
  info: { container: "border-teal/40 bg-surface", Icon: Info },
  success: { container: "border-risk-low/40 bg-surface", Icon: CircleCheck },
  warning: { container: "border-risk-medium/40 bg-surface", Icon: TriangleAlert },
  danger: { container: "border-risk-high/40 bg-surface", Icon: CircleAlert },
};

const ICON_COLORS: Record<ToastVariant, string> = {
  info: "text-teal",
  success: "text-risk-low",
  warning: "text-risk-medium",
  danger: "text-risk-high",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastRecord[]>([]);
  const counter = useRef(0);
  const timers = useRef(new Map<string, ReturnType<typeof setTimeout>>());

  const dismiss = useCallback((id: string) => {
    setToasts((current) => current.filter((item) => item.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const toast = useCallback(
    (input: ToastInput) => {
      counter.current += 1;
      const id = `toast-${counter.current}`;
      const record: ToastRecord = {
        id,
        title: input.title,
        description: input.description,
        variant: input.variant ?? "info",
        duration: input.duration ?? 6000,
      };
      setToasts((current) => [...current, record]);

      if (record.duration > 0) {
        timers.current.set(
          id,
          setTimeout(() => dismiss(id), record.duration),
        );
      }
      return id;
    },
    [dismiss],
  );

  useEffect(() => {
    const pending = timers.current;
    return () => {
      pending.forEach((timer) => clearTimeout(timer));
      pending.clear();
    };
  }, []);

  const value = useMemo(() => ({ toast, dismiss }), [toast, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        aria-live="polite"
        aria-atomic="false"
        className="pointer-events-none fixed inset-x-0 bottom-0 z-50 flex flex-col items-center gap-2 p-4 sm:items-end"
      >
        {toasts.map((item) => {
          const { container, Icon } = TOAST_STYLES[item.variant];
          return (
            <div
              key={item.id}
              role="status"
              className={cn(
                "pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-card border p-4 shadow-raised",
                container,
              )}
            >
              <Icon
                aria-hidden="true"
                className={cn("mt-0.5 size-4 shrink-0", ICON_COLORS[item.variant])}
              />
              <div className="flex-1 space-y-1">
                <p className="text-sm font-semibold text-navy">{item.title}</p>
                {item.description ? (
                  <p className="text-sm text-muted">{item.description}</p>
                ) : null}
              </div>
              <button
                type="button"
                onClick={() => dismiss(item.id)}
                aria-label={`Dismiss notification: ${item.title}`}
                className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-muted hover:bg-navy/5 hover:text-navy"
              >
                <X aria-hidden="true" className="size-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider.");
  }
  return context;
}
