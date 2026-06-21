import { requireProfile } from "@/lib/profile";
import { getRecruiterCompanies, getRecruitersForUser } from "@/lib/queries";
import { getHint, linkedInSearchUrl } from "@/lib/recruiter-hints";
import { PageHeader } from "@/components/ui";
import { RecruiterClient } from "./RecruiterClient";

export const dynamic = "force-dynamic";

export default async function RecruitersPage() {
  const { user, profile } = await requireProfile();

  const [companies, contacts] = await Promise.all([
    getRecruiterCompanies(profile, user.id),
    getRecruitersForUser(user.id),
  ]);

  // Pre-compute hints and LinkedIn URLs on the server so the client bundle
  // doesn't need to import recruiter-hints (server-only data).
  const hints = Object.fromEntries(
    companies.map((c) => [c.company_name, getHint(c.company_name)]),
  );
  const linkedInUrls = Object.fromEntries(
    companies.map((c) => [c.company_name, linkedInSearchUrl(c.company_name)]),
  );

  const contacted = contacts.filter((c) => c.outreach_status !== "not_contacted").length;

  return (
    <>
      <PageHeader
        title="Recruiters"
        subtitle={`${companies.length} target companies · ${contacts.length} contacts · ${contacted} reached`}
      />

      <RecruiterClient
        companies={companies}
        contacts={contacts}
        hints={hints}
        linkedInUrls={linkedInUrls}
      />

      {contacts.length === 0 && (
        <p className="mt-4 text-xs text-[var(--muted)]">
          Click <span className="text-indigo-300">+</span> on any company to add a recruiter contact. Use{" "}
          <span className="text-sky-300">LinkedIn</span> to find recruiters and{" "}
          <span className="text-amber-300">Hunter.io</span> to verify their email.
        </p>
      )}
    </>
  );
}
