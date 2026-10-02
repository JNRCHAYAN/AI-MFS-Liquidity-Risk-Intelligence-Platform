import { FlaskConical, GitBranch, Info, Scale, Sparkles } from "lucide-react";

import { Badge, Card, RiskBadge } from "@/components/ui";
import { formatPoisha } from "@/lib/formatting";

/**
 * Product preview built from *rendered synthetic demo data* (no screenshot and
 * no live API). Every value below is an illustrative generated sample, is
 * labelled as such, and is deliberately not presented as measured model
 * performance.
 */
const DEMO_SIGNALS = [
  {
    Icon: Sparkles,
    label: "Model score",
    value: "0.82",
    note: "An uncalibrated model score, not a probability.",
  },
  {
    Icon: Scale,
    label: "Behavioural anomaly",
    value: "97th percentile",
    note: "Isolation Forest percentile, not a probability.",
  },
  {
    Icon: GitBranch,
    label: "Graph evidence",
    value: "Shared motif",
    note: "Recipient linked to a mule-like flow with 4 accounts in 48h.",
  },
] as const;

export function AlertPreview() {
  return (
    <figure className="w-full max-w-md rounded-card border border-border bg-canvas p-3 shadow-card">
      <Card className="overflow-hidden">
        <div className="flex items-center justify-between gap-2 border-b border-border bg-surface px-4 py-3">
          <div className="flex items-center gap-2">
            <FlaskConical aria-hidden="true" className="size-4 text-teal" />
            <span className="text-sm font-semibold text-navy">
              Alert preview
            </span>
          </div>
          <Badge variant="teal">Synthetic</Badge>
        </div>

        <div className="space-y-4 p-4">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="font-mono text-xs text-muted">TXN-SYN-000123</p>
              <p className="mt-1 text-sm text-muted">
                Flagged transaction value
              </p>
              <p className="text-2xl font-semibold tabular-nums text-navy">
                {formatPoisha(1_250_000)}
              </p>
              <p className="mt-1 flex items-start gap-1 text-xs text-muted">
                <Info aria-hidden="true" className="mt-0.5 size-3.5 shrink-0" />
                Value under review. This is not money saved or blocked loss.
              </p>
            </div>
            <RiskBadge level="high" />
          </div>

          <dl className="space-y-2">
            {DEMO_SIGNALS.map(({ Icon, label, value, note }) => (
              <div
                key={label}
                className="flex items-start gap-3 rounded-lg border border-border bg-surface p-3"
              >
                <Icon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-teal" />
                <div className="min-w-0">
                  <dt className="text-sm font-medium text-navy">{label}</dt>
                  <dd className="text-sm tabular-nums text-navy">{value}</dd>
                  <dd className="mt-0.5 text-xs text-muted">{note}</dd>
                </div>
              </div>
            ))}
          </dl>

          <div className="rounded-lg border border-border bg-canvas p-3">
            <p className="text-sm font-medium text-navy">
              Recommended next step
            </p>
            <p className="mt-1 text-sm text-muted">
              Simulated hold and urgent analyst review. A human reviews the
              evidence before anything happens.
            </p>
          </div>
        </div>
      </Card>

      <figcaption className="mt-3 px-1 text-xs text-muted">
        Illustrative synthetic sample. Values and entities are generated for
        demonstration only and are not measured model performance.
      </figcaption>
    </figure>
  );
}
