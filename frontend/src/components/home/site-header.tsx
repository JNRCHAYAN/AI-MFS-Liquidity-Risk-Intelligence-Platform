"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";

import { Brand } from "@/components/layout/brand";
import { buttonClassName } from "@/components/ui";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { label: "Features", href: "#features" },
  { label: "How it works", href: "#how-it-works" },
  { label: "Responsible AI", href: "#responsible-ai" },
] as const;

export function SiteHeader() {
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!menuOpen) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [menuOpen]);

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/95 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Brand />

        <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="inline-flex min-h-11 items-center rounded-lg px-3 text-sm font-medium text-muted hover:bg-navy/5 hover:text-navy"
            >
              {link.label}
            </a>
          ))}
          <Link
            href="/app/overview"
            className="ml-2 inline-flex min-h-11 items-center rounded-lg px-3 text-sm font-medium text-teal hover:bg-teal-soft"
          >
            Demo
          </Link>
        </nav>

        <div className="hidden md:block">
          <Link href="/app/overview" className={buttonClassName()}>
            Explore demo
          </Link>
        </div>

        <button
          type="button"
          onClick={() => setMenuOpen((open) => !open)}
          aria-expanded={menuOpen}
          aria-controls="mobile-menu"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg text-navy hover:bg-navy/5 md:hidden"
        >
          {menuOpen ? (
            <X aria-hidden="true" className="size-5" />
          ) : (
            <Menu aria-hidden="true" className="size-5" />
          )}
        </button>
      </div>

      <div
        id="mobile-menu"
        hidden={!menuOpen}
        className={cn("border-t border-border bg-surface md:hidden")}
      >
        <nav aria-label="Main" className="flex flex-col gap-1 px-4 py-3">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className="flex min-h-11 items-center rounded-lg px-3 text-sm font-medium text-muted hover:bg-navy/5 hover:text-navy"
            >
              {link.label}
            </a>
          ))}
          <Link
            href="/app/overview"
            onClick={() => setMenuOpen(false)}
            className="flex min-h-11 items-center rounded-lg px-3 text-sm font-medium text-teal hover:bg-teal-soft"
          >
            Demo
          </Link>
        </nav>
      </div>
    </header>
  );
}
