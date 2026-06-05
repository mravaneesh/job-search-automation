"use server";

import { mkdir, writeFile } from "fs/promises";
import path from "path";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { signIn, signOut } from "@/auth";
import { query } from "./db";
import { requireUser, upsertProfile } from "./profile";
import { APPLICATION_STATUSES } from "./format";

// ---- auth ----------------------------------------------------------------

export async function signInWithGoogle() {
  await signIn("google", { redirectTo: "/" });
}

export async function doSignOut() {
  await signOut({ redirectTo: "/signin" });
}

// ---- application tracking (per-user) -------------------------------------

export async function trackJob(jobId: number) {
  const user = await requireUser();
  await query(
    `INSERT INTO applications (job_id, user_id, status) VALUES ($1, $2, 'SAVED')
     ON CONFLICT (user_id, job_id) DO NOTHING`,
    [jobId, user.id],
  );
  revalidatePath(`/jobs/${jobId}`);
  revalidatePath("/applications");
}

export async function setApplicationStatus(jobId: number, status: string) {
  if (!APPLICATION_STATUSES.includes(status as (typeof APPLICATION_STATUSES)[number])) {
    throw new Error(`invalid status: ${status}`);
  }
  const user = await requireUser();
  await query(
    `INSERT INTO applications (job_id, user_id, status, last_update)
     VALUES ($1, $2, $3, now())
     ON CONFLICT (user_id, job_id)
     DO UPDATE SET status = EXCLUDED.status, last_update = now()`,
    [jobId, user.id, status],
  );
  revalidatePath("/applications");
  revalidatePath(`/jobs/${jobId}`);
}

export async function removeApplication(jobId: number) {
  const user = await requireUser();
  await query(`DELETE FROM applications WHERE job_id = $1 AND user_id = $2`, [
    jobId,
    user.id,
  ]);
  revalidatePath("/applications");
  revalidatePath(`/jobs/${jobId}`);
}

// ---- onboarding / profile -------------------------------------------------

function splitCsvOrList(formData: FormData, key: string): string[] {
  const all = formData.getAll(key).map(String).filter(Boolean);
  // Skills/locations may arrive as a single comma-separated string too.
  return [
    ...new Set(
      all
        .flatMap((v) => v.split(","))
        .map((s) => s.trim())
        .filter(Boolean),
    ),
  ];
}

export async function saveOnboarding(formData: FormData) {
  const user = await requireUser();

  const targetRoles = formData.getAll("targetRoles").map(String).filter(Boolean);
  const experienceYears = Number(formData.get("experienceYears") ?? 0) || 0;
  const skills = splitCsvOrList(formData, "skills");
  const preferredLocations = splitCsvOrList(formData, "preferredLocations");
  const remoteOnly = formData.get("remoteOnly") === "on";
  const minSalaryRaw = formData.get("minSalary");
  const minSalary = minSalaryRaw ? Number(minSalaryRaw) : null;
  const salaryCurrency = String(formData.get("salaryCurrency") ?? "INR");
  const workAuthorization = (formData.get("workAuthorization") as string) || null;
  const fullName = (formData.get("fullName") as string) || user.name || null;

  // Optional resume upload -> stored under web/uploads (git-ignored).
  let resumeFilename: string | null = null;
  let resumeText: string | null = null;
  const file = formData.get("resume");
  if (file && typeof file === "object" && "arrayBuffer" in file && file.size > 0) {
    const f = file as File;
    const dir = path.join(process.cwd(), "uploads");
    await mkdir(dir, { recursive: true });
    const safe = f.name.replace(/[^a-zA-Z0-9._-]/g, "_");
    resumeFilename = `${user.id}-${safe}`;
    const buf = Buffer.from(await f.arrayBuffer());
    await writeFile(path.join(dir, resumeFilename), buf);
    if (f.type.startsWith("text/")) resumeText = buf.toString("utf8").slice(0, 20000);
  }

  await upsertProfile(user.id, {
    fullName,
    targetRoles,
    experienceYears,
    skills,
    preferredLocations,
    remoteOnly,
    minSalary,
    salaryCurrency,
    workAuthorization,
    resumeFilename,
    resumeText,
    onboarded: true,
  });

  revalidatePath("/");
  redirect("/");
}
