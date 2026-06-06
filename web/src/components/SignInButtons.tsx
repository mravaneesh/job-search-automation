"use client";

import { useFormStatus } from "react-dom";
import { Loader2 } from "lucide-react";
import { signInWithGoogle } from "@/lib/actions";

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden>
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

function GoogleSubmit() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="group relative flex w-full items-center justify-center gap-3 overflow-hidden rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-800 shadow-md transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-indigo-500/20 active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-80"
    >
      {pending ? (
        <>
          <Loader2 size={18} className="animate-spin text-indigo-600" />
          Connecting to Google…
        </>
      ) : (
        <>
          <GoogleIcon />
          Continue with Google
        </>
      )}
      {pending && (
        <span className="absolute bottom-0 left-0 h-0.5 w-full overflow-hidden bg-indigo-100">
          <span className="block h-full w-1/3 animate-[sheen_1.2s_ease-in-out_infinite] bg-indigo-500" />
        </span>
      )}
    </button>
  );
}

export function SignInButtons({
  googleEnabled,
  devLoginEnabled,
}: {
  googleEnabled: boolean;
  devLoginEnabled: boolean;
}) {
  return (
    <div className="space-y-3">
      {googleEnabled && (
        <form action={signInWithGoogle}>
          <GoogleSubmit />
        </form>
      )}

      {devLoginEnabled && (
        <a
          href="/api/dev-login"
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-[var(--border)] px-4 py-2.5 text-sm text-[var(--muted)] transition-colors hover:border-indigo-500/50 hover:text-indigo-200"
        >
          Continue as dev user (local)
        </a>
      )}

      {!googleEnabled && !devLoginEnabled && (
        <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
          No sign-in method configured. Add <code>AUTH_GOOGLE_ID</code> and{" "}
          <code>AUTH_GOOGLE_SECRET</code> to <code>web/.env.local</code> (or set{" "}
          <code>DEV_LOGIN=1</code>), then restart.
        </p>
      )}
    </div>
  );
}
