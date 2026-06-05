import Link from "next/link";
import type { ReactNode } from "react";
import {
  PRIORITY_BADGE,
  ROLE_COLORS,
  roleLabel,
  scoreColor,
} from "@/lib/format";
import type { Priority } from "@/lib/types";

export function PageHeader({
  title,
  subtitle,
  right,
}: {
  title: string;
  subtitle?: string;
  right?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle && (
          <p className="mt-1 text-sm text-[var(--muted)]">{subtitle}</p>
        )}
      </div>
      {right}
    </div>
  );
}

export function PriorityBadge({ priority }: { priority: Priority | null }) {
  if (!priority)
    return (
      <span className="chip border-slate-600/40 bg-slate-700/20 text-slate-400">
        unscored
      </span>
    );
  return <span className={`chip ${PRIORITY_BADGE[priority]}`}>{priority}</span>;
}

export function RoleBadge({ role }: { role: string }) {
  const color = ROLE_COLORS[role as keyof typeof ROLE_COLORS] ?? "#94a3b8";
  return (
    <span
      className="chip"
      style={{
        color,
        borderColor: `${color}40`,
        background: `${color}1a`,
      }}
    >
      {roleLabel(role)}
    </span>
  );
}

export function ScorePill({ score }: { score: number | null }) {
  const color = scoreColor(score);
  return (
    <span
      className="inline-flex h-7 min-w-9 items-center justify-center rounded-lg px-2 text-sm font-bold tabular-nums"
      style={{ color, background: `${color}1f`, border: `1px solid ${color}33` }}
    >
      {score ?? "—"}
    </span>
  );
}

export function Chip({
  children,
  tone = "default",
}: {
  children: ReactNode;
  tone?: "default" | "accent" | "muted";
}) {
  const tones = {
    default: "border-slate-600/40 bg-slate-700/20 text-slate-300",
    accent: "border-indigo-500/30 bg-indigo-500/15 text-indigo-200",
    muted: "border-slate-700/40 bg-slate-800/30 text-slate-400",
  };
  return <span className={`chip ${tones[tone]}`}>{children}</span>;
}

export function EmptyState({
  title,
  hint,
}: {
  title: string;
  hint?: ReactNode;
}) {
  return (
    <div className="card grid place-items-center px-6 py-16 text-center">
      <div className="text-base font-medium">{title}</div>
      {hint && <div className="mt-1 max-w-md text-sm text-[var(--muted)]">{hint}</div>}
    </div>
  );
}

export function CardLink({
  href,
  children,
  external,
}: {
  href: string;
  children: ReactNode;
  external?: boolean;
}) {
  if (external)
    return (
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="text-indigo-300 hover:text-indigo-200 hover:underline"
      >
        {children}
      </a>
    );
  return (
    <Link href={href} className="hover:text-indigo-200">
      {children}
    </Link>
  );
}
