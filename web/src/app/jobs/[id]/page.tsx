import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { getJobDetail } from "@/lib/queries";
import { requireProfile } from "@/lib/profile";
import { StatusControl } from "@/components/StatusControl";
import { Chip, PriorityBadge, RoleBadge, ScorePill } from "@/components/ui";
import { formatDate, formatSalary, scoreColor } from "@/lib/format";

export const dynamic = "force-dynamic";

const DIMENSIONS: { key: keyof ScoreFields; label: string }[] = [
  { key: "skill_score", label: "Skill match" },
  { key: "experience_score", label: "Experience" },
  { key: "location_score", label: "Location" },
  { key: "seniority_score", label: "Seniority" },
  { key: "company_score", label: "Company quality" },
  { key: "interview_likelihood", label: "Interview likelihood" },
];

interface ScoreFields {
  skill_score: number | null;
  experience_score: number | null;
  location_score: number | null;
  seniority_score: number | null;
  company_score: number | null;
  interview_likelihood: number | null;
}

function Bar({ label, value }: { label: string; value: number | null }) {
  const v = value ?? 0;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-[var(--muted)]">{label}</span>
        <span className="tabular-nums" style={{ color: scoreColor(v) }}>
          {value ?? "—"}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white/5">
        <div
          className="h-full rounded-full"
          style={{ width: `${v}%`, background: scoreColor(v) }}
        />
      </div>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 py-2 text-sm">
      <span className="text-[var(--muted)]">{label}</span>
      <span className="text-right font-medium">{value || "—"}</span>
    </div>
  );
}

export default async function JobDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const { user, profile } = await requireProfile();
  const job = await getJobDetail(profile, user.id, Number(id));
  if (!job) notFound();

  const salary = formatSalary(job.salary_min, job.salary_max, job.currency);

  return (
    <div className="mx-auto max-w-5xl">
      <Link
        href="/jobs"
        className="mb-5 inline-flex items-center gap-1.5 text-sm text-[var(--muted)] transition hover:text-[var(--text)]"
      >
        <ArrowLeft size={15} /> Back to jobs
      </Link>

      <div className="card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <RoleBadge role={job.role_category} />
              <PriorityBadge priority={job.priority} />
              {job.tier && <Chip tone="muted">{job.tier}</Chip>}
            </div>
            <h1 className="text-2xl font-semibold tracking-tight">{job.title}</h1>
            <p className="mt-1 text-[var(--muted)]">
              {job.company_name}
              {job.location ? ` · ${job.location}` : ""}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {job.match_score != null && <ScorePill score={job.match_score} />}
            <StatusControl jobId={job.id} status={job.application_status} />
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <a
            href={job.url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-xl border border-indigo-500/40 bg-indigo-500/10 px-4 py-2 text-sm font-medium text-indigo-200 transition hover:bg-indigo-500/20"
          >
            Open original posting <ExternalLink size={15} />
          </a>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[1.6fr_1fr]">
        <div className="space-y-4">
          {(job.matched_skills?.length > 0 || job.missing_skills?.length > 0) && (
            <section className="card p-5">
              <h2 className="mb-3 text-sm font-semibold">Skills</h2>
              {job.matched_skills?.length > 0 && (
                <div className="mb-3">
                  <div className="mb-1.5 text-xs text-[var(--muted)]">Matched</div>
                  <div className="flex flex-wrap gap-1.5">
                    {job.matched_skills.map((s) => (
                      <span
                        key={s}
                        className="chip border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {job.missing_skills?.length > 0 && (
                <div>
                  <div className="mb-1.5 text-xs text-[var(--muted)]">Missing</div>
                  <div className="flex flex-wrap gap-1.5">
                    {job.missing_skills.map((s) => (
                      <span
                        key={s}
                        className="chip border-rose-500/25 bg-rose-500/10 text-rose-300"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </section>
          )}

          <section className="card p-5">
            <h2 className="mb-3 text-sm font-semibold">Description</h2>
            {job.description ? (
              <p className="whitespace-pre-line text-sm leading-relaxed text-slate-300">
                {job.description.slice(0, 6000)}
              </p>
            ) : (
              <p className="text-sm text-[var(--muted)]">
                No description captured for this source. Use “Open original
                posting” for full details.
              </p>
            )}
          </section>
        </div>

        <div className="space-y-4">
          {job.match_score != null && (
            <section className="card p-5">
              <h2 className="mb-4 text-sm font-semibold">Score breakdown</h2>
              <div className="space-y-3">
                {DIMENSIONS.map((d) => (
                  <Bar key={d.key} label={d.label} value={job[d.key]} />
                ))}
              </div>
              <p className="mt-4 text-xs text-[var(--muted)]">
                Scored against your profile
              </p>
            </section>
          )}

          <section className="card p-5">
            <h2 className="mb-2 text-sm font-semibold">Details</h2>
            <div className="divide-y divide-[var(--border-soft)]">
              <Meta label="Company" value={job.company_name} />
              <Meta label="Location" value={job.location} />
              <Meta label="Experience" value={job.experience} />
              <Meta label="Employment" value={job.employment_type} />
              {salary && <Meta label="Salary" value={salary} />}
              <Meta label="Source" value={job.source} />
              <Meta label="Category" value={job.category} />
              <Meta label="Posted" value={formatDate(job.created_date)} />
              <Meta label="Discovered" value={formatDate(job.discovered_date)} />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
