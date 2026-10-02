import type { Metadata } from "next";
import { Construction } from "lucide-react";

import { Alert, Card, EmptyState } from "@/components/ui";

export const metadata: Metadata = {
  title: "Overview",
  description: "Placeholder for the analyst workspace overview screen.",
};

const PLANNED = [
  "Scored transactions, open alerts, alert rate and reviewed cases — each with a stated time range and definition.",
  "Prioritised alert queue and trend summaries.",
  "Honest loading, empty, error and degraded states, with an explicit unavailable banner when the backend is down.",
] as const;

/**
 * Placeholder for `/app/overview`. The full analyst screen is the next build
 * wave; this page exists so the homepage CTA resolves and the shared shell can
 * be reviewed now.
 */
export default function OverviewPage() {
  return (
    <div className="mx-auto w-full max-w-4xl space-y-6">
      <Alert variant="info" title="Scaffold only — the analyst screens are next">
        This route proves the workspace shell, synthetic banner and typography.
        No metrics are shown because none have been validated yet.
      </Alert>

      <Card className="p-6">
        <h2 className="flex items-center gap-2 text-base font-semibold text-navy">
          <Construction aria-hidden="true" className="size-4 text-teal" />
          What will live here
        </h2>
        <ul className="mt-4 space-y-3">
          {PLANNED.map((item) => (
            <li key={item} className="flex gap-3 text-sm text-muted">
              <span
                aria-hidden="true"
                className="mt-2 size-1.5 shrink-0 rounded-full bg-teal"
              />
              {item}
            </li>
          ))}
        </ul>
      </Card>

      <EmptyState
        title="No data yet"
        description="Once the scoring pipeline and database are wired up, this screen will show the prioritised alert queue. It is intentionally empty for now."
      />
    </div>
  );
}
