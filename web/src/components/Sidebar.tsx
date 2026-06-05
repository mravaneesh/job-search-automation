"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Briefcase,
  KanbanSquare,
  Building2,
  Radar,
  UserCog,
  LogOut,
} from "lucide-react";
import { doSignOut } from "@/lib/actions";

const NAV = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/jobs", label: "Jobs", icon: Briefcase },
  { href: "/applications", label: "Applications", icon: KanbanSquare },
  { href: "/companies", label: "Companies", icon: Building2 },
  { href: "/onboarding", label: "My profile", icon: UserCog },
];

export interface NavUser {
  name: string | null;
  email: string | null;
  image: string | null;
}

export function Sidebar({ user }: { user: NavUser | null }) {
  const pathname = usePathname();

  // No chrome on the auth/onboarding screens.
  if (!user || pathname === "/signin" || pathname === "/onboarding") return null;

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

      <div className="mt-auto border-t border-[var(--border-soft)] pt-3">
        <div className="flex items-center gap-2.5 px-2 py-2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          {user.image ? (
            <img
              src={user.image}
              alt=""
              className="h-8 w-8 rounded-full"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="grid h-8 w-8 place-items-center rounded-full bg-indigo-500/20 text-xs font-semibold text-indigo-200">
              {(user.name ?? user.email ?? "?").slice(0, 1).toUpperCase()}
            </div>
          )}
          <div className="min-w-0 leading-tight">
            <div className="truncate text-xs font-medium">
              {user.name ?? "You"}
            </div>
            <div className="truncate text-[11px] text-[var(--muted)]">
              {user.email}
            </div>
          </div>
        </div>
        <form action={doSignOut}>
          <button
            type="submit"
            className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-[var(--muted)] transition hover:bg-white/5 hover:text-rose-300"
          >
            <LogOut size={14} /> Sign out
          </button>
        </form>
      </div>
    </aside>
  );
}
