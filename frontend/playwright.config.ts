import { defineConfig, devices } from "@playwright/test";

// Run through e2e/run.mjs (it provides the database); see docs/testing.md, Playwright (e2e).
const BACKEND = "127.0.0.1:8001";
const FRONTEND = "http://127.0.0.1:4173";
const vite = "node node_modules/vite/bin/vite.js";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: true,
  reporter: [["list"]],
  use: {
    baseURL: FRONTEND,
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  // The one owner of the app-under-test lifecycle: started for the run, stopped at the end,
  // failures and timeouts included. Never reuse a server someone left running.
  webServer: [
    {
      command: `uv run --frozen python scripts/e2e_server.py ${BACKEND}`,
      cwd: "../backend",
      url: `http://${BACKEND}/api/health/`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        DJANGO_SECRET_KEY: "e2e-only-not-a-secret",
        DJANGO_DEBUG: "false",
        DJANGO_ALLOWED_HOSTS: "127.0.0.1,localhost",
      },
    },
    {
      // A production build behind `vite preview` (not the dev server); /api is proxied to the
      // backend so the page and the API share one origin (spec 0001, AC-20).
      command: `${vite} build --logLevel warn && ${vite} preview --host 127.0.0.1 --port 4173 --strictPort`,
      url: FRONTEND,
      reuseExistingServer: false,
      timeout: 120_000,
      env: { API_TARGET: `http://${BACKEND}` },
    },
  ],
});
