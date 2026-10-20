import createClient, { type Middleware } from "openapi-fetch";

import type { paths } from "./schema";

const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

function csrfToken(): string | undefined {
  const cookie = document.cookie.split("; ").find((c) => c.startsWith("csrftoken="));
  return cookie ? decodeURIComponent(cookie.slice("csrftoken=".length)) : undefined;
}

/** Django's CSRF protection (docs/security.md): every unsafe request carries the token. */
const csrf: Middleware = {
  onRequest({ request }) {
    const token = csrfToken();
    if (UNSAFE_METHODS.has(request.method) && token) {
      request.headers.set("X-CSRFToken", token);
    }
    return request;
  },
};

/** The only way the frontend talks to the server (docs/architecture.md, Forbidden dependencies 6).
 * Same origin: paths are relative, /api is served or proxied next to the SPA. */
export const api = createClient<paths>({ baseUrl: "" });
api.use(csrf);

/** Machine code of an RFC 9457 problem+json error body (docs/conventions.md). */
export function problemCode(error: unknown): string | undefined {
  if (typeof error === "object" && error !== null && "code" in error) {
    return typeof error.code === "string" ? error.code : undefined;
  }
  return undefined;
}

/** Field errors of a validation problem: { field: [message, ...] }. */
export function problemFieldErrors(error: unknown): Record<string, string[]> {
  if (typeof error === "object" && error !== null && "errors" in error) {
    const errors = error.errors;
    if (typeof errors === "object" && errors !== null) {
      return Object.fromEntries(
        Object.entries(errors).map(([field, messages]) => [
          field,
          Array.isArray(messages) ? messages.map(String) : [String(messages)],
        ]),
      );
    }
  }
  return {};
}
