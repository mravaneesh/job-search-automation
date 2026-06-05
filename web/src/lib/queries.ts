import "server-only";
import { query, queryOne } from "./db";
import {
  passesProfileFilter,
  scoreJob,
  type JobRow,
  type Profile,
  type Scored,
} from "./scoring";
import type {
  ApplicationCard,
  CompanyRow,
  JobFacets,
  OverviewStats,
  Priority,
  RoleCategory,
} from "./types";

export type ScoredJob = JobRow & Scored & { application_status: string | null };

const COLS = `
  j.id, j.title, j.company_name, j.role_category, j.location, j.source,
  j.url, j.experience, j.employment_type, j.discovered_date, j.created_date,
  j.skills, j.description, j.salary_min, j.salary_max, j.currency,
  c.category, c.tier`;

type RawRow = JobRow & { application_status: string | null };

/** Load the shared corpus for the profile's roles, scored + filtered per user. */
async function loadScored(profile: Profile, userId: number): Promise<ScoredJob[]> {
  if (!profile.targetRoles.length) return [];
  const rows = await query<RawRow>(
    `SELECT ${COLS}, a.status AS application_status
     FROM jobs j
     LEFT JOIN companies c ON c.id = j.company_id
     LEFT JOIN applications a ON a.job_id = j.id AND a.user_id = $2
     WHERE j.status = 'open' AND j.role_category = ANY($1)`,
    [profile.targetRoles, userId],
  );
  const out: ScoredJob[] = [];
  for (const r of rows) {
    if (!passesProfileFilter(r, profile)) continue;
    out.push({ ...r, ...scoreJob(r, profile) });
  }
  out.sort((a, b) => b.match_score - a.match_score || b.id - a.id);
  return out;
}

export interface JobUiFilter {
  q?: string;
  role?: string;
  priority?: string;
  source?: string;
  company?: string;
  location?: string;
  minScore?: number;
  sort?: string;
  dir?: "asc" | "desc";
  page?: number;
  pageSize?: number;
}

function applyUiFilters(jobs: ScoredJob[], f: JobUiFilter): ScoredJob[] {
  let r = jobs;
  if (f.q) {
    const q = f.q.toLowerCase();
    r = r.filter(
      (j) =>
        j.title.toLowerCase().includes(q) ||
        j.company_name.toLowerCase().includes(q),
    );
  }
  if (f.role) r = r.filter((j) => j.role_category === f.role);
  if (f.priority) r = r.filter((j) => j.priority === f.priority);
  if (f.source) r = r.filter((j) => j.source === f.source);
  if (f.company)
    r = r.filter((j) =>
      j.company_name.toLowerCase().includes(f.company!.toLowerCase()),
    );
  if (f.location)
    r = r.filter((j) =>
      (j.location ?? "").toLowerCase().includes(f.location!.toLowerCase()),
    );
  if (f.minScore != null) r = r.filter((j) => j.match_score >= f.minScore!);
  return r;
}

function sortJobs(jobs: ScoredJob[], sort?: string, dir?: "asc" | "desc"): ScoredJob[] {
  const mul = dir === "asc" ? 1 : -1;
  const by: Record<string, (a: ScoredJob, b: ScoredJob) => number> = {
    score: (a, b) => a.match_score - b.match_score,
    discovered: (a, b) =>
      new Date(a.discovered_date).getTime() - new Date(b.discovered_date).getTime(),
    company: (a, b) => a.company_name.localeCompare(b.company_name),
    title: (a, b) => a.title.localeCompare(b.title),
  };
  const cmp = by[sort ?? "score"] ?? by.score;
  return [...jobs].sort((a, b) => mul * cmp(a, b) || b.id - a.id);
}

export async function getJobsForProfile(
  profile: Profile,
  userId: number,
  f: JobUiFilter,
): Promise<{ rows: ScoredJob[]; total: number; facets: JobFacets }> {
  const all = await loadScored(profile, userId);
  const facets: JobFacets = {
    sources: [...new Set(all.map((j) => j.source))].sort(),
    companies: [],
  };
  const filtered = sortJobs(applyUiFilters(all, f), f.sort, f.dir);
  const page = Math.max(1, f.page ?? 1);
  const pageSize = Math.min(100, Math.max(1, f.pageSize ?? 25));
  const start = (page - 1) * pageSize;
  return {
    rows: filtered.slice(start, start + pageSize),
    total: filtered.length,
    facets,
  };
}

export async function getJobDetail(
  profile: Profile,
  userId: number,
  id: number,
): Promise<ScoredJob | null> {
  const r = await queryOne<RawRow>(
    `SELECT ${COLS}, a.status AS application_status
     FROM jobs j
     LEFT JOIN companies c ON c.id = j.company_id
     LEFT JOIN applications a ON a.job_id = j.id AND a.user_id = $2
     WHERE j.id = $1`,
    [id, userId],
  );
  return r ? { ...r, ...scoreJob(r, profile) } : null;
}

export async function getOverviewForProfile(
  profile: Profile,
  userId: number,
): Promise<OverviewStats> {
  const jobs = await loadScored(profile, userId);
  const today = new Date().toISOString().slice(0, 10);

  const tally = <T extends string>(key: (j: ScoredJob) => T) => {
    const m = new Map<T, number>();
    for (const j of jobs) m.set(key(j), (m.get(key(j)) ?? 0) + 1);
    return m;
  };

  const prio = tally((j) => j.priority);
  const roles = tally((j) => j.role_category as RoleCategory);
  const sources = tally((j) => j.source);

  const companyMap = new Map<string, { count: number; high: number }>();
  for (const j of jobs) {
    const e = companyMap.get(j.company_name) ?? { count: 0, high: 0 };
    e.count += 1;
    if (j.priority === "HIGH") e.high += 1;
    companyMap.set(j.company_name, e);
  }
  const topCompanies = [...companyMap.entries()]
    .map(([company, v]) => ({ company, ...v }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 12);

  const bucketOf = (s: number) =>
    s >= 85 ? "85-100" : s >= 70 ? "70-84" : s >= 55 ? "55-69" : s >= 40 ? "40-54" : "0-39";
  const buckets = tally((j) => bucketOf(j.match_score));

  const dayMap = new Map<string, number>();
  const cutoff = Date.now() - 29 * 86_400_000;
  for (const j of jobs) {
    const d = new Date(j.discovered_date);
    if (d.getTime() < cutoff) continue;
    const day = d.toISOString().slice(0, 10);
    dayMap.set(day, (dayMap.get(day) ?? 0) + 1);
  }
  const discoveries = [...dayMap.entries()]
    .map(([day, count]) => ({ day, count }))
    .sort((a, b) => a.day.localeCompare(b.day));

  return {
    totalOpen: jobs.length,
    newToday: jobs.filter(
      (j) => new Date(j.discovered_date).toISOString().slice(0, 10) === today,
    ).length,
    companies: new Set(jobs.map((j) => j.company_name)).size,
    scored: jobs.length,
    highMediumCount: (prio.get("HIGH") ?? 0) + (prio.get("MEDIUM") ?? 0),
    byPriority: (["HIGH", "MEDIUM", "LOW"] as Priority[]).map((p) => ({
      priority: p,
      count: prio.get(p) ?? 0,
    })),
    byRole: [...roles.entries()].map(([role, count]) => ({ role, count })),
    bySource: [...sources.entries()]
      .map(([source, count]) => ({ source, count }))
      .sort((a, b) => b.count - a.count),
    topCompanies,
    scoreBuckets: [...buckets.entries()].map(([bucket, count]) => ({ bucket, count })),
    discoveries,
  };
}

export async function getApplicationsBoard(
  profile: Profile,
  userId: number,
): Promise<ApplicationCard[]> {
  const rows = await query<RawRow & { status: string; last_update: string }>(
    `SELECT ${COLS}, a.status, a.last_update, a.status AS application_status
     FROM applications a
     JOIN jobs j ON j.id = a.job_id
     LEFT JOIN companies c ON c.id = j.company_id
     WHERE a.user_id = $1
     ORDER BY a.last_update DESC`,
    [userId],
  );
  return rows.map((r) => {
    const s = scoreJob(r, profile);
    return {
      job_id: r.id,
      status: r.status,
      title: r.title,
      company_name: r.company_name,
      role_category: r.role_category as RoleCategory,
      location: r.location,
      url: r.url,
      match_score: s.match_score,
      priority: s.priority,
      last_update: r.last_update,
    };
  });
}

export async function getCompaniesForProfile(
  profile: Profile,
  userId: number,
): Promise<CompanyRow[]> {
  const jobs = await loadScored(profile, userId);
  const m = new Map<string, CompanyRow>();
  for (const j of jobs) {
    const e =
      m.get(j.company_name) ??
      ({
        name: j.company_name,
        category: j.category,
        tier: j.tier,
        total: 0,
        high: 0,
        medium: 0,
      } as CompanyRow);
    e.total += 1;
    if (j.priority === "HIGH") e.high += 1;
    if (j.priority === "MEDIUM") e.medium += 1;
    m.set(j.company_name, e);
  }
  return [...m.values()].sort((a, b) => b.total - a.total);
}
