import type { Priority, RoleCategory } from "./types";

export const ROLE_LABELS: Record<RoleCategory, string> = {
  android: "Android",
  ios: "iOS",
  frontend: "Frontend",
  fullstack: "Full Stack",
  backend: "Backend",
  devops: "DevOps",
  data_engineering: "Data Eng",
  ai_ml: "AI/ML",
};

export const ROLE_COLORS: Record<RoleCategory, string> = {
  android: "#34d399", // emerald
  ios: "#60a5fa", // blue
  frontend: "#f472b6", // pink
  fullstack: "#fb923c", // orange
  backend: "#38bdf8", // sky
  devops: "#2dd4bf", // teal
  data_engineering: "#facc15", // amber
  ai_ml: "#a78bfa", // violet
};

export const PRIORITY_COLORS: Record<Priority, string> = {
  HIGH: "#34d399",
  MEDIUM: "#fbbf24",
  LOW: "#64748b",
};

export const PRIORITY_BADGE: Record<Priority, string> = {
  HIGH: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  MEDIUM: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  LOW: "bg-slate-500/15 text-slate-300 border-slate-500/30",
};

// Ordered application funnel.
export const APPLICATION_STATUSES = [
  "SAVED",
  "READY_TO_APPLY",
  "APPLIED",
  "RECRUITER_SCREEN",
  "ONLINE_ASSESSMENT",
  "TECHNICAL",
  "FINAL",
  "OFFER",
  "REJECTED",
] as const;

export const STATUS_LABELS: Record<string, string> = {
  SAVED: "Saved",
  READY_TO_APPLY: "Ready",
  APPLIED: "Applied",
  RECRUITER_SCREEN: "Recruiter",
  ONLINE_ASSESSMENT: "Assessment",
  TECHNICAL: "Technical",
  FINAL: "Final",
  OFFER: "Offer",
  REJECTED: "Rejected",
};

export const STATUS_ACCENT: Record<string, string> = {
  SAVED: "#64748b",
  READY_TO_APPLY: "#38bdf8",
  APPLIED: "#6366f1",
  RECRUITER_SCREEN: "#a78bfa",
  ONLINE_ASSESSMENT: "#f59e0b",
  TECHNICAL: "#f97316",
  FINAL: "#14b8a6",
  OFFER: "#34d399",
  REJECTED: "#ef4444",
};

export function roleLabel(role: string): string {
  return ROLE_LABELS[role as RoleCategory] ?? role;
}

export function scoreColor(score: number | null): string {
  if (score == null) return "#64748b";
  if (score >= 75) return "#34d399";
  if (score >= 55) return "#fbbf24";
  return "#94a3b8";
}

export function formatDate(value: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function relativeDay(value: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  const days = Math.floor((Date.now() - d.getTime()) / 86_400_000);
  if (days <= 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 30) return `${days}d ago`;
  return formatDate(value);
}

export function formatSalary(
  min: number | null,
  max: number | null,
  currency: string | null,
): string | null {
  if (min == null && max == null) return null;
  const cur = currency ?? "";
  const fmt = (n: number) =>
    n >= 100000 ? `${(n / 100000).toFixed(1)}L` : n.toLocaleString();
  if (min != null && max != null) return `${cur} ${fmt(min)}–${fmt(max)}`.trim();
  return `${cur} ${fmt((min ?? max)!)}`.trim();
}
