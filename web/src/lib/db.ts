import "server-only";
import { Pool, type QueryResultRow } from "pg";

const connectionString =
  process.env.DATABASE_URL ??
  "postgresql://jobsearch:jobsearch@localhost:5432/jobsearch";

// Reuse a single pool across HMR reloads in dev.
const globalForPg = globalThis as unknown as { _pgPool?: Pool };

export const pool =
  globalForPg._pgPool ?? new Pool({ connectionString, max: 5 });

if (process.env.NODE_ENV !== "production") globalForPg._pgPool = pool;

export async function query<T extends QueryResultRow = QueryResultRow>(
  text: string,
  params?: unknown[],
): Promise<T[]> {
  const res = await pool.query<T>(text, params as never[]);
  return res.rows;
}

export async function queryOne<T extends QueryResultRow = QueryResultRow>(
  text: string,
  params?: unknown[],
): Promise<T | null> {
  const rows = await query<T>(text, params);
  return rows[0] ?? null;
}
