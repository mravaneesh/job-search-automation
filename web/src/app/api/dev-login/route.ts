import { randomBytes } from "crypto";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { query, queryOne } from "@/lib/db";

// Local-only shortcut: signs in a fixed dev user by creating a real DB session
// row + cookie (the same path Auth.js uses), so the app can be exercised end to
// end without Google credentials. Guarded by DEV_LOGIN=1.
export async function GET(req: Request) {
  if (process.env.DEV_LOGIN !== "1") {
    return NextResponse.json({ error: "dev login disabled" }, { status: 403 });
  }

  let user = await queryOne<{ id: number }>(
    `SELECT id FROM users WHERE email = $1`,
    ["dev@local"],
  );
  if (!user) {
    user = await queryOne<{ id: number }>(
      `INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id`,
      ["Dev User", "dev@local"],
    );
  }

  const token = randomBytes(32).toString("hex");
  const expires = new Date(Date.now() + 30 * 86_400_000);
  await query(
    `INSERT INTO sessions ("userId", expires, "sessionToken") VALUES ($1, $2, $3)`,
    [user!.id, expires, token],
  );

  const store = await cookies();
  store.set("authjs.session-token", token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    expires,
  });

  return NextResponse.redirect(new URL("/", req.url));
}
