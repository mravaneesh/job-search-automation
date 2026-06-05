"use client";

import { useState } from "react";
import { Check, Plus, X, Loader2 } from "lucide-react";
import { saveOnboarding } from "@/lib/actions";
import type { Profile } from "@/lib/scoring";

const ROLES = [
  { v: "android", label: "Android" },
  { v: "ios", label: "iOS" },
  { v: "frontend", label: "Frontend" },
  { v: "fullstack", label: "Full Stack" },
  { v: "backend", label: "Backend" },
  { v: "devops", label: "DevOps" },
  { v: "data_engineering", label: "Data Eng" },
  { v: "ai_ml", label: "AI/ML" },
];
const SKILL_SUGGEST = [
  "Kotlin", "Java", "Android SDK", "Jetpack Compose", "Swift", "SwiftUI",
  "React", "TypeScript", "Next.js", "Node.js", "Angular", "Vue",
  "Spring", "PostgreSQL", "MySQL", "REST", "gRPC", "Microservices",
  "Docker", "Kubernetes", "AWS", "Terraform", "CI/CD",
  "Python", "PyTorch", "LLM", "NLP", "RAG", "Spark", "Airflow",
];
const LOCATION_SUGGEST = [
  "Bengaluru", "Hyderabad", "Pune", "Mumbai", "Delhi", "Gurgaon",
  "Chennai", "Remote",
];
const WORK_AUTH = ["India citizen", "Need visa sponsorship", "Other"];

export function OnboardingForm({
  initial,
  defaultName,
  submitLabel = "Finish & see my jobs",
}: {
  initial?: Profile | null;
  defaultName?: string | null;
  submitLabel?: string;
}) {
  const [roles, setRoles] = useState<string[]>(initial?.targetRoles ?? ["android"]);
  const [skills, setSkills] = useState<string[]>(initial?.skills ?? []);
  const [locations, setLocations] = useState<string[]>(
    initial?.preferredLocations ?? ["Bengaluru", "Remote"],
  );
  const [submitting, setSubmitting] = useState(false);

  const toggleRole = (v: string) =>
    setRoles((r) => (r.includes(v) ? r.filter((x) => x !== v) : [...r, v]));

  return (
    <form
      action={saveOnboarding}
      onSubmit={() => setSubmitting(true)}
      className="space-y-5"
    >
      {/* hidden fields carrying multi-value selections */}
      {roles.map((r) => (
        <input key={r} type="hidden" name="targetRoles" value={r} />
      ))}
      {skills.map((s) => (
        <input key={s} type="hidden" name="skills" value={s} />
      ))}
      {locations.map((l) => (
        <input key={l} type="hidden" name="preferredLocations" value={l} />
      ))}

      <Section title="Your name">
        <input
          name="fullName"
          defaultValue={initial?.fullName ?? defaultName ?? ""}
          placeholder="Full name"
          className="input w-full"
        />
      </Section>

      <Section
        title="Target roles"
        hint="Pick what you're looking for. Order = priority (first is primary)."
      >
        <div className="flex flex-wrap gap-2">
          {ROLES.map((r) => {
            const active = roles.includes(r.v);
            const rank = roles.indexOf(r.v);
            return (
              <button
                key={r.v}
                type="button"
                onClick={() => toggleRole(r.v)}
                className={`flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium transition ${
                  active
                    ? "border-indigo-500/40 bg-indigo-500/15 text-indigo-200"
                    : "border-[var(--border)] text-[var(--muted)] hover:text-[var(--text)]"
                }`}
              >
                {active && (
                  <span className="grid h-5 w-5 place-items-center rounded-full bg-indigo-500 text-[11px] font-bold text-white">
                    {rank + 1}
                  </span>
                )}
                {r.label}
              </button>
            );
          })}
        </div>
      </Section>

      <Section title="Experience" hint="Years of professional experience.">
        <input
          name="experienceYears"
          type="number"
          min={0}
          max={40}
          step={0.5}
          defaultValue={initial?.experienceYears ?? 2}
          className="input w-32"
        />
      </Section>

      <Section title="Skills" hint="What you know — drives match scoring.">
        <ChipInput
          values={skills}
          setValues={setSkills}
          placeholder="Add a skill and press Enter"
          suggestions={SKILL_SUGGEST}
        />
      </Section>

      <Section title="Preferred locations">
        <ChipInput
          values={locations}
          setValues={setLocations}
          placeholder="Add a location"
          suggestions={LOCATION_SUGGEST}
        />
        <label className="mt-3 flex w-fit items-center gap-2 text-sm text-[var(--muted)]">
          <input
            type="checkbox"
            name="remoteOnly"
            defaultChecked={initial?.remoteOnly ?? false}
            className="h-4 w-4 accent-indigo-500"
          />
          Remote only
        </label>
      </Section>

      <Section title="Salary expectation" hint="Optional — filters out lower offers.">
        <div className="flex gap-2">
          <select
            name="salaryCurrency"
            defaultValue={initial?.salaryCurrency ?? "INR"}
            className="input"
          >
            <option value="INR">INR</option>
            <option value="USD">USD</option>
          </select>
          <input
            name="minSalary"
            type="number"
            min={0}
            step={50000}
            defaultValue={initial?.minSalary ?? ""}
            placeholder="Minimum (annual)"
            className="input w-48"
          />
        </div>
      </Section>

      <Section title="Work authorization">
        <select
          name="workAuthorization"
          defaultValue={initial?.workAuthorization ?? "India citizen"}
          className="input w-full sm:w-72"
        >
          {WORK_AUTH.map((w) => (
            <option key={w} value={w}>
              {w}
            </option>
          ))}
        </select>
      </Section>

      <Section title="Resume" hint="Optional — stored for tailoring later.">
        <input
          name="resume"
          type="file"
          accept=".pdf,.doc,.docx,.txt"
          className="block w-full text-sm text-[var(--muted)] file:mr-3 file:rounded-lg file:border-0 file:bg-indigo-500/15 file:px-3 file:py-2 file:text-sm file:font-medium file:text-indigo-200 hover:file:bg-indigo-500/25"
        />
        {initial?.resumeFilename && (
          <p className="mt-1 text-xs text-[var(--muted)]">
            Current: {initial.resumeFilename}
          </p>
        )}
      </Section>

      <button
        type="submit"
        disabled={submitting || roles.length === 0}
        className="flex items-center gap-2 rounded-xl bg-indigo-500 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition hover:bg-indigo-400 disabled:opacity-60"
      >
        {submitting ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
        {submitLabel}
      </button>
    </form>
  );
}

function Section({
  title,
  hint,
  children,
}: {
  title: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card p-5">
      <div className="mb-3">
        <h2 className="text-sm font-semibold">{title}</h2>
        {hint && <p className="text-xs text-[var(--muted)]">{hint}</p>}
      </div>
      {children}
    </div>
  );
}

function ChipInput({
  values,
  setValues,
  placeholder,
  suggestions,
}: {
  values: string[];
  setValues: (v: string[]) => void;
  placeholder: string;
  suggestions: string[];
}) {
  const [draft, setDraft] = useState("");
  const add = (v: string) => {
    const t = v.trim();
    if (t && !values.some((x) => x.toLowerCase() === t.toLowerCase()))
      setValues([...values, t]);
    setDraft("");
  };
  const remaining = suggestions.filter(
    (s) => !values.some((v) => v.toLowerCase() === s.toLowerCase()),
  );

  return (
    <div>
      <div className="flex flex-wrap gap-1.5">
        {values.map((v) => (
          <span
            key={v}
            className="chip border-indigo-500/30 bg-indigo-500/15 text-indigo-200"
          >
            {v}
            <button
              type="button"
              onClick={() => setValues(values.filter((x) => x !== v))}
              className="text-indigo-300/70 hover:text-rose-300"
            >
              <X size={12} />
            </button>
          </span>
        ))}
      </div>
      <input
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            add(draft);
          }
        }}
        placeholder={placeholder}
        className="input mt-2 w-full"
      />
      {remaining.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {remaining.slice(0, 12).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => add(s)}
              className="chip border-[var(--border)] text-[var(--muted)] transition hover:border-indigo-500/40 hover:text-indigo-200"
            >
              <Plus size={11} /> {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
