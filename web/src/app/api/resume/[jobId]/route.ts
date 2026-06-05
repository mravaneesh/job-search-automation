import { createElement } from "react";
import { auth } from "@/auth";
import { getProfile } from "@/lib/profile";
import { getJobDetail } from "@/lib/queries";
import { buildResumeData, extractResumeText } from "@/lib/resume";
import { ResumeDocument } from "@/components/ResumeDocument";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ jobId: string }> },
) {
  const session = await auth();
  if (!session?.user?.id) {
    return new Response("Unauthorized", { status: 401 });
  }
  const user = {
    id: Number(session.user.id),
    name: session.user.name ?? null,
    email: session.user.email ?? null,
    image: session.user.image ?? null,
  };

  const profile = await getProfile(user.id);
  if (!profile || !profile.onboarded) {
    return new Response("Complete onboarding first", { status: 400 });
  }

  const { jobId } = await params;
  const job = await getJobDetail(profile, user.id, Number(jobId));
  if (!job) return new Response("Job not found", { status: 404 });

  const resumeText = profile.resumeFilename
    ? await extractResumeText(profile.resumeFilename)
    : null;

  const data = buildResumeData(job, profile, user, resumeText);

  const { renderToBuffer } = await import("@react-pdf/renderer");
  const element = createElement(ResumeDocument, { data });
  // renderToBuffer expects a <Document> element, which ResumeDocument returns.
  const buffer = await renderToBuffer(
    element as Parameters<typeof renderToBuffer>[0],
  );

  const safeCompany = job.company_name.replace(/[^a-zA-Z0-9]+/g, "_").slice(0, 40);
  return new Response(new Uint8Array(buffer), {
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": `attachment; filename="resume-${safeCompany}-${jobId}.pdf"`,
      "Cache-Control": "no-store",
    },
  });
}
