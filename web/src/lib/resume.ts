import "server-only";
import { readFile } from "fs/promises";
import path from "path";
import { roleLabel } from "./format";
import type { Profile } from "./scoring";
import type { ScoredJob } from "./queries";
import type { SessionUser } from "./profile";

export interface ResumeData {
  name: string;
  email: string | null;
  location: string | null;
  roleLabel: string;
  company: string;
  jobTitle: string;
  matchScore: number | null;
  summary: string;
  relevantSkills: string[]; // your skills the job asks for (lead with these)
  otherSkills: string[]; // your remaining skills
  matchedSkills: string[];
  missingSkills: string[];
  experienceParagraphs: string[];
  generatedOn: string;
}

/** Read an uploaded résumé file and extract its plain text (PDF / DOCX / TXT). */
export async function extractResumeText(filename: string): Promise<string | null> {
  try {
    const filePath = path.join(process.cwd(), "uploads", filename);
    const buf = await readFile(filePath);
    const ext = filename.toLowerCase().split(".").pop();

    if (ext === "pdf") {
      const { extractText, getDocumentProxy } = await import("unpdf");
      const pdf = await getDocumentProxy(new Uint8Array(buf));
      const { text } = await extractText(pdf, { mergePages: true });
      return text;
    }
    if (ext === "docx" || ext === "doc") {
      const mammoth = await import("mammoth");
      const { value } = await mammoth.extractRawText({ buffer: buf });
      return value;
    }
    return buf.toString("utf8");
  } catch {
    return null;
  }
}

function lower(arr: string[]): Set<string> {
  return new Set(arr.map((s) => s.toLowerCase()));
}

export function buildResumeData(
  job: ScoredJob,
  profile: Profile,
  user: SessionUser,
  resumeText: string | null,
): ResumeData {
  const jobSkills = lower(job.skills ?? []);
  const relevantSkills = profile.skills.filter((s) => jobSkills.has(s.toLowerCase()));
  const relevantSet = lower(relevantSkills);
  const otherSkills = profile.skills.filter((s) => !relevantSet.has(s.toLowerCase()));

  const top = relevantSkills.slice(0, 4);
  const yrs = profile.experienceYears;
  const yearsLabel = yrs > 0 ? `${yrs % 1 === 0 ? yrs : yrs.toFixed(1)}+ years` : "Early-career";
  const role = roleLabel(job.role_category);
  const summary =
    `${yearsLabel} ${role} engineer targeting the ${job.title} role at ${job.company_name}. ` +
    (top.length
      ? `Hands-on with ${top.join(", ")}${relevantSkills.length > top.length ? ", and more" : ""}, directly matching this role's requirements.`
      : `Aligned to this role's focus areas.`);

  const experienceParagraphs = (resumeText ?? "")
    .replace(/\r/g, "")
    .split(/\n{2,}/)
    .map((p) => p.replace(/\s+\n/g, "\n").trim())
    .filter((p) => p.length > 1)
    .slice(0, 40);

  return {
    name: profile.fullName || user.name || "Your Name",
    email: user.email,
    location: profile.preferredLocations[0] ?? null,
    roleLabel: role,
    company: job.company_name,
    jobTitle: job.title,
    matchScore: job.match_score,
    summary,
    relevantSkills,
    otherSkills,
    matchedSkills: job.matched_skills ?? [],
    missingSkills: job.missing_skills ?? [],
    experienceParagraphs,
    generatedOn: new Date().toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
    }),
  };
}
