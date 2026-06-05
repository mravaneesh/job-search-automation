"use client";

import { useTransition } from "react";
import { Bookmark, Loader2, Trash2 } from "lucide-react";
import {
  removeApplication,
  setApplicationStatus,
  trackJob,
} from "@/lib/actions";
import { APPLICATION_STATUSES, STATUS_LABELS } from "@/lib/format";

export function StatusControl({
  jobId,
  status,
}: {
  jobId: number;
  status: string | null;
}) {
  const [pending, start] = useTransition();

  if (!status) {
    return (
      <button
        onClick={() => start(() => trackJob(jobId))}
        disabled={pending}
        className="flex items-center gap-2 rounded-xl bg-indigo-500 px-4 py-2 text-sm font-medium text-white shadow-lg shadow-indigo-500/20 transition hover:bg-indigo-400 disabled:opacity-60"
      >
        {pending ? <Loader2 size={15} className="animate-spin" /> : <Bookmark size={15} />}
        Track application
      </button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <select
        value={status}
        disabled={pending}
        onChange={(e) =>
          start(() => setApplicationStatus(jobId, e.target.value))
        }
        className="input font-medium"
      >
        {APPLICATION_STATUSES.map((s) => (
          <option key={s} value={s}>
            {STATUS_LABELS[s]}
          </option>
        ))}
      </select>
      <button
        onClick={() => start(() => removeApplication(jobId))}
        disabled={pending}
        title="Stop tracking"
        className="grid h-9 w-9 place-items-center rounded-lg border border-[var(--border)] text-[var(--muted)] transition hover:border-rose-500/40 hover:text-rose-300 disabled:opacity-60"
      >
        {pending ? <Loader2 size={15} className="animate-spin" /> : <Trash2 size={15} />}
      </button>
    </div>
  );
}
