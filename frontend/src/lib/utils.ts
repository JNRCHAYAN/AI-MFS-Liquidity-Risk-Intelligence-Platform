/**
 * Minimal class-name joiner. Kept dependency-free on purpose — the project
 * avoids abstractions with a single trivial use.
 */
export type ClassValue = string | number | false | null | undefined;

export function cn(...values: ClassValue[]): string {
  return values.filter(Boolean).join(" ");
}
