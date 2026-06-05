"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  PRIORITY_COLORS,
  ROLE_COLORS,
  ROLE_LABELS,
  roleLabel,
} from "@/lib/format";
import type { OverviewStats, Priority, RoleCategory } from "@/lib/types";

const AXIS = { fill: "#8b98ac", fontSize: 12 };
const BAR_PALETTE = [
  "#6366f1",
  "#38bdf8",
  "#34d399",
  "#fbbf24",
  "#f472b6",
  "#a78bfa",
  "#fb923c",
  "#2dd4bf",
];

interface TipItem {
  name?: string | number;
  value?: string | number;
  payload?: { label?: string; fill?: string };
}

function Tip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TipItem[];
  label?: string | number;
}) {
  if (!active || !payload?.length) return null;
  const p = payload[0];
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[#0c121e] px-3 py-2 text-xs shadow-xl">
      <div className="font-medium text-[var(--text)]">
        {p.payload?.label ?? label}
      </div>
      <div className="text-[var(--muted)]">
        {p.value} {Number(p.value) === 1 ? "job" : "jobs"}
      </div>
    </div>
  );
}

export function PriorityDonut({
  data,
}: {
  data: { priority: Priority; count: number }[];
}) {
  const order: Priority[] = ["HIGH", "MEDIUM", "LOW"];
  const rows = order
    .map((p) => ({
      label: p,
      value: data.find((d) => d.priority === p)?.count ?? 0,
      fill: PRIORITY_COLORS[p],
    }))
    .filter((r) => r.value > 0);
  const total = rows.reduce((s, r) => s + r.value, 0);

  return (
    <div className="relative h-56">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={rows}
            dataKey="value"
            nameKey="label"
            innerRadius={62}
            outerRadius={90}
            paddingAngle={2}
            stroke="none"
          >
            {rows.map((r) => (
              <Cell key={r.label} fill={r.fill} />
            ))}
          </Pie>
          <Tooltip content={<Tip />} />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-semibold tabular-nums">{total}</span>
        <span className="text-xs text-[var(--muted)]">scored</span>
      </div>
    </div>
  );
}

export function RoleBars({
  data,
}: {
  data: { role: RoleCategory; count: number }[];
}) {
  const rows = data
    .map((d) => ({
      label: ROLE_LABELS[d.role] ?? d.role,
      value: d.count,
      fill: ROLE_COLORS[d.role] ?? "#6366f1",
    }))
    .sort((a, b) => b.value - a.value);

  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 16 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="label"
            tick={AXIS}
            axisLine={false}
            tickLine={false}
            width={70}
          />
          <Tooltip content={<Tip />} cursor={{ fill: "#ffffff08" }} />
          <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={26}>
            {rows.map((r) => (
              <Cell key={r.label} fill={r.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function TopCompaniesBars({
  data,
}: {
  data: OverviewStats["topCompanies"];
}) {
  const rows = data.map((d) => ({
    label: d.company.length > 18 ? `${d.company.slice(0, 17)}…` : d.company,
    value: d.count,
  }));
  return (
    <div style={{ height: Math.max(220, rows.length * 30) }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 18 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="label"
            tick={AXIS}
            axisLine={false}
            tickLine={false}
            width={120}
          />
          <Tooltip content={<Tip />} cursor={{ fill: "#ffffff08" }} />
          <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={16}>
            {rows.map((_, i) => (
              <Cell key={i} fill={BAR_PALETTE[i % BAR_PALETTE.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SourceBars({
  data,
}: {
  data: { source: string; count: number }[];
}) {
  const rows = data.map((d) => ({ label: d.source, value: d.count }));
  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ left: -18, right: 8, top: 8 }}>
          <XAxis
            dataKey="label"
            tick={AXIS}
            axisLine={false}
            tickLine={false}
            interval={0}
            angle={-20}
            textAnchor="end"
            height={50}
          />
          <YAxis tick={AXIS} axisLine={false} tickLine={false} />
          <Tooltip content={<Tip />} cursor={{ fill: "#ffffff08" }} />
          <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={34}>
            {rows.map((_, i) => (
              <Cell key={i} fill={BAR_PALETTE[i % BAR_PALETTE.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ScoreHistogram({
  data,
}: {
  data: { bucket: string; count: number }[];
}) {
  const order = ["0-39", "40-54", "55-69", "70-84", "85-100"];
  const colors = ["#64748b", "#94a3b8", "#fbbf24", "#34d399", "#10b981"];
  const rows = order.map((b, i) => ({
    label: b,
    value: data.find((d) => d.bucket === b)?.count ?? 0,
    fill: colors[i],
  }));
  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ left: -18, right: 8, top: 8 }}>
          <XAxis dataKey="label" tick={AXIS} axisLine={false} tickLine={false} />
          <YAxis tick={AXIS} axisLine={false} tickLine={false} />
          <Tooltip content={<Tip />} cursor={{ fill: "#ffffff08" }} />
          <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={40}>
            {rows.map((r) => (
              <Cell key={r.label} fill={r.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function DiscoveryArea({
  data,
}: {
  data: { day: string; count: number }[];
}) {
  const rows = data.map((d) => ({
    label: new Date(d.day).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    }),
    value: d.count,
  }));
  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={rows} margin={{ left: -18, right: 8, top: 8 }}>
          <defs>
            <linearGradient id="disc" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366f1" stopOpacity={0.5} />
              <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="label"
            tick={AXIS}
            axisLine={false}
            tickLine={false}
            minTickGap={24}
          />
          <YAxis tick={AXIS} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip content={<Tip />} cursor={{ stroke: "#334155" }} />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#818cf8"
            strokeWidth={2}
            fill="url(#disc)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export { roleLabel };
