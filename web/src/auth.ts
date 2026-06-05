import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import PostgresAdapter from "@auth/pg-adapter";
import { pool } from "@/lib/db";
import type { Provider } from "next-auth/providers";

// Google is enabled only when its credentials are present, so local dev works
// without them (use the dev-login route). Add the creds to .env.local to enable.
const providers: Provider[] = [];
if (process.env.AUTH_GOOGLE_ID && process.env.AUTH_GOOGLE_SECRET) {
  providers.push(Google);
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: PostgresAdapter(pool),
  session: { strategy: "database" },
  trustHost: true,
  providers,
  pages: { signIn: "/signin" },
  callbacks: {
    session({ session, user }) {
      if (session.user && user) session.user.id = user.id;
      return session;
    },
  },
});

export const googleEnabled = providers.length > 0;
export const devLoginEnabled = process.env.DEV_LOGIN === "1";
