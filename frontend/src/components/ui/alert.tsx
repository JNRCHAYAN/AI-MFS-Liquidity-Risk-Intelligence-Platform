import type { ComponentProps } from "react";
import { CircleAlert, CircleCheck, Info, TriangleAlert } from "lucide-react";

import { cn } from "@/lib/utils";

export type AlertVariant = "info" | "success" | "warning" | "danger";

const ALERT_STYLES: Record<
  AlertVariant,
  { container: string; Icon: typeof Info }
> = {
  info: { container: "border-teal/30 bg-teal-soft text-teal-strong", Icon: Info },
  success: {
    container: "border-risk-low/30 bg-risk-low-bg text-risk-low",
    Icon: CircleCheck,
  },
  warning: {
    container: "border-risk-medium/30 bg-risk-medium-bg text-risk-medium",
    Icon: TriangleAlert,
  },
  danger: {
    container: "border-risk-high/30 bg-risk-high-bg text-risk-high",
    Icon: CircleAlert,
  },
};

export interface AlertProps extends ComponentProps<"div"> {
  variant?: AlertVariant;
  title: string;
}

export function Alert({
  variant = "info",
  title,
  className,
  children,
  ...props
}: AlertProps) {
  const { container, Icon } = ALERT_STYLES[variant];

  return (
    <div
      role={variant === "danger" ? "alert" : "status"}
      className={cn(
        "flex items-start gap-3 rounded-card border p-4 text-sm",
        container,
        className,
      )}
      {...props}
    >
      <Icon aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
      <div className="space-y-1">
        <p className="font-semibold">{title}</p>
        {children ? <div className="text-muted">{children}</div> : null}
      </div>
    </div>
  );
}
