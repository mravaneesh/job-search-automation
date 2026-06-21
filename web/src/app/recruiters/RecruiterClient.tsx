"use client";

import { useRef, useState, useTransition } from "react";
import {
  Link2,
  Mail,
  Plus,
  Trash2,
  X,
  ChevronDown,
} from "lucide-react";
import {
  addRecruiter,
  updateRecruiterStatus,
  deleteRecruiter,
} from "@/lib/actions";
import type { OutreachStatus, RecruiterCompanyRow, RecruiterContact } from "@/lib/types";
import type { RecruiterHint } from "@/lib/recruiter-hints";

// ── status config ────────────────────────────────────────────────────────────

const STATUS_LABELS: Record<OutreachStatus, string> = {
  not_contacted: "Not contacted",
  contacted: "Contacted",
  replied: "Replied",
  not_relevant: "Not relevant",
};

const STATUS_STYLE: Record<OutreachStatus, string> = {
  not_contacted: "border-slate-600/40 bg-slate-700/20 text-slate-400",
  contacted: "border-amber-500/30 bg-amber-500/10 text-amber-300",
  replied: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  not_relevant: "border-slate-700/30 bg-slate-800/20 text-slate-500",
};

// ── status dropdown ──────────────────────────────────────────────────────────

function StatusDropdown({
  id,
  current,
}: {
  id: number;
  current: OutreachStatus;
}) {
  const [open, setOpen] = useState(false);
  const [, startTransition] = useTransition();
  const [value, setValue] = useState<OutreachStatus>(current);

  function pick(s: OutreachStatus) {
    setValue(s);
    setOpen(false);
    startTransition(() => updateRecruiterStatus(id, s));
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((p) => !p)}
        className={`chip flex items-center gap-1 ${STATUS_STYLE[value]}`}
      >
        {STATUS_LABELS[value]}
        <ChevronDown size={11} />
      </button>
      {open && (
        <div className="absolute left-0 top-full z-20 mt-1 min-w-[160px] rounded-xl border border-[var(--border)] bg-[var(--panel)] py-1 shadow-xl">
          {(Object.keys(STATUS_LABELS) as OutreachStatus[]).map((s) => (
            <button
              key={s}
              onClick={() => pick(s)}
              className={`block w-full px-3 py-2 text-left text-xs transition hover:bg-white/5 ${
                s === value ? "text-indigo-200" : "text-[var(--text)]"
              }`}
            >
              {STATUS_LABELS[s]}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── add recruiter modal ──────────────────────────────────────────────────────

function AddModal({
  company,
  hint,
  onClose,
}: {
  company: string;
  hint: RecruiterHint | null;
  onClose: () => void;
}) {
  const ref = useRef<HTMLFormElement>(null);
  const [pending, startTransition] = useTransition();

  function submit(fd: FormData) {
    startTransition(async () => {
      await addRecruiter(fd);
      onClose();
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold">Add recruiter — {company}</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-[var(--muted)] hover:bg-white/5 hover:text-[var(--text)]"
          >
            <X size={16} />
          </button>
        </div>

        {hint && (
          <div className="mb-4 rounded-xl border border-indigo-500/20 bg-indigo-500/5 px-3 py-2 text-xs text-indigo-300">
            Email pattern: <span className="font-mono">{hint.pattern}</span>
          </div>
        )}

        <form ref={ref} action={submit} className="flex flex-col gap-3">
          <input type="hidden" name="company_name" value={company} />

          <div className="grid grid-cols-2 gap-3">
            <label className="flex flex-col gap-1">
              <span className="text-xs text-[var(--muted)]">Name</span>
              <input
                name="name"
                placeholder="Priya Sharma"
                className="rounded-lg border border-[var(--border)] bg-white/5 px-3 py-2 text-sm placeholder:text-[var(--muted)] focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-[var(--muted)]">Title</span>
              <input
                name="title"
                placeholder="Technical Recruiter"
                className="rounded-lg border border-[var(--border)] bg-white/5 px-3 py-2 text-sm placeholder:text-[var(--muted)] focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </label>
          </div>

          <label className="flex flex-col gap-1">
            <span className="text-xs text-[var(--muted)]">LinkedIn URL</span>
            <input
              name="linkedin_url"
              type="url"
              placeholder="https://linkedin.com/in/priya-sharma"
              className="rounded-lg border border-[var(--border)] bg-white/5 px-3 py-2 text-sm placeholder:text-[var(--muted)] focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs text-[var(--muted)]">Email</span>
            <input
              name="email"
              type="email"
              placeholder={hint ? hint.pattern.replace("first", "priya").replace("last", "sharma") : "recruiter@company.com"}
              className="rounded-lg border border-[var(--border)] bg-white/5 px-3 py-2 text-sm placeholder:text-[var(--muted)] focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs text-[var(--muted)]">Notes</span>
            <textarea
              name="notes"
              rows={2}
              placeholder="Met at event, replied to InMail, etc."
              className="resize-none rounded-lg border border-[var(--border)] bg-white/5 px-3 py-2 text-sm placeholder:text-[var(--muted)] focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </label>

          <div className="mt-1 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg px-4 py-2 text-sm text-[var(--muted)] hover:bg-white/5"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={pending}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              {pending ? "Saving…" : "Add recruiter"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── main client component ────────────────────────────────────────────────────

export function RecruiterClient({
  companies,
  contacts,
  hints,
  linkedInUrls,
}: {
  companies: RecruiterCompanyRow[];
  contacts: RecruiterContact[];
  hints: Record<string, RecruiterHint | null>;
  linkedInUrls: Record<string, string>;
}) {
  const [modal, setModal] = useState<string | null>(null);
  const [, startTransition] = useTransition();
  const [filter, setFilter] = useState<OutreachStatus | "all">("all");

  const filteredContacts =
    filter === "all" ? contacts : contacts.filter((c) => c.outreach_status === filter);

  return (
    <>
      {/* ── Company targets table ─────────────────────────────── */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-left text-xs uppercase tracking-wide text-[var(--muted)]">
                <th className="px-4 py-3 font-medium">Company</th>
                <th className="px-4 py-3 font-medium">Open Jobs</th>
                <th className="px-4 py-3 font-medium">Email Pattern</th>
                <th className="px-4 py-3 font-medium">Contacts</th>
                <th className="px-4 py-3 font-medium">Best Status</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {companies.map((co) => {
                const hint = hints[co.company_name] ?? null;
                const liUrl = linkedInUrls[co.company_name];
                return (
                  <tr
                    key={co.company_name}
                    className="border-b border-[var(--border-soft)] last:border-0 transition hover:bg-white/[0.025]"
                  >
                    <td className="px-4 py-3 font-medium">{co.company_name}</td>
                    <td className="px-4 py-3">
                      {co.open_jobs > 0 ? (
                        <a
                          href={`/jobs?company=${encodeURIComponent(co.company_name)}`}
                          className="tabular-nums text-indigo-300 hover:underline"
                        >
                          {co.open_jobs}
                        </a>
                      ) : (
                        <span className="text-[var(--muted)]">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {hint ? (
                        <span className="font-mono text-xs text-slate-300">{hint.pattern}</span>
                      ) : (
                        <span className="text-xs text-[var(--muted)]">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 tabular-nums">
                      {co.recruiter_count > 0 ? (
                        <span className="text-[var(--text)]">{co.recruiter_count}</span>
                      ) : (
                        <span className="text-[var(--muted)]">0</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {co.best_status ? (
                        <span className={`chip ${STATUS_STYLE[co.best_status]}`}>
                          {STATUS_LABELS[co.best_status]}
                        </span>
                      ) : (
                        <span className="text-xs text-[var(--muted)]">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <a
                          href={liUrl}
                          target="_blank"
                          rel="noreferrer"
                          title="Find recruiters on LinkedIn"
                          className="grid h-7 w-7 place-items-center rounded-md text-[var(--muted)] transition hover:bg-sky-500/15 hover:text-sky-300"
                        >
                          <Link2 size={14} />
                        </a>
                        {hint?.domain && (
                          <a
                            href={`https://hunter.io/search/${hint.domain}`}
                            target="_blank"
                            rel="noreferrer"
                            title="Find emails on Hunter.io"
                            className="grid h-7 w-7 place-items-center rounded-md text-[var(--muted)] transition hover:bg-amber-500/15 hover:text-amber-300"
                          >
                            <Mail size={14} />
                          </a>
                        )}
                        <button
                          onClick={() => setModal(co.company_name)}
                          title="Add recruiter contact"
                          className="grid h-7 w-7 place-items-center rounded-md text-[var(--muted)] transition hover:bg-indigo-500/15 hover:text-indigo-300"
                        >
                          <Plus size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Recruiter contacts ────────────────────────────────────── */}
      {contacts.length > 0 && (
        <div className="mt-8">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">Recruiter Contacts</h2>
            <div className="flex gap-1.5">
              {(["all", "not_contacted", "contacted", "replied", "not_relevant"] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => setFilter(s)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                    filter === s
                      ? "bg-indigo-500/20 text-indigo-200 ring-1 ring-indigo-500/30"
                      : "text-[var(--muted)] hover:bg-white/5"
                  }`}
                >
                  {s === "all" ? "All" : STATUS_LABELS[s]}
                </button>
              ))}
            </div>
          </div>

          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)] text-left text-xs uppercase tracking-wide text-[var(--muted)]">
                    <th className="px-4 py-3 font-medium">Name</th>
                    <th className="px-4 py-3 font-medium">Company</th>
                    <th className="px-4 py-3 font-medium">Title</th>
                    <th className="px-4 py-3 font-medium">Contact</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium">Last Contacted</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {filteredContacts.map((r) => (
                    <tr
                      key={r.id}
                      className="border-b border-[var(--border-soft)] last:border-0 transition hover:bg-white/[0.025]"
                    >
                      <td className="px-4 py-3 font-medium">
                        {r.name ?? <span className="text-[var(--muted)]">—</span>}
                      </td>
                      <td className="px-4 py-3 text-[var(--muted)]">{r.company_name}</td>
                      <td className="px-4 py-3 text-[var(--muted)]">
                        {r.title ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {r.linkedin_url && (
                            <a
                              href={r.linkedin_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-sky-400 hover:text-sky-300"
                            >
                              <Link2 size={14} />
                            </a>
                          )}
                          {r.email && (
                            <a
                              href={`mailto:${r.email}`}
                              className="text-xs text-indigo-300 hover:underline"
                            >
                              {r.email}
                            </a>
                          )}
                          {!r.linkedin_url && !r.email && (
                            <span className="text-xs text-[var(--muted)]">—</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <StatusDropdown
                          id={r.id}
                          current={r.outreach_status}
                        />
                      </td>
                      <td className="px-4 py-3 text-xs text-[var(--muted)]">
                        {r.last_contacted_at
                          ? new Date(r.last_contacted_at).toLocaleDateString("en-IN", {
                              day: "numeric",
                              month: "short",
                            })
                          : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() =>
                            startTransition(() => deleteRecruiter(r.id))
                          }
                          className="grid h-7 w-7 place-items-center rounded-md text-[var(--muted)] transition hover:bg-rose-500/15 hover:text-rose-300"
                        >
                          <Trash2 size={13} />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {filteredContacts.length === 0 && (
                    <tr>
                      <td colSpan={7} className="px-4 py-12 text-center text-[var(--muted)]">
                        No contacts with this status.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ── Add modal ───────────────────────────────────────────── */}
      {modal && (
        <AddModal
          company={modal}
          hint={hints[modal] ?? null}
          onClose={() => setModal(null)}
        />
      )}
    </>
  );
}
