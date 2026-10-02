import { FlaskConical } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * Persistent synthetic-data banner. It is mounted in the authenticated app
 * shell so every analyst screen carries the same notice.
 */
export function SyntheticBanner({ className }: { className?: string }) {
  return (
    <div
      role="note"
      aria-label="Synthetic data notice"
      className={cn(
        "flex items-start gap-2 border-b border-risk-medium/30 bg-risk-medium-bg px-4 py-2 text-xs text-risk-medium sm:items-center sm:text-sm",
        className,
      )}
    >
      <FlaskConical aria-hidden="true" className="mt-0.5 size-4 shrink-0 sm:mt-0" />
      <p>
        <span className="font-semibold">Synthetic data only.</span> Every
        transaction, entity and alert in this prototype is generated for
        demonstration. There are no real transactions and no customer data.
      </p>
    </div>
  );
}
