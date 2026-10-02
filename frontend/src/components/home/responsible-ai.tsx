import { Database, Eye, ShieldQuestion, UserCheck } from "lucide-react";

import { Badge } from "@/components/ui";

const COMMITMENTS = [
  {
    Icon: Database,
    title: "Synthetic data",
    body: "Every record is generated. The prototype never ingests real customer data, real PII or production upay data.",
  },
  {
    Icon: Eye,
    title: "Explainability",
    body: "Alerts show signed feature contributions with their observed vs historical values, plus policy and graph evidence as separate sources.",
  },
  {
    Icon: ShieldQuestion,
    title: "Uncertainty",
    body: "Missing data or an unavailable model produces an explicit insufficient or degraded state — never an invented score.",
  },
  {
    Icon: UserCheck,
    title: "Analyst oversight",
    body: "The system recommends; a person decides. The optional language model writes narrative text only and holds no authority or tools.",
  },
] as const;

export function ResponsibleAi() {
  return (
    <section
      id="responsible-ai"
      aria-labelledby="responsible-ai-heading"
      className="scroll-mt-20 border-b border-border bg-navy py-16 text-white sm:py-20"
    >
      <div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
        <div className="max-w-2xl space-y-3">
          <Badge variant="teal">Responsible AI</Badge>
          <h2
            id="responsible-ai-heading"
            className="text-2xl font-bold tracking-tight sm:text-3xl"
          >
            Built to be accountable
          </h2>
          <p className="text-base leading-relaxed text-white/80">
            A risk tool has to be trustworthy before it is clever. These four
            commitments shape how upay Shield is designed.
          </p>
        </div>

        <dl className="mt-10 grid gap-4 sm:grid-cols-2">
          {COMMITMENTS.map(({ Icon, title, body }) => (
            <div
              key={title}
              className="flex gap-4 rounded-card border border-white/15 bg-white/5 p-5"
            >
              <span className="inline-flex size-11 shrink-0 items-center justify-center rounded-xl bg-teal-soft text-teal-strong">
                <Icon aria-hidden="true" className="size-5" />
              </span>
              <div className="space-y-1">
                <dt className="text-base font-semibold text-white">{title}</dt>
                <dd className="text-sm leading-relaxed text-white/80">
                  {body}
                </dd>
              </div>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
