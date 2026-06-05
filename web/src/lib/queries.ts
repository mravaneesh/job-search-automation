import "server-only";
import { query, queryOne } from "./db";
import type {
  ApplicationCard,
  CompanyRow,
  JobDetail,
  JobFacets,
  JobListItem,
  OverviewStats,
} from "./types";

export async function getOverviewStats(): Promise<OverviewStats> {
  const [
    totals,
    byPriority,
    byRole,
    bySource,
    topCompanies,
    scoreBuckets,
    discoveries,
  ] = await Promise.all([
    queryOne<{
      total_open: number;
      new_today: number;
      companies: number;
      scored: number;
      high_medium: number;
    }>(`
      SELECT
        count(*) FILTER (WHERE j.status = 'open')::int AS total_open,
        count(*) FILTER (WHERE j.discovered_date::date = current_date)::int AS new_today,
        count(DISTINCT j.company_name)::int AS companies,
        (SELECT count(*) FROM job_scores)::int AS scored,
        (SELECT count(*) FROM job_scores WHERE priority IN ('HIGH','MEDIUM'))::int AS high_medium
      FROM jobs j
    `),
    query<{ priority: string; count: number }>(
      `SELECT priority, count(*)::int AS count FROM job_scores GROUP BY priority`,
    ),
    query<{ role: string; count: number }>(
      `SELECT role_category AS role, count(*)::int AS count FROM jobs GROUP BY role_category`,
    ),
    query<{ source: string; count: number }>(
      `SELECT source, count(*)::int AS count FROM jobs GROUP BY source ORDER BY count DESC`,
    ),
    query<{ company: string; count: number; high: number }>(`
      SELECT j.company_name AS company,
             count(*)::int AS count,
             count(*) FILTER (WHERE s.priority = 'HIGH')::int AS high
      FROM jobs j
      LEFT JOIN job_scores s ON s.job_id = j.id
      GROUP BY j.company_name
      ORDER BY count DESC
      LIMIT 12
    `),
    query<{ bucket: string; count: number }>(`
      SELECT CASE
               WHEN match_score >= 85 THEN '85-100'
               WHEN match_score >= 70 THEN '70-84'
               WHEN match_score >= 55 THEN '55-69'
               WHEN match_score >= 40 THEN '40-54'
               ELSE '0-39'
             END AS bucket,
             count(*)::int AS count
      FROM job_scores
      GROUP BY bucket
    `),
    query<{ day: string; count: number }>(`
      SELECT discovered_date::date AS day, count(*)::int AS count
      FROM jobs
      WHERE discovered_date >= current_date - INTERVAL '29 days'
      GROUP BY day
      ORDER BY day
    `),
  ]);

  return {
    totalOpen: totals?.total_open ?? 0,
    newToday: totals?.new_today ?? 0,
    companies: totals?.companies ?? 0,
    scored: totals?.scored ?? 0,
    highMediumCount: totals?.high_medium ?? 0,
    byPriority: byPriority.map((r) => ({
      priority: r.priority as OverviewStats["byPriority"][number]["priority"],
      count: r.count,
    })),
    byRole: byRole.map((r) => ({
      role: r.role as OverviewStats["byRole"][number]["role"],
      count: r.count,
    })),
    bySource,
    topCompanies,
    scoreBuckets,
    discoveries: discoveries.map((d) => ({
      day: new Date(d.day).toISOString().slice(0, 10),
      count: d.count,
    })),
  };
}

export interface JobQuery {
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

const SORT_COLUMNS: Record<string, string> = {
  score: "s.match_score",
  discovered: "j.discovered_date",
  company: "j.company_name",
  title: "j.title",
};

export async function getJobs(
  f: JobQuery,
): Promise<{ rows: JobListItem[]; total: number }> {
  const where: string[] = [];
  const params: unknown[] = [];
  const push = (value: unknown) => {
    params.push(value);
    return `$${params.length}`;
  };

  if (f.q) {
    const p = push(`%${f.q}%`);
    where.push(`(j.title ILIKE ${p} OR j.company_name ILIKE ${p})`);
  }
  if (f.role) where.push(`j.role_category = ${push(f.role)}`);
  if (f.source) where.push(`j.source = ${push(f.source)}`);
  if (f.company) where.push(`j.company_name ILIKE ${push(`%${f.company}%`)}`);
  if (f.location) where.push(`j.location ILIKE ${push(`%${f.location}%`)}`);
  if (f.priority) where.push(`s.priority = ${push(f.priority)}`);
  if (f.minScore != null) where.push(`COALESCE(s.match_score, 0) >= ${push(f.minScore)}`);

  const whereSql = where.length ? `WHERE ${where.join(" AND ")}` : "";

  const sortCol = SORT_COLUMNS[f.sort ?? "score"] ?? SORT_COLUMNS.score;
  const dir = f.dir === "asc" ? "ASC" : "DESC";
  const page = Math.max(1, f.page ?? 1);
  const pageSize = Math.min(100, Math.max(1, f.pageSize ?? 25));
  const offset = (page - 1) * pageSize;

  const totalRow = await queryOne<{ count: number }>(
    `SELECT count(*)::int AS count
     FROM jobs j
     LEFT JOIN job_scores s ON s.job_id = j.id
     ${whereSql}`,
    params,
  );

  const rows = await query<JobListItem>(
    `SELECT j.id, j.title, j.company_name, j.role_category, j.location, j.source,
            j.url, j.experience, j.discovered_date,
            s.match_score, s.priority, c.tier,
            a.status AS application_status
     FROM jobs j
     LEFT JOIN job_scores s ON s.job_id = j.id
     LEFT JOIN companies c ON c.id = j.company_id
     LEFT JOIN applications a ON a.job_id = j.id
     ${whereSql}
     ORDER BY ${sortCol} ${dir} NULLS LAST, j.id DESC
     LIMIT ${pageSize} OFFSET ${offset}`,
    params,
  );

  return { rows, total: totalRow?.count ?? 0 };
}

export async function getJobFacets(): Promise<JobFacets> {
  const sources = await query<{ source: string }>(
    `SELECT DISTINCT source FROM jobs ORDER BY source`,
  );
  const companies = await query<{ company_name: string }>(
    `SELECT company_name FROM jobs GROUP BY company_name ORDER BY count(*) DESC LIMIT 300`,
  );
  return {
    sources: sources.map((s) => s.source),
    companies: companies.map((c) => c.company_name),
  };
}

export async function getJob(id: number): Promise<JobDetail | null> {
  return queryOne<JobDetail>(
    `SELECT j.id, j.title, j.company_name, j.role_category, j.location, j.source,
            j.url, j.experience, j.discovered_date, j.description, j.employment_type,
            j.skills, j.created_date, j.salary_min, j.salary_max, j.currency,
            c.tier, c.category,
            s.match_score, s.priority, s.skill_score, s.experience_score,
            s.location_score, s.seniority_score, s.company_score,
            s.interview_likelihood, s.matched_skills, s.missing_skills, s.scored_by,
            a.status AS application_status
     FROM jobs j
     LEFT JOIN job_scores s ON s.job_id = j.id
     LEFT JOIN companies c ON c.id = j.company_id
     LEFT JOIN applications a ON a.job_id = j.id
     WHERE j.id = $1`,
    [id],
  );
}

export async function getApplicationsBoard(): Promise<ApplicationCard[]> {
  return query<ApplicationCard>(`
    SELECT a.job_id, a.status, a.last_update,
           j.title, j.company_name, j.role_category, j.location, j.url,
           s.match_score, s.priority
    FROM applications a
    JOIN jobs j ON j.id = a.job_id
    LEFT JOIN job_scores s ON s.job_id = j.id
    ORDER BY a.last_update DESC
  `);
}

export async function getCompanies(): Promise<CompanyRow[]> {
  return query<CompanyRow>(`
    SELECT j.company_name AS name,
           max(c.category) AS category,
           max(c.tier) AS tier,
           count(*)::int AS total,
           count(*) FILTER (WHERE s.priority = 'HIGH')::int AS high,
           count(*) FILTER (WHERE s.priority = 'MEDIUM')::int AS medium
    FROM jobs j
    LEFT JOIN companies c ON c.id = j.company_id
    LEFT JOIN job_scores s ON s.job_id = j.id
    GROUP BY j.company_name
    ORDER BY total DESC
  `);
}
