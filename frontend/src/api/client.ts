import createClient from "openapi-fetch";

import type { paths } from "./schema";

/** The only way the frontend talks to the server (docs/architecture.md, Forbidden dependencies 6).
 * Same origin: paths are relative, /api is served or proxied next to the SPA. */
export const api = createClient<paths>({ baseUrl: "" });
