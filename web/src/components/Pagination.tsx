"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ChevronLeft, ChevronRight } from "lucide-react";

export function Pagination({
  page,
  pageSize,
  total,
}: {
  page: number;
  pageSize: number;
  total: number;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const sp = useSearchParams();
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(total, page * pageSize);

  const go = (p: number) => {
    const params = new URLSearchParams(sp.toString());
    if (p <= 1) params.delete("page");
    else params.set("page", String(p));
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  };

  return (
    <div className="mt-4 flex items-center justify-between text-sm text-[var(--muted)]">
      <span className="tabular-nums">
        {from.toLocaleString()}–{to.toLocaleString()} of {total.toLocaleString()}
      </span>
      <div className="flex items-center gap-2">
        <button
          disabled={page <= 1}
          onClick={() => go(page - 1)}
          className="grid h-8 w-8 place-items-center rounded-lg border border-[var(--border)] transition enabled:hover:border-indigo-500/40 enabled:hover:text-indigo-200 disabled:opacity-30"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="tabular-nums text-[var(--text)]">
          {page} / {pages}
        </span>
        <button
          disabled={page >= pages}
          onClick={() => go(page + 1)}
          className="grid h-8 w-8 place-items-center rounded-lg border border-[var(--border)] transition enabled:hover:border-indigo-500/40 enabled:hover:text-indigo-200 disabled:opacity-30"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
