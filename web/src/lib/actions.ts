"use server";

import { revalidatePath } from "next/cache";
import { query } from "./db";
import { APPLICATION_STATUSES } from "./format";

export async function trackJob(jobId: number) {
  await query(
    `INSERT INTO applications (job_id, status) VALUES ($1, 'SAVED')
     ON CONFLICT (job_id) DO NOTHING`,
    [jobId],
  );
  revalidatePath(`/jobs/${jobId}`);
  revalidatePath("/applications");
}

export async function setApplicationStatus(jobId: number, status: string) {
  if (!APPLICATION_STATUSES.includes(status as (typeof APPLICATION_STATUSES)[number])) {
    throw new Error(`invalid status: ${status}`);
  }
  await query(
    `INSERT INTO applications (job_id, status, last_update) VALUES ($1, $2, now())
     ON CONFLICT (job_id) DO UPDATE SET status = EXCLUDED.status, last_update = now()`,
    [jobId, status],
  );
  revalidatePath("/applications");
  revalidatePath(`/jobs/${jobId}`);
}

export async function removeApplication(jobId: number) {
  await query(`DELETE FROM applications WHERE job_id = $1`, [jobId]);
  revalidatePath("/applications");
  revalidatePath(`/jobs/${jobId}`);
}
