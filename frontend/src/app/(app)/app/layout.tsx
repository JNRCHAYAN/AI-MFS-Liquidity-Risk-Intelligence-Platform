import type { ReactNode } from "react";

import { AppShell } from "@/components/layout/app-shell";

/**
 * Route group for the authenticated analyst workspace (`/app/*`). The shared
 * shell — persistent synthetic banner, responsive sidebar drawer, breadcrumb
 * and title — lives here so the individual screens can be added in the next
 * wave without restructuring.
 */
export default function WorkspaceLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
