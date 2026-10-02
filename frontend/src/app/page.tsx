import { CtaFooter } from "@/components/home/cta-footer";
import { EvidenceTransparency } from "@/components/home/evidence-transparency";
import { FeatureGrid } from "@/components/home/feature-grid";
import { Hero } from "@/components/home/hero";
import { HowItWorks } from "@/components/home/how-it-works";
import { ResponsibleAi } from "@/components/home/responsible-ai";
import { SiteHeader } from "@/components/home/site-header";

/**
 * Public homepage. Rendered from static product copy at build time — it never
 * calls the API, so it loads without authentication and stays usable when the
 * backend is unavailable.
 */
export default function HomePage() {
  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <Hero />
        <FeatureGrid />
        <HowItWorks />
        <EvidenceTransparency />
        <ResponsibleAi />
        <CtaFooter />
      </main>
    </>
  );
}
