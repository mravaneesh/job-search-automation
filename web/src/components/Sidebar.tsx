"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Briefcase,
  KanbanSquare,
  Building2,
  Radar,
} from "lucide-react";

const NAV = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/jobs", label: "Jobs", icon: Briefcase },
  { href: "/applications", label: "Applications", icon: KanbanSquare },
  { href: "/companies", label: "Companies", icon: Building2 },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-[var(--border-soft)] bg-[var(--panel-2)]/60 px-3 py-5 backdrop-blur md:flex">
      <div className="flex items-center gap-2.5 px-2 pb-6">
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-sky-500 shadow-lg shadow-indigo-500/20">
          <Radar size={18} className="text-white" />
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold">JobScope</div>
          <div className="text-[11px] text-[var(--muted)]">India · Remote</div>
        </div>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                active
                  ? "bg-indigo-500/15 text-indigo-200 ring-1 ring-inset ring-indigo-500/25"
                  : "text-[var(--muted)] hover:bg-white/5 hover:text-[var(--text)]"
              }`}
            >
              <Icon size={17} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto px-3 pt-6 text-[11px] leading-relaxed text-[var(--muted)]">
        Data refreshed by the Python pipeline.
        <br />
        Run <code className="text-indigo-300">jobsearch collect</code> to update.
      </div>
    </aside>
  );
}
