import "server-only";
import { redirect } from "next/navigation";
import { auth } from "@/auth";
import { query, queryOne } from "./db";
import type { Profile } from "./scoring";

export interface SessionUser {
  id: number;
  name: string | null;
  email: string | null;
  image: string | null;
}

interface ProfileRow {
  user_id: number;
  full_name: string | null;
  target_roles: string[];
  experience_years: string;
  skills: string[];
  preferred_locations: string[];
  remote_only: boolean;
  min_salary: string | null;
  salary_currency: string | null;
  work_authorization: string | null;
  resume_filename: string | null;
  onboarded: boolean;
}

function mapProfile(r: ProfileRow): Profile {
  return {
    userId: r.user_id,
    fullName: r.full_name,
    targetRoles: r.target_roles ?? [],
    experienceYears: Number(r.experience_years ?? 0),
    skills: r.skills ?? [],
    preferredLocations: r.preferred_locations ?? [],
    remoteOnly: r.remote_only,
    minSalary: r.min_salary != null ? Number(r.min_salary) : null,
    salaryCurrency: r.salary_currency,
    workAuthorization: r.work_authorization,
    resumeFilename: r.resume_filename,
    onboarded: r.onboarded,
  };
}

export async function requireUser(): Promise<SessionUser> {
  const session = await auth();
  if (!session?.user?.id) redirect("/signin");
  return {
    id: Number(session.user.id),
    name: session.user.name ?? null,
    email: session.user.email ?? null,
    image: session.user.image ?? null,
  };
}

export async function getProfile(userId: number): Promise<Profile | null> {
  const r = await queryOne<ProfileRow>(
    `SELECT * FROM profiles WHERE user_id = $1`,
    [userId],
  );
  return r ? mapProfile(r) : null;
}

/** Require a signed-in, onboarded user; otherwise redirect appropriately. */
export async function requireProfile(): Promise<{
  user: SessionUser;
  profile: Profile;
}> {
  const user = await requireUser();
  const profile = await getProfile(user.id);
  if (!profile || !profile.onboarded) redirect("/onboarding");
  return { user, profile };
}

export interface ProfileInput {
  fullName: string | null;
  targetRoles: string[];
  experienceYears: number;
  skills: string[];
  preferredLocations: string[];
  remoteOnly: boolean;
  minSalary: number | null;
  salaryCurrency: string | null;
  workAuthorization: string | null;
  resumeFilename?: string | null;
  resumeText?: string | null;
  onboarded: boolean;
}

export async function upsertProfile(userId: number, p: ProfileInput): Promise<void> {
  await query(
    `INSERT INTO profiles
       (user_id, full_name, target_roles, experience_years, skills,
        preferred_locations, remote_only, min_salary, salary_currency,
        work_authorization, resume_filename, resume_text, onboarded, updated_at)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,
             COALESCE($11, (SELECT resume_filename FROM profiles WHERE user_id=$1)),
             COALESCE($12, (SELECT resume_text FROM profiles WHERE user_id=$1)),
             $13, now())
     ON CONFLICT (user_id) DO UPDATE SET
       full_name = EXCLUDED.full_name,
       target_roles = EXCLUDED.target_roles,
       experience_years = EXCLUDED.experience_years,
       skills = EXCLUDED.skills,
       preferred_locations = EXCLUDED.preferred_locations,
       remote_only = EXCLUDED.remote_only,
       min_salary = EXCLUDED.min_salary,
       salary_currency = EXCLUDED.salary_currency,
       work_authorization = EXCLUDED.work_authorization,
       resume_filename = COALESCE(EXCLUDED.resume_filename, profiles.resume_filename),
       resume_text = COALESCE(EXCLUDED.resume_text, profiles.resume_text),
       onboarded = EXCLUDED.onboarded,
       updated_at = now()`,
    [
      userId,
      p.fullName,
      p.targetRoles,
      p.experienceYears,
      p.skills,
      p.preferredLocations,
      p.remoteOnly,
      p.minSalary,
      p.salaryCurrency,
      p.workAuthorization,
      p.resumeFilename ?? null,
      p.resumeText ?? null,
      p.onboarded,
    ],
  );
}
