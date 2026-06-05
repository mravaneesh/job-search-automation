import { redirect } from "next/navigation";
import { Radar } from "lucide-react";
import { auth, devLoginEnabled, googleEnabled } from "@/auth";
import { signInWithGoogle } from "@/lib/actions";

export const dynamic = "force-dynamic";

export default async function SignInPage() {
  const session = await auth();
  if (session?.user?.id) redirect("/");

  return (
    <div className="grid min-h-[80vh] place-items-center">
      <div className="card w-full max-w-sm p-8 text-center">
        <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-indigo-500 to-sky-500 shadow-lg shadow-indigo-500/25">
          <Radar size={26} className="text-white" />
        </div>
        <h1 className="text-xl font-semibold">Welcome to JobScope</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Sign in to build your profile and get jobs matched to you.
        </p>

        <div className="mt-6 space-y-3">
          {googleEnabled && (
            <form action={signInWithGoogle}>
              <button
                type="submit"
                className="flex w-full items-center justify-center gap-3 rounded-xl border border-[var(--border)] bg-white px-4 py-2.5 text-sm font-medium text-slate-800 transition hover:bg-slate-100"
              >
                <GoogleIcon /> Continue with Google
              </button>
            </form>
          )}

          {devLoginEnabled && (
            <a
              href="/api/dev-login"
              className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-[var(--border)] px-4 py-2.5 text-sm text-[var(--muted)] transition hover:border-indigo-500/40 hover:text-indigo-200"
            >
              Continue as dev user (local)
            </a>
          )}

          {!googleEnabled && !devLoginEnabled && (
            <p className="text-xs text-amber-300/80">
              No sign-in method configured. Add Google OAuth credentials to
              <code className="mx-1">web/.env.local</code> or set DEV_LOGIN=1.
            </p>
          )}
        </div>

        {googleEnabled || (
          <p className="mt-5 text-[11px] leading-relaxed text-[var(--muted)]/70">
            Tip: add <code>AUTH_GOOGLE_ID</code> / <code>AUTH_GOOGLE_SECRET</code>{" "}
            to enable Google sign-in.
          </p>
        )}
      </div>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.27-4.74 3.27-8.1z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.1a6.6 6.6 0 0 1 0-4.2V7.06H2.18a11 11 0 0 0 0 9.88l3.66-2.84z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84C6.71 7.31 9.14 5.38 12 5.38z"
      />
    </svg>
  );
}
