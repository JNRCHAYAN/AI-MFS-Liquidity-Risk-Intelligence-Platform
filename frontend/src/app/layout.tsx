import type { Metadata } from "next";

import { Providers } from "@/components/providers";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "upay Shield — Understand risk. Protect trust.",
    template: "%s · upay Shield",
  },
  description:
    "upay Shield is a hackathon prototype for Trust & Risk Intelligence. It combines a fraud classifier, behavioural anomaly scoring, transaction-graph evidence and policy rules into one explained alert. Synthetic data only.",
  applicationName: "upay Shield",
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-dvh bg-canvas text-navy antialiased">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-navy focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white"
        >
          Skip to main content
        </a>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
