import Link from "next/link";
import { getCompaniesForProfile } from "@/lib/queries";
import { requireProfile } from "@/lib/profile";
import { Chip, PageHeader } from "@/components/ui";

export const dynamic = "force-dynamic";

const TIER_TONE: Record<string, string> = {
  tier1: "border-amber-500/30 bg-amber-500/10 text-amber-300",
  tier2: "border-sky-500/30 bg-sky-500/10 text-sky-300",
  tier3: "border-slate-600/40 bg-slate-700/20 text-slate-300",
};

export default async function CompaniesPage() {
  const { user, profile } = await requireProfile();
  const companies = await getCompaniesForProfile(profile, user.id);
  const totalRoles = companies.reduce((s, c) => s + c.total, 0);

  return (
    <>
      <PageHeader
        title="Companies"
        subtitle={`${companies.length} companies · ${totalRoles.toLocaleString()} roles`}
      />

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-left text-xs uppercase tracking-wide text-[var(--muted)]">
                <th className="px-4 py-3 font-medium">Company</th>
                <th className="px-4 py-3 font-medium">Category</th>
                <th className="px-4 py-3 font-medium">Tier</th>
                <th className="px-4 py-3 text-right font-medium">Roles</th>
                <th className="px-4 py-3 text-right font-medium">High</th>
                <th className="px-4 py-3 text-right font-medium">Medium</th>
              </tr>
            </thead>
            <tbody>
              {companies.map((c) => (
                <tr
                  key={c.name}
                  className="border-b border-[var(--border-soft)] last:border-0 transition hover:bg-white/[0.025]"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/jobs?company=${encodeURIComponent(c.name)}`}
                      className="font-medium hover:text-indigo-200"
                    >
                      {c.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-[var(--muted)]">
                    {c.category ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    {c.tier ? (
                      <span className={`chip ${TIER_TONE[c.tier] ?? TIER_TONE.tier3}`}>
                        {c.tier}
                      </span>
                    ) : (
                      <span className="text-[var(--muted)]">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">{c.total}</td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {c.high > 0 ? (
                      <span className="text-emerald-300">{c.high}</span>
                    ) : (
                      <span className="text-[var(--muted)]">0</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {c.medium > 0 ? (
                      <span className="text-amber-300">{c.medium}</span>
                    ) : (
                      <span className="text-[var(--muted)]">0</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <p className="mt-3 text-xs text-[var(--muted)]">
        Tip: click a company to see its roles. <Chip tone="accent">High</Chip>{" "}
        counts are HIGH-priority matches.
      </p>
    </>
  );
}
