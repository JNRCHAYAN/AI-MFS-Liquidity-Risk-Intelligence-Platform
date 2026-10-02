import { Database, FileSearch, Scale, UserCheck } from "lucide-react";

import { Alert, Badge, Card } from "@/components/ui";

const PILLARS = [
  {
    Icon: Database,
    title: "Dataset scope",
    body: "A generated synthetic corpus of transactions, entities, devices, login events, agents and network structure. No production upay data and no real PII is used anywhere in the prototype.",
  },
  {
    Icon: FileSearch,
    title: "Provenance",
    body: "Model attribution, anomaly evidence, graph motifs and policy rules are shown as distinct sources, each carrying a stable evidence ID an analyst can trace back to its origin.",
  },
  {
    Icon: Scale,
    title: "Honest labelling",
    body: "Scores keep their real units. An anomaly percentile is never relabelled as a probability, and a flagged transaction value is never described as money saved or blocked loss.",
  },
  {
    Icon: UserCheck,
    title: "Human review",
    body: "Every suggested hold, release, verify or block is simulated, requires an authorised analyst and a written rationale, and writes a durable audit event.",
  },
] as const;

export function EvidenceTransparency() {
  return (
    <section
      id="evidence"
      aria-labelledby="evidence-heading"
      className="scroll-mt-20 border-b border-border bg-canvas py-16 sm:py-20"
    >
      <div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
        <div className="max-w-2xl space-y-3">
          <Badge variant="neutral">Evidence &amp; transparency</Badge>
          <h2
            id="evidence-heading"
            className="text-2xl font-bold tracking-tight text-navy sm:text-3xl"
          >
            We publish what we can prove
          </h2>
          <p className="text-base leading-relaxed text-muted">
            The prototype is still being built. Where results do not exist yet,
            we say so rather than filling the gap with a number.
          </p>
        </div>

        <div className="mt-8">
          <Alert variant="warning" title="Model metrics are not published yet">
            There are no validated held-out results for this prototype so far,
            so no accuracy, precision, recall or success rate is shown here. We
            will publish the real numbers, including where the model is weak,
            once evaluation is complete. See the model card in the repository
            docs for status.
          </Alert>
        </div>

        <ul className="mt-8 grid gap-4 sm:grid-cols-2">
          {PILLARS.map(({ Icon, title, body }) => (
            <li key={title}>
              <Card className="flex h-full gap-4 p-5">
                <span className="inline-flex size-11 shrink-0 items-center justify-center rounded-xl bg-teal-soft text-teal-strong">
                  <Icon aria-hidden="true" className="size-5" />
                </span>
                <div className="space-y-1">
                  <h3 className="text-base font-semibold text-navy">{title}</h3>
                  <p className="text-sm leading-relaxed text-muted">{body}</p>
                </div>
              </Card>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
