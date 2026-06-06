import { redirect } from "next/navigation";
import { Radar, Target, Building2, FileText, KanbanSquare } from "lucide-react";
import { auth, devLoginEnabled, googleEnabled } from "@/auth";
import { SignInButtons } from "@/components/SignInButtons";

export const dynamic = "force-dynamic";

const FEATURES = [
  {
    icon: Target,
    title: "Matched to you",
    desc: "Every job ranked against your profile, skills & experience.",
    color: "#34d399",
  },
  {
    icon: Building2,
    title: "100+ companies",
    desc: "India & remote roles from top product startups and global teams.",
    color: "#38bdf8",
  },
  {
    icon: FileText,
    title: "Tailored résumé",
    desc: "Generate a job-specific résumé PDF in one click.",
    color: "#a78bfa",
  },
  {
    icon: KanbanSquare,
    title: "Track applications",
    desc: "Move every role from saved to offer on your own board.",
    color: "#fbbf24",
  },
];

export default async function SignInPage() {
  const session = await auth();
  if (session?.user?.id) redirect("/");

  return (
    <div className="grid min-h-[88vh] place-items-center">
      <div className="card w-full max-w-md overflow-hidden">
        {/* header */}
        <div className="border-b border-[var(--border-soft)] bg-gradient-to-br from-indigo-500/15 via-transparent to-sky-500/10 px-8 pb-7 pt-9 text-center">
          <div className="glow-pulse mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-indigo-500 to-sky-500">
            <Radar size={26} className="text-white" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight">
            Welcome to JobScope
          </h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Your personalized job search, automated.
          </p>
        </div>

        {/* value props */}
        <div className="space-y-1 px-5 py-5">
          {FEATURES.map(({ icon: Icon, title, desc, color }) => (
            <div
              key={title}
              className="flex items-start gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-white/[0.04]"
            >
              <span
                className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-lg"
                style={{ background: `${color}1f`, color }}
              >
                <Icon size={17} />
              </span>
              <div className="leading-snug">
                <div className="text-sm font-medium">{title}</div>
                <div className="text-xs text-[var(--muted)]">{desc}</div>
              </div>
            </div>
          ))}
        </div>

        {/* sign-in */}
        <div className="border-t border-[var(--border-soft)] px-8 pb-8 pt-5">
          <SignInButtons
            googleEnabled={googleEnabled}
            devLoginEnabled={devLoginEnabled}
          />
          <p className="mt-4 text-center text-[11px] leading-relaxed text-[var(--muted)]/70">
            We only use your Google account to sign you in. Your profile and
            saved jobs stay private to you.
          </p>
        </div>
      </div>
    </div>
  );
}
