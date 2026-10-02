import Link from "next/link";
import { ArrowRight, FlaskConical, ShieldCheck, UserCheck } from "lucide-react";

import { AlertPreview } from "./product-preview";
import { buttonClassName } from "@/components/ui/button";

const TRUST_CHIPS = [
  { label: "Synthetic data only", Icon: FlaskConical },
  { label: "Analyst decides", Icon: UserCheck },
  { label: "Explainable evidence", Icon: ShieldCheck },
] as const;

export function Hero() {
  return (
    <section
      aria-labelledby="hero-heading"
      className="border-b border-border bg-surface"
    >
      <div className="mx-auto grid w-full max-w-6xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:items-center lg:py-24">
        <div className="space-y-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-teal">
            AI DEV FEST 2026 · Track 01 · Trust &amp; Risk Intelligence
          </p>
          <h1
            id="hero-heading"
            className="text-4xl font-bold leading-tight tracking-tight text-navy sm:text-5xl"
          >
            Understand risk. Protect trust.
          </h1>
          <p className="max-w-xl text-base leading-relaxed text-muted sm:text-lg">
            upay Shield is a hackathon prototype that combines a tabular fraud
            classifier, a behavioural anomaly score, transaction-graph evidence
            and explicit policy rules into one explained alert. It is built to
            help a fraud analyst answer three questions: what happened, why it
            is risky, and what to review next.
          </p>
          <p className="max-w-xl text-sm leading-relaxed text-muted">
            It runs entirely on generated synthetic data. Nothing here scores a
            real payment, and the AI never makes the final decision — it
            surfaces evidence for a human.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
            <Link
              href="/app/overview"
              className={buttonClassName({ size: "lg" })}
            >
              Explore demo
              <ArrowRight aria-hidden="true" className="size-4" />
            </Link>
            <a
              href="#how-it-works"
              className={buttonClassName({ variant: "outline", size: "lg" })}
            >
              How it works
            </a>
          </div>
          <ul className="flex flex-wrap gap-x-4 gap-y-2 pt-2">
            {TRUST_CHIPS.map(({ label, Icon }) => (
              <li
                key={label}
                className="inline-flex items-center gap-2 text-sm text-muted"
              >
                <Icon aria-hidden="true" className="size-4 text-teal" />
                {label}
              </li>
            ))}
          </ul>
        </div>

        <div className="lg:justify-self-end">
          <AlertPreview />
        </div>
      </div>
    </section>
  );
}
