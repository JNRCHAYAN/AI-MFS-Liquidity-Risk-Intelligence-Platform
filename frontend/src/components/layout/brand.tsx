import Link from "next/link";

import { cn } from "@/lib/utils";

/**
 * Original wordmark for the prototype. The shield glyph is decorative
 * (aria-hidden); the product name is always present as real text.
 */
export function Brand({
  className,
  href = "/",
}: {
  className?: string;
  href?: string;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "inline-flex items-center gap-2 rounded-lg py-1 font-semibold text-navy",
        className,
      )}
      aria-label="upay Shield home"
    >
      <ShieldMark className="size-7 text-teal" />
      <span className="text-base tracking-tight sm:text-lg">
        upay <span className="text-teal">Shield</span>
      </span>
    </Link>
  );
}

function ShieldMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={className}
    >
      <path d="M12 3l7 3v5c0 4.4-2.9 8.2-7 9.5C7.9 19.2 5 15.4 5 11V6l7-3z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}
