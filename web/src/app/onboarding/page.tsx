import { getProfile, requireUser } from "@/lib/profile";
import { OnboardingForm } from "@/components/OnboardingForm";

export const dynamic = "force-dynamic";

export default async function OnboardingPage() {
  const user = await requireUser();
  const profile = await getProfile(user.id);

  return (
    <div className="mx-auto max-w-2xl py-4">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">
          {profile?.onboarded ? "Edit your profile" : "Set up your profile"}
        </h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          We&apos;ll match jobs from the shared corpus to you — re-rank instantly
          whenever you change this.
        </p>
      </div>
      <OnboardingForm initial={profile} defaultName={user.name} />
    </div>
  );
}
