import Link from "next/link";
import { ArrowRight, BookOpen } from "lucide-react";

import { Brand } from "@/components/layout/brand";
import { buttonClassName } from "@/components/ui/button";

/**
 * Inline GitHub brand mark.
 *
 * lucide-react 1.x removed brand icons, so this small SVG is defined locally
 * rather than pulled from the icon library. Decorative only: the adjacent text
 * carries the meaning, so it is hidden from assistive technology.
 */
function GitHubMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
      focusable="false"
      className={className}
    >
      <path d="M12 .5C5.73.5.5 5.73.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55v-2.1c-3.2.7-3.87-1.36-3.87-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.7 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.1 11.1 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.84 1.19 3.1 0 4.43-2.7 5.4-5.26 5.69.41.36.78 1.06.78 2.14v3.17c0 .3.21.67.8.55A11.51 11.51 0 0 0 23.5 12C23.5 5.73 18.27.5 12 .5Z" />
    </svg>
  );
}

/**
 * Repository URL taken from the project's own recorded remote in
 * docs/PROGRESS.md. Not a claim of a live deployment.
 */
const REPOSITORY_URL =
  "https://github.com/JNRCHAYAN/AI-MFS-Liquidity-Risk-Intelligence-Platform";
const DOCS_URL = `${REPOSITORY_URL}/tree/master/docs`;

export function CtaFooter() {
  return (
    <>
      <section
        aria-labelledby="cta-heading"
        className="border-b border-border bg-surface py-16 sm:py-20"
      >
        <div className="mx-auto flex w-full max-w-6xl flex-col items-start gap-6 px-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-xl space-y-2">
            <h2
              id="cta-heading"
              className="text-2xl font-bold tracking-tight text-navy sm:text-3xl"
            >
              Explore the analyst workspace
            </h2>
            <p className="text-base leading-relaxed text-muted">
              Open the demo overview to see how alerts are structured. The
              detailed analyst screens arrive in the next build wave.
            </p>
          </div>
          <Link
            href="/app/overview"
            className={buttonClassName({ size: "lg" })}
          >
            Explore demo
            <ArrowRight aria-hidden="true" className="size-4" />
          </Link>
        </div>
      </section>

      <footer className="bg-canvas py-12">
        <div className="mx-auto grid w-full max-w-6xl gap-8 px-4 sm:px-6 md:grid-cols-3">
          <div className="space-y-3">
            <Brand />
            <p className="text-sm leading-relaxed text-muted">
              A proposed hackathon concept for AI DEV FEST 2026, Track 01
              (Trust &amp; Risk Intelligence), organized by DIU CPC × upay. It
              is not an official upay product and makes no partnership claim.
            </p>
          </div>

          <nav aria-label="Project links" className="space-y-3">
            <h2 className="text-sm font-semibold text-navy">Project</h2>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href={REPOSITORY_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex min-h-11 items-center gap-2 rounded-lg text-muted hover:text-teal"
                >
                  <GitHubMark className="size-4" />
                  Repository
                  <span className="sr-only">(opens in a new tab)</span>
                </a>
              </li>
              <li>
                <a
                  href={DOCS_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex min-h-11 items-center gap-2 rounded-lg text-muted hover:text-teal"
                >
                  <BookOpen aria-hidden="true" className="size-4" />
                  Documentation
                  <span className="sr-only">(opens in a new tab)</span>
                </a>
              </li>
              <li>
                <Link
                  href="/app/overview"
                  className="inline-flex min-h-11 items-center gap-2 rounded-lg text-muted hover:text-teal"
                >
                  Demo overview
                </Link>
              </li>
            </ul>
          </nav>

          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-navy">Team</h2>
            <p className="text-sm leading-relaxed text-muted">
              Built by the upay Shield hackathon team. Individual member names
              and roles are recorded in the repository README and
              docs/PROGRESS.md. Artificial-intelligence tools used in
              development are disclosed in docs/ai-disclosure.md.
            </p>
          </div>
        </div>

        <div className="mx-auto mt-8 w-full max-w-6xl border-t border-border px-4 pt-6 sm:px-6">
          <p className="text-sm font-semibold text-navy">
            Hackathon prototype; no real transactions.
          </p>
          <p className="mt-1 text-xs text-muted">
            All data shown is synthetic. Not for production use. No real
            financial decisions are made or executed by this software.
          </p>
        </div>
      </footer>
    </>
  );
}
