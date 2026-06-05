import type { ReactNode } from "react";

export function StatCard({
  label,
  value,
  sub,
  icon,
  accent = "#6366f1",
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  icon?: ReactNode;
  accent?: string;
}) {
  return (
    <div className="card panel-hover p-4">
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-[var(--muted)]">
          {label}
        </span>
        {icon && (
          <span
            className="grid h-8 w-8 place-items-center rounded-lg"
            style={{ background: `${accent}1f`, color: accent }}
          >
            {icon}
          </span>
        )}
      </div>
      <div className="mt-2 text-3xl font-semibold tabular-nums">{value}</div>
      {sub && <div className="mt-1 text-xs text-[var(--muted)]">{sub}</div>}
    </div>
  );
}
