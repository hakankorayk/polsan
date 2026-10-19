// E2E runner: owns the database lifecycle; Playwright's webServer owns the app lifecycle.
// Playwright starts webServer BEFORE globalSetup, so a database started in globalSetup would not
// exist yet when the backend boots (plan 0001, risk 3). This runner starts a throwaway
// PostgreSQL 17, runs `playwright test`, and stops the container in `finally` — on failure,
// timeout and Ctrl+C too (docs/testing.md, Resource hygiene).
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

import { PostgreSqlContainer } from "@testcontainers/postgresql";

const playwrightCli = fileURLToPath(import.meta.resolve("@playwright/test/cli"));

const container = await new PostgreSqlContainer("postgres:17-alpine").start();
let child;
const stop = (signal) => child?.kill(signal);
process.on("SIGINT", stop);
process.on("SIGTERM", stop);

let exitCode = 1;
try {
  exitCode = await new Promise((resolve) => {
    child = spawn(
      process.execPath,
      [playwrightCli, "test", "--workers=1", ...process.argv.slice(2)],
      {
        stdio: "inherit",
        env: {
          ...process.env,
          POSTGRES_HOST: container.getHost(),
          POSTGRES_PORT: String(container.getPort()),
          POSTGRES_DB: container.getDatabase(),
          POSTGRES_USER: container.getUsername(),
          POSTGRES_PASSWORD: container.getPassword(),
        },
      },
    );
    child.on("exit", (code) => resolve(code ?? 1));
    child.on("error", () => resolve(1));
  });
} finally {
  await container.stop();
}
process.exit(exitCode);
