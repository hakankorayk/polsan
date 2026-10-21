import { api } from "./api/client";

/** Remembers, for this tab only, that the user was signed in. A later "not authenticated" answer
 * then means the session expired (spec 0002, AC-13) — the server cannot tell the two apart. */
const KEY = "plm.hadSession";

function storage(): Storage | undefined {
  try {
    return window.sessionStorage;
  } catch {
    return undefined; // storage blocked: the expired notice degrades to a plain login screen
  }
}

export function markSession(): void {
  storage()?.setItem(KEY, "1");
}

export function clearSession(): void {
  storage()?.removeItem(KEY);
}

export function hadSession(): boolean {
  return storage()?.getItem(KEY) === "1";
}

/** Makes sure the CSRF cookie exists before the first unsafe request. */
export async function ensureCsrfCookie(): Promise<void> {
  try {
    await api.GET("/api/auth/csrf/");
  } catch {
    // The login attempt will report the unreachable server.
  }
}
