import {
  Activity,
  Bot,
  Fingerprint,
  Gauge,
  MessageSquareWarning,
  Network,
  Users,
  type LucideIcon,
} from "lucide-react";

import { Badge, Card } from "@/components/ui";

interface Feature {
  Icon: LucideIcon;
  direction: string;
  title: string;
  description: string;
  surface: string;
}

/**
 * The seven feature cards map one-to-one to the seven Track 01 "Trust & Risk
 * Intelligence" challenge directions. Each card carries a plain-language
 * explanation and the route where the capability is planned to surface, so it
 * is informative even before the authenticated screens exist.
 */
const FEATURES: readonly Feature[] = [
  {
    Icon: Gauge,
    direction: "Real-time transaction risk",
    title: "Score transactions as they arrive",
    description:
      "A tabular classifier scores each transaction from causal features computed strictly from earlier events, never from the current or future outcome.",
    surface: "/app/transactions",
  },
  {
    Icon: Activity,
    direction: "Behavioural anomaly detection",
    title: "Notice deviations from normal",
    description:
      "An Isolation Forest reports an anomaly percentile against the customer's own prior behaviour, with an explicit insufficient-history flag when data is thin.",
    surface: "/app/transactions/[id]",
  },
  {
    Icon: Fingerprint,
    direction: "Account takeover intelligence",
    title: "Surface takeover signals",
    description:
      "Unusual device, location, timing, recipient novelty and velocity patterns are gathered as evidence — each with its own provenance.",
    surface: "/app/transactions/[id]",
  },
  {
    Icon: Network,
    direction: "Money-mule & network risk",
    title: "Trace connected entities",
    description:
      "Transaction-graph motifs reveal mule-like flows and linked accounts. The graph is always paired with an equivalent evidence list or table.",
    surface: "/app/network",
  },
  {
    Icon: Users,
    direction: "Agent risk intelligence",
    title: "Compare agents to peers",
    description:
      "Agent behaviour is compared to peer and historical patterns, with minimum-sample rules so a tiny sample never looks like a strong signal.",
    surface: "/app/agents",
  },
  {
    Icon: MessageSquareWarning,
    direction: "Scam intelligence",
    title: "Flag social-engineering patterns",
    description:
      "Patterns associated with scam or social-engineering transactions are surfaced as separate evidence, not folded into a single opaque score.",
    surface: "/app/alerts",
  },
  {
    Icon: Bot,
    direction: "Investigation assistant",
    title: "Explain the alert",
    description:
      "An evidence-grounded assistant drafts a narrative summary for the analyst. It is optional, backend-only, and never decides fraud or authorises an action.",
    surface: "/app/cases/[id]",
  },
];

export function FeatureGrid() {
  return (
    <section
      id="features"
      aria-labelledby="features-heading"
      className="scroll-mt-20 border-b border-border bg-canvas py-16 sm:py-20"
    >
      <div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
        <div className="max-w-2xl space-y-3">
          <Badge variant="teal">Track 01 · Trust &amp; Risk Intelligence</Badge>
          <h2
            id="features-heading"
            className="text-2xl font-bold tracking-tight text-navy sm:text-3xl"
          >
            Seven capabilities, one explained alert
          </h2>
          <p className="text-base leading-relaxed text-muted">
            Each card corresponds to one of the seven challenge directions for
            Track 01. Risk components stay separate — they are never averaged
            into a misleading single &ldquo;fraud probability&rdquo;.
          </p>
        </div>

        <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ Icon, direction, title, description, surface }) => (
            <li key={direction}>
              <Card className="flex h-full flex-col gap-3 p-5">
                <span className="inline-flex size-11 items-center justify-center rounded-xl bg-teal-soft text-teal-strong">
                  <Icon aria-hidden="true" className="size-5" />
                </span>
                <p className="text-xs font-semibold uppercase tracking-wide text-teal">
                  {direction}
                </p>
                <h3 className="text-base font-semibold text-navy">{title}</h3>
                <p className="flex-1 text-sm leading-relaxed text-muted">
                  {description}
                </p>
                <p className="border-t border-border pt-3 font-mono text-xs text-muted">
                  Planned surface: {surface}
                </p>
              </Card>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
