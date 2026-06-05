import { Briefcase, CalendarPlus, Building2, Sparkles, Target } from "lucide-react";
import { getOverviewForProfile } from "@/lib/queries";
import { requireProfile } from "@/lib/profile";
import { StatCard } from "@/components/StatCard";
import { PageHeader } from "@/components/ui";
import {
  DiscoveryArea,
  PriorityDonut,
  RoleBars,
  ScoreHistogram,
  SourceBars,
  TopCompaniesBars,
} from "@/components/charts";

export const dynamic = "force-dynamic";

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="card p-5">
      <div className="mb-4">
        <h2 className="text-sm font-semibold">{title}</h2>
        {subtitle && <p className="text-xs text-[var(--muted)]">{subtitle}</p>}
      </div>
      {children}
    </section>
  );
}

export default async function OverviewPage() {
  const { user, profile } = await requireProfile();
  const stats = await getOverviewForProfile(profile, user.id);
  const high = stats.byPriority.find((p) => p.priority === "HIGH")?.count ?? 0;
  const medium = stats.byPriority.find((p) => p.priority === "MEDIUM")?.count ?? 0;
  const firstName = (profile.fullName ?? user.name ?? "there").split(" ")[0];

  return (
    <>
      <PageHeader
        title={`Welcome back, ${firstName}`}
        subtitle="Jobs matched to your profile across India & remote."
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <StatCard
          label="Open jobs"
          value={stats.totalOpen.toLocaleString()}
          icon={<Briefcase size={16} />}
          accent="#6366f1"
        />
        <StatCard
          label="High match"
          value={high}
          sub={`${medium} medium`}
          icon={<Target size={16} />}
          accent="#34d399"
        />
        <StatCard
          label="New today"
          value={stats.newToday}
          icon={<CalendarPlus size={16} />}
          accent="#38bdf8"
        />
        <StatCard
          label="Companies"
          value={stats.companies}
          icon={<Building2 size={16} />}
          accent="#a78bfa"
        />
        <StatCard
          label="Scored"
          value={stats.scored.toLocaleString()}
          sub={`${stats.highMediumCount} actionable`}
          icon={<Sparkles size={16} />}
          accent="#fbbf24"
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <ChartCard title="Priority mix" subtitle="HIGH / MEDIUM / LOW">
          <PriorityDonut data={stats.byPriority} />
        </ChartCard>
        <ChartCard title="By role" subtitle="Across the three targets">
          <RoleBars data={stats.byRole} />
        </ChartCard>
        <ChartCard title="Match-score distribution">
          <ScoreHistogram data={stats.scoreBuckets} />
        </ChartCard>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <ChartCard title="Discoveries" subtitle="Last 30 days">
          <DiscoveryArea data={stats.discoveries} />
        </ChartCard>
        <ChartCard title="By source">
          <SourceBars data={stats.bySource} />
        </ChartCard>
        <ChartCard title="Top companies" subtitle="By open roles">
          <TopCompaniesBars data={stats.topCompanies} />
        </ChartCard>
      </div>
    </>
  );
}
