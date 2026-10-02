"use client";

import { useId, useRef, useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface TabItem {
  id: string;
  label: string;
  content: ReactNode;
}

export interface TabsProps {
  items: readonly TabItem[];
  /** Label for the tab list, announced to assistive tech. */
  label: string;
  defaultTabId?: string;
  className?: string;
}

/**
 * Accessible tabs following the WAI-ARIA pattern: roving tabindex, arrow-key
 * navigation, Home/End support and proper tab/tabpanel wiring.
 */
export function Tabs({ items, label, defaultTabId, className }: TabsProps) {
  const baseId = useId();
  const [activeId, setActiveId] = useState(
    defaultTabId ?? items[0]?.id ?? "",
  );
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});

  if (items.length === 0) {
    return null;
  }

  const activeIndex = Math.max(
    0,
    items.findIndex((item) => item.id === activeId),
  );
  const activeItem = items[activeIndex] ?? items[0];

  const focusTabAt = (index: number) => {
    const wrapped = (index + items.length) % items.length;
    const target = items[wrapped];
    if (!target) {
      return;
    }
    setActiveId(target.id);
    tabRefs.current[target.id]?.focus();
  };

  return (
    <div className={className}>
      <div
        role="tablist"
        aria-label={label}
        className="flex flex-wrap gap-1 border-b border-border"
      >
        {items.map((item, index) => {
          const selected = item.id === activeItem?.id;
          return (
            <button
              key={item.id}
              ref={(node) => {
                tabRefs.current[item.id] = node;
              }}
              type="button"
              role="tab"
              id={`${baseId}-tab-${item.id}`}
              aria-selected={selected}
              aria-controls={`${baseId}-panel-${item.id}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => setActiveId(item.id)}
              onKeyDown={(event) => {
                switch (event.key) {
                  case "ArrowRight":
                    event.preventDefault();
                    focusTabAt(index + 1);
                    break;
                  case "ArrowLeft":
                    event.preventDefault();
                    focusTabAt(index - 1);
                    break;
                  case "Home":
                    event.preventDefault();
                    focusTabAt(0);
                    break;
                  case "End":
                    event.preventDefault();
                    focusTabAt(items.length - 1);
                    break;
                  default:
                    break;
                }
              }}
              className={cn(
                "min-h-11 rounded-t-lg px-4 text-sm font-medium",
                selected
                  ? "border-b-2 border-teal text-teal"
                  : "border-b-2 border-transparent text-muted hover:text-navy",
              )}
            >
              {item.label}
            </button>
          );
        })}
      </div>
      {activeItem ? (
        <div
          role="tabpanel"
          id={`${baseId}-panel-${activeItem.id}`}
          aria-labelledby={`${baseId}-tab-${activeItem.id}`}
          tabIndex={0}
          className="p-4 text-sm text-muted"
        >
          {activeItem.content}
        </div>
      ) : null}
    </div>
  );
}
