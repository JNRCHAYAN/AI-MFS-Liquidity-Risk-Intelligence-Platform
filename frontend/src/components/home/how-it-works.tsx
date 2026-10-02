import { Eye, MessageSquareText, UserCheck } from "lucide-react";

import { Badge } from "@/components/ui";

const STEPS = [
  {
    Icon: Eye,
    title: "Observe activity",
    description:
      "A synthetic transaction is validated and turned into a chronological feature snapshot using only events that strictly precede it.",
  },
  {
    Icon: MessageSquareText,
    title: "Explain risk",
    description:
      "Model attribution, anomaly percentile, graph evidence and policy rules are presented as separate, traceable sources with stable evidence IDs.",
  },
  {
    Icon: UserCheck,
    title: "Review action",
    description:
      "Policy suggests a review workflow. A human analyst confirms what happens next; every simulated action is recorded in an audit trail.",
  },
] as const;

export function HowItWorks() {
  return (
    <section
      id="how-it-works"
      aria-labelledby="how-it-works-heading"
      className="scroll-mt-20 border-b border-border bg-surface py-16 sm:py-20"
    >
      <div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
        <div className="max-w-2xl space-y-3">
          <Badge variant="neutral">How it works</Badge>
          <h2
            id="how-it-works-heading"
            className="text-2xl font-bold tracking-tight text-navy sm:text-3xl"
          >
            From activity to a reviewed decision
          </h2>
          <p className="text-base leading-relaxed text-muted">
            Three steps, with the analyst in the loop the whole way through.
          </p>
        </div>

        <ol className="mt-10 grid gap-4 md:grid-cols-3">
          {STEPS.map(({ Icon, title, description }, index) => (
            <li key={title}>
              <div className="flex h-full flex-col gap-3 rounded-card border border-border bg-canvas p-5">
                <div className="flex items-center gap-3">
                  <span
                    aria-hidden="true"
                    className="inline-flex size-9 items-center justify-center rounded-full bg-navy text-sm font-semibold tabular-nums text-white"
                  >
                    {index + 1}
                  </span>
                  <Icon aria-hidden="true" className="size-5 text-teal" />
                </div>
                <h3 className="text-base font-semibold text-navy">{title}</h3>
                <p className="text-sm leading-relaxed text-muted">
                  {description}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
