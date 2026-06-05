"use client";

import Link from "next/link";
import { useTransition } from "react";
import { ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";
import { setApplicationStatus } from "@/lib/actions";
import {
  APPLICATION_STATUSES,
  STATUS_ACCENT,
  STATUS_LABELS,
} from "@/lib/format";
import type { ApplicationCard } from "@/lib/types";
import { PriorityBadge, ScorePill } from "./ui";

export function KanbanBoard({ cards }: { cards: ApplicationCard[] }) {
  const [pending, start] = useTransition();
  const byStatus = (s: string) => cards.filter((c) => c.status === s);

  return (
    <div className={pending ? "opacity-70 transition" : "transition"}>
      <div className="flex gap-3 overflow-x-auto pb-4">
        {APPLICATION_STATUSES.map((status) => {
          const items = byStatus(status);
          const accent = STATUS_ACCENT[status];
          return (
            <div
              key={status}
              className="flex w-72 shrink-0 flex-col rounded-2xl border border-[var(--border-soft)] bg-[var(--panel-2)]/50"
            >
              <div className="flex items-center justify-between px-3 py-2.5">
                <div className="flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ background: accent }}
                  />
                  <span className="text-sm font-semibold">
                    {STATUS_LABELS[status]}
                  </span>
                </div>
                <span className="rounded-md bg-white/5 px-1.5 py-0.5 text-xs tabular-nums text-[var(--muted)]">
                  {items.length}
                </span>
              </div>
              <div
                className="h-0.5 w-full"
                style={{ background: `${accent}55` }}
              />
              <div className="flex max-h-[calc(100vh-230px)] flex-col gap-2 overflow-y-auto p-2">
                {items.map((card) => (
                  <Card
                    key={card.job_id}
                    card={card}
                    onMove={(dir) => {
                      const idx = APPLICATION_STATUSES.indexOf(status);
                      const next = APPLICATION_STATUSES[idx + dir];
                      if (next) start(() => setApplicationStatus(card.job_id, next));
                    }}
                    canPrev={APPLICATION_STATUSES.indexOf(status) > 0}
                    canNext={
                      APPLICATION_STATUSES.indexOf(status) <
                      APPLICATION_STATUSES.length - 1
                    }
                  />
                ))}
                {items.length === 0 && (
                  <div className="px-2 py-6 text-center text-xs text-[var(--muted)]/60">
                    —
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Card({
  card,
  onMove,
  canPrev,
  canNext,
}: {
  card: ApplicationCard;
  onMove: (dir: number) => void;
  canPrev: boolean;
  canNext: boolean;
}) {
  return (
    <div className="card panel-hover p-3">
      <div className="flex items-start justify-between gap-2">
        <Link
          href={`/jobs/${card.job_id}`}
          className="line-clamp-2 text-sm font-medium leading-snug hover:text-indigo-200"
        >
          {card.title}
        </Link>
        {card.match_score != null && <ScorePill score={card.match_score} />}
      </div>
      <div className="mt-1.5 flex items-center justify-between">
        <span className="truncate text-xs text-[var(--muted)]">
          {card.company_name}
        </span>
        <PriorityBadge priority={card.priority} />
      </div>
      <div className="mt-2.5 flex items-center justify-between border-t border-[var(--border-soft)] pt-2">
        <div className="flex gap-1">
          <button
            disabled={!canPrev}
            onClick={() => onMove(-1)}
            title="Move back"
            className="grid h-6 w-6 place-items-center rounded-md border border-[var(--border)] text-[var(--muted)] transition enabled:hover:text-[var(--text)] disabled:opacity-25"
          >
            <ChevronLeft size={14} />
          </button>
          <button
            disabled={!canNext}
            onClick={() => onMove(1)}
            title="Move forward"
            className="grid h-6 w-6 place-items-center rounded-md border border-[var(--border)] text-[var(--muted)] transition enabled:hover:text-[var(--text)] disabled:opacity-25"
          >
            <ChevronRight size={14} />
          </button>
        </div>
        <a
          href={card.url}
          target="_blank"
          rel="noreferrer"
          className="grid h-6 w-6 place-items-center rounded-md text-[var(--muted)] transition hover:text-indigo-200"
        >
          <ExternalLink size={13} />
        </a>
      </div>
    </div>
  );
}
