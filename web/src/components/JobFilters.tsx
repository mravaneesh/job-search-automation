"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { Search, X } from "lucide-react";

const ROLES = [
  { v: "", label: "All roles" },
  { v: "android", label: "Android" },
  { v: "ios", label: "iOS" },
  { v: "frontend", label: "Frontend" },
  { v: "fullstack", label: "Full Stack" },
  { v: "backend", label: "Backend" },
  { v: "devops", label: "DevOps" },
  { v: "data_engineering", label: "Data Eng" },
  { v: "ai_ml", label: "AI/ML" },
  { v: "software", label: "Software" },
];
const PRIORITIES = [
  { v: "", label: "Any priority" },
  { v: "HIGH", label: "High" },
  { v: "MEDIUM", label: "Medium" },
  { v: "LOW", label: "Low" },
];
const MIN_SCORES = [
  { v: "", label: "Any score" },
  { v: "55", label: "55+" },
  { v: "70", label: "70+" },
  { v: "85", label: "85+" },
];
const SORTS = [
  { v: "score_desc", label: "Score ↓" },
  { v: "score_asc", label: "Score ↑" },
  { v: "discovered_desc", label: "Newest" },
  { v: "company_asc", label: "Company A→Z" },
  { v: "title_asc", label: "Title A→Z" },
];

export function JobFilters({ sources }: { sources: string[] }) {
  const router = useRouter();
  const pathname = usePathname();
  const sp = useSearchParams();
  const spRef = useRef(sp);
  spRef.current = sp;

  const setParam = useCallback(
    (updates: Record<string, string | undefined>) => {
      const params = new URLSearchParams(spRef.current.toString());
      for (const [k, v] of Object.entries(updates)) {
        if (!v) params.delete(k);
        else params.set(k, v);
      }
      if (!("page" in updates)) params.delete("page");
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [pathname, router],
  );

  const [q, setQ] = useState(sp.get("q") ?? "");
  const [company, setCompany] = useState(sp.get("company") ?? "");
  const [location, setLocation] = useState(sp.get("location") ?? "");

  useDebouncedSync(q, "q", setParam);
  useDebouncedSync(company, "company", setParam);
  useDebouncedSync(location, "location", setParam);

  const sort = `${sp.get("sort") ?? "score"}_${sp.get("dir") ?? "desc"}`;
  const hasFilters = Array.from(sp.keys()).some((k) => k !== "page");

  return (
    <div className="card mb-4 flex flex-wrap items-center gap-2 p-3">
      <label className="relative min-w-52 flex-1">
        <Search
          size={15}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
        />
        <input
          className="input w-full pl-9"
          placeholder="Search title or company…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </label>

      <select
        className="input"
        value={sp.get("role") ?? ""}
        onChange={(e) => setParam({ role: e.target.value })}
      >
        {ROLES.map((o) => (
          <option key={o.v} value={o.v}>
            {o.label}
          </option>
        ))}
      </select>

      <select
        className="input"
        value={sp.get("priority") ?? ""}
        onChange={(e) => setParam({ priority: e.target.value })}
      >
        {PRIORITIES.map((o) => (
          <option key={o.v} value={o.v}>
            {o.label}
          </option>
        ))}
      </select>

      <select
        className="input"
        value={sp.get("source") ?? ""}
        onChange={(e) => setParam({ source: e.target.value })}
      >
        <option value="">All sources</option>
        {sources.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>

      <select
        className="input"
        value={sp.get("minScore") ?? ""}
        onChange={(e) => setParam({ minScore: e.target.value })}
      >
        {MIN_SCORES.map((o) => (
          <option key={o.v} value={o.v}>
            {o.label}
          </option>
        ))}
      </select>

      <input
        className="input w-32"
        placeholder="Company"
        value={company}
        onChange={(e) => setCompany(e.target.value)}
      />
      <input
        className="input w-32"
        placeholder="Location"
        value={location}
        onChange={(e) => setLocation(e.target.value)}
      />

      <select
        className="input"
        value={sort}
        onChange={(e) => {
          const [s, d] = e.target.value.split("_");
          setParam({ sort: s, dir: d });
        }}
      >
        {SORTS.map((o) => (
          <option key={o.v} value={o.v}>
            {o.label}
          </option>
        ))}
      </select>

      {hasFilters && (
        <button
          onClick={() => {
            setQ("");
            setCompany("");
            setLocation("");
            router.replace(pathname, { scroll: false });
          }}
          className="flex items-center gap-1 rounded-lg border border-[var(--border)] px-2.5 py-2 text-xs text-[var(--muted)] transition hover:border-rose-500/40 hover:text-rose-300"
        >
          <X size={14} /> Clear
        </button>
      )}
    </div>
  );
}

function useDebouncedSync(
  value: string,
  key: string,
  setParam: (u: Record<string, string | undefined>) => void,
) {
  const first = useRef(true);
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    const t = setTimeout(() => setParam({ [key]: value || undefined }), 350);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);
}
