// Deterministic, per-profile scoring — a TypeScript port of the Python engine
// (src/jobsearch/scoring/engine.py). Runs at read-time against the signed-in
// user's profile, so editing the profile instantly re-ranks the shared corpus.

import type { Priority } from "./types";

export interface Profile {
  userId: number;
  fullName: string | null;
  targetRoles: string[]; // ordered: [primary, secondary, stretch]
  experienceYears: number;
  skills: string[];
  preferredLocations: string[];
  remoteOnly: boolean;
  minSalary: number | null;
  salaryCurrency: string | null;
  workAuthorization: string | null;
  resumeFilename: string | null;
  onboarded: boolean;
}

export interface JobRow {
  id: number;
  title: string;
  company_name: string;
  role_category: string;
  location: string | null;
  source: string;
  url: string;
  experience: string | null;
  employment_type: string | null;
  discovered_date: string;
  created_date: string | null;
  skills: string[];
  description: string | null;
  salary_min: number | null;
  salary_max: number | null;
  currency: string | null;
  category: string | null; // company category
  tier: string | null;
}

export interface Scored {
  match_score: number;
  priority: Priority;
  skill_score: number;
  experience_score: number;
  location_score: number;
  seniority_score: number;
  company_score: number;
  interview_likelihood: number;
  matched_skills: string[];
  missing_skills: string[];
}

const WEIGHTS = {
  skill: 0.3,
  experience: 0.15,
  location: 0.1,
  seniority: 0.1,
  company: 0.1,
  interview: 0.25,
};
const THRESH = { high: 75, medium: 55 };
const ROLE_FACTORS = [1.0, 0.9, 0.78];
const COMPANY_QUALITY: Record<string, number> = {
  global: 100,
  ai: 95,
  backend: 90,
  india_product: 85,
  unicorn: 80,
};
const DEFAULT_QUALITY = 60;

// title/experience label -> [experience fit, seniority fit]
const SENIORITY_FIT: Record<string, [number, number]> = {
  internship: [70, 60],
  "entry level": [100, 95],
  junior: [100, 95],
  lead: [35, 35],
  senior: [45, 45],
  staff: [25, 25],
  principal: [15, 15],
  manager: [10, 10],
  director: [5, 5],
  executive: [5, 5],
};
const TITLE_SENIORITY: [string, string][] = [
  ["intern", "internship"],
  ["principal", "principal"],
  ["distinguished", "principal"],
  ["staff", "staff"],
  ["architect", "staff"],
  ["director", "director"],
  [" head ", "director"],
  [" vp ", "director"],
  ["vice president", "director"],
  ["chief", "executive"],
  ["manager", "manager"],
  ["senior", "senior"],
  [" sr ", "senior"],
  ["lead", "lead"],
  ["junior", "junior"],
  [" jr ", "junior"],
  ["new grad", "entry level"],
  ["entry level", "entry level"],
];

const clamp = (v: number) => Math.max(0, Math.min(100, Math.round(v)));

export function parseRequiredYears(text: string | null): number | null {
  if (!text) return null;
  const m = text.match(/(\d{1,2})\s*\+?\s*(?:-\s*\d{1,2}\s*)?(?:years?|yrs?)/i);
  return m ? Number(m[1]) : null;
}

function seniorityLabel(title: string): string | null {
  const t = ` ${title.toLowerCase()} `;
  for (const [needle, label] of TITLE_SENIORITY) {
    if (t.includes(needle)) return label;
  }
  return null;
}

export function scoreJob(job: JobRow, profile: Profile): Scored {
  const profileSkills = new Set(profile.skills.map((s) => s.toLowerCase()));

  // skills
  const matched: string[] = [];
  const missing: string[] = [];
  for (const s of job.skills ?? []) {
    (profileSkills.has(s.toLowerCase()) ? matched : missing).push(s);
  }
  const skill = !job.skills?.length
    ? 50
    : clamp((100 * matched.length) / job.skills.length);

  // experience
  let experience = 60;
  const reqYears = parseRequiredYears(job.experience);
  if (reqYears != null) {
    const diff = reqYears - profile.experienceYears;
    experience = diff <= 0 ? 100 : clamp(100 - diff * 20);
  } else {
    const label = seniorityLabel(job.title);
    if (label && SENIORITY_FIT[label]) experience = SENIORITY_FIT[label][0];
  }

  // seniority (title)
  const label = seniorityLabel(job.title);
  const seniority = label && SENIORITY_FIT[label] ? SENIORITY_FIT[label][1] : 90;

  // location
  let location = 60;
  if (job.location) {
    const loc = job.location.toLowerCase();
    if (profile.preferredLocations.some((p) => loc.includes(p.toLowerCase())))
      location = 100;
    else if (loc.includes("remote") || loc.includes("hybrid")) location = 90;
    else location = 40;
  }

  // company
  const company = job.category
    ? (COMPANY_QUALITY[job.category] ?? DEFAULT_QUALITY)
    : DEFAULT_QUALITY;

  const interview = clamp(0.5 * skill + 0.25 * experience + 0.25 * seniority);

  const raw =
    WEIGHTS.skill * skill +
    WEIGHTS.experience * experience +
    WEIGHTS.location * location +
    WEIGHTS.seniority * seniority +
    WEIGHTS.company * company +
    WEIGHTS.interview * interview;

  const roleIdx = profile.targetRoles.indexOf(job.role_category);
  const factor = roleIdx >= 0 ? (ROLE_FACTORS[roleIdx] ?? 0.7) : 0.7;
  const match_score = clamp(raw * factor);
  const priority: Priority =
    match_score >= THRESH.high ? "HIGH" : match_score >= THRESH.medium ? "MEDIUM" : "LOW";

  return {
    match_score,
    priority,
    skill_score: skill,
    experience_score: experience,
    location_score: location,
    seniority_score: seniority,
    company_score: company,
    interview_likelihood: interview,
    matched_skills: [...new Set(matched)].sort(),
    missing_skills: [...new Set(missing)].sort(),
  };
}

// Read-time hard filter: keep only roles that fit the profile.
export function passesProfileFilter(job: JobRow, profile: Profile): boolean {
  if (profile.targetRoles.length && !profile.targetRoles.includes(job.role_category))
    return false;

  if (profile.remoteOnly) {
    const loc = (job.location ?? "").toLowerCase();
    if (!loc.includes("remote") && !loc.includes("anywhere")) return false;
  }

  // Too senior for the candidate's experience.
  const req = parseRequiredYears(job.experience);
  if (req != null && req > profile.experienceYears + 3) return false;
  if (profile.experienceYears < 6) {
    const label = seniorityLabel(job.title);
    if (label && ["staff", "principal", "manager", "director", "executive"].includes(label))
      return false;
  }

  if (profile.minSalary != null && job.salary_max != null && job.salary_max < profile.minSalary)
    return false;

  return true;
}
