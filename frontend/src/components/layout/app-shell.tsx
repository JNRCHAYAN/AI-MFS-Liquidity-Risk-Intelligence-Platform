"use client";

import { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Bot,
  LayoutDashboard,
  Menu,
  Network,
  Settings,
  ShieldAlert,
  SlidersHorizontal,
  Table2,
  Users,
  X,
  type LucideIcon,
} from "lucide-react";

import { Brand } from "@/components/layout/brand";
import { SyntheticBanner } from "@/components/layout/synthetic-banner";
import { Badge, Breadcrumb } from "@/components/ui";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  icon: LucideIcon;
  href?: string;
  planned?: boolean;
}

const NAV_ITEMS: readonly NavItem[] = [
  { label: "Overview", icon: LayoutDashboard, href: "/app/overview" },
  { label: "Transactions", icon: Table2, planned: true },
  { label: "Alerts", icon: ShieldAlert, planned: true },
  { label: "Cases", icon: Activity, planned: true },
  { label: "Network", icon: Network, planned: true },
  { label: "Agents", icon: Users, planned: true },
  { label: "Simulation", icon: SlidersHorizontal, planned: true },
  { label: "Models", icon: Bot, planned: true },
  { label: "Settings", icon: Settings, planned: true },
];

export interface AppShellProps {
  children: ReactNode;
}

function resolveSection(pathname: string): string {
  const match = NAV_ITEMS.find(
    (item) =>
      item.href &&
      (pathname === item.href || pathname.startsWith(`${item.href}/`)),
  );
  return match?.label ?? "Workspace";
}

/**
 * Analyst workspace shell. Screens for each section arrive in the next wave;
 * this shell already provides the persistent synthetic banner, responsive
 * sidebar/drawer, breadcrumb and title so those screens can be added without
 * restructuring.
 */
export function AppShell({ children }: AppShellProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const pathname = usePathname();
  const section = resolveSection(pathname);
  const breadcrumb = [
    { label: "Workspace", href: "/app/overview" },
    { label: section, href: pathname },
  ];

  useEffect(() => {
    if (!drawerOpen) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setDrawerOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [drawerOpen]);

  const nav = (
    <nav aria-label="Analyst workspace" className="flex flex-col gap-1 p-3">
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const active = item.href === pathname;
        if (item.href && !item.planned) {
          return (
            <Link
              key={item.label}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium",
                active
                  ? "bg-teal-soft text-teal-strong"
                  : "text-muted hover:bg-navy/5 hover:text-navy",
              )}
            >
              <Icon aria-hidden="true" className="size-4 shrink-0" />
              {item.label}
            </Link>
          );
        }
        return (
          <span
            key={item.label}
            aria-disabled="true"
            className="flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium text-muted/70"
          >
            <Icon aria-hidden="true" className="size-4 shrink-0" />
            <span className="flex-1">{item.label}</span>
            <Badge variant="outline" className="text-[10px] uppercase">
              Soon
            </Badge>
          </span>
        );
      })}
    </nav>
  );

  return (
    <div className="flex min-h-dvh flex-col">
      <SyntheticBanner />
      <div className="mx-auto flex w-full max-w-[100rem] flex-1 flex-col lg:flex-row">
        {/* Desktop sidebar */}
        <aside className="hidden w-60 shrink-0 border-r border-border bg-surface lg:block">
          <div className="border-b border-border px-4 py-4">
            <Brand href="/" />
          </div>
          {nav}
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex items-center gap-3 border-b border-border bg-surface px-4 py-3">
            <button
              type="button"
              onClick={() => setDrawerOpen(true)}
              aria-label="Open workspace navigation"
              aria-expanded={drawerOpen}
              className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg text-navy hover:bg-navy/5 lg:hidden"
            >
              <Menu aria-hidden="true" className="size-5" />
            </button>
            <div className="min-w-0">
              <Breadcrumb items={breadcrumb} />
              <h1 className="truncate text-lg font-semibold text-navy">
                {section}
              </h1>
            </div>
          </header>

          <main className="min-w-0 flex-1 p-4 sm:p-6">{children}</main>
        </div>
      </div>

      {/* Mobile drawer */}
      {drawerOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Close workspace navigation"
            onClick={() => setDrawerOpen(false)}
            className="absolute inset-0 bg-navy/40"
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Workspace navigation"
            className="absolute inset-y-0 left-0 w-64 max-w-[85vw] overflow-y-auto bg-surface shadow-raised"
          >
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <Brand href="/" />
              <button
                type="button"
                onClick={() => setDrawerOpen(false)}
                aria-label="Close workspace navigation"
                className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg text-navy hover:bg-navy/5"
              >
                <X aria-hidden="true" className="size-5" />
              </button>
            </div>
            {nav}
          </div>
        </div>
      ) : null}
    </div>
  );
}
