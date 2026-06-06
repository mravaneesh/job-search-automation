import Link from "next/link";
import { ExternalLink, MapPin, CheckCircle2 } from "lucide-react";
import { getJobsForProfile, type JobUiFilter } from "@/lib/queries";
import { requireProfile } from "@/lib/profile";
import { JobFilters } from "@/components/JobFilters";
import { Pagination } from "@/components/Pagination";
import { PageHeader, PriorityBadge, RoleBadge, ScorePill } from "@/components/ui";
import { relativeDay } from "@/lib/format";

export const dynamic = "force-dynamic";

const PAGE_SIZE = 25;

function first(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

export default async function JobsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { user, profile } = await requireProfile();
  const sp = await searchParams;
  const minScoreRaw = first(sp.minScore);
  const filter: JobUiFilter = {
    q: first(sp.q),
    role: first(sp.role),
    priority: first(sp.priority),
    source: first(sp.source),
    company: first(sp.company),
    location: first(sp.location),
    minScore: minScoreRaw ? Number(minScoreRaw) : undefined,
    sort: first(sp.sort),
    dir: first(sp.dir) === "asc" ? "asc" : "desc",
    page: Number(first(sp.page) ?? 1) || 1,
    pageSize: PAGE_SIZE,
  };

  const { rows, total, facets } = await getJobsForProfile(profile, user.id, filter);

  return (
    <>
      <PageHeader
        title="Jobs"
        subtitle={`${total.toLocaleString()} matching roles`}
      />

      <JobFilters sources={facets.sources} />

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-left text-xs uppercase tracking-wide text-[var(--muted)]">
                <th className="px-4 py-3 font-medium">Job</th>
                <th className="px-4 py-3 font-medium">Location</th>
                <th className="px-4 py-3 font-medium">Experience</th>
                <th className="px-4 py-3 text-center font-medium">Score</th>
                <th className="px-4 py-3 font-medium">Priority</th>
                <th className="px-4 py-3 font-medium">Source</th>
                <th className="px-4 py-3 font-medium">Found</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {rows.map((job) => (
                <tr
                  key={job.id}
                  className="group border-b border-[var(--border-soft)] last:border-0 transition hover:bg-white/[0.025]"
                >
                  <td className="max-w-[420px] px-4 py-3">
                    <Link
                      href={`/jobs/${job.id}`}
                      className="line-clamp-1 font-medium text-[var(--text)] group-hover:text-indigo-200"
                    >
                      {job.title}
                    </Link>
                    <div className="mt-0.5 flex items-center gap-1.5 text-xs text-[var(--muted)]">
                      <RoleBadge role={job.role_category} />
                      <span className="truncate">{job.company_name}</span>
                      {job.application_status && (
                        <span className="inline-flex items-center gap-1 text-emerald-400">
                          <CheckCircle2 size={12} /> tracked
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="max-w-[200px] px-4 py-3 text-[var(--muted)]">
                    <span className="flex items-center gap-1">
                      <MapPin size={13} className="shrink-0 opacity-60" />
                      <span className="line-clamp-1">{job.location ?? "—"}</span>
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    {job.experience ? (
                      <span className="rounded-md border border-[var(--border)] bg-white/[0.03] px-2 py-0.5 text-xs text-slate-300">
                        {job.experience}
                      </span>
                    ) : (
                      <span className="text-xs text-[var(--muted)]">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <ScorePill score={job.match_score} />
                  </td>
                  <td className="px-4 py-3">
                    <PriorityBadge priority={job.priority} />
                  </td>
                  <td className="px-4 py-3 text-[var(--muted)]">{job.source}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-xs text-[var(--muted)]">
                    {relativeDay(job.discovered_date)}
                  </td>
                  <td className="px-4 py-3">
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noreferrer"
                      title="Open posting"
                      className="grid h-7 w-7 place-items-center rounded-md text-[var(--muted)] transition hover:bg-indigo-500/15 hover:text-indigo-200"
                    >
                      <ExternalLink size={15} />
                    </a>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td
                    colSpan={8}
                    className="px-4 py-16 text-center text-[var(--muted)]"
                  >
                    No jobs match these filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <Pagination page={filter.page ?? 1} pageSize={PAGE_SIZE} total={total} />
    </>
  );
}
