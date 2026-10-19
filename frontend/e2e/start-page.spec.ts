import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const HEALTH = "**/api/health/";
const CHECKING = "Sunucu bağlantısı kontrol ediliyor…";
const CONNECTED = "Sunucu bağlantısı: Bağlı";
const UNREACHABLE = "Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin.";

async function expectNoWcagAaViolations(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
}

test("shows title and lang tr (AC-1)", async ({ page }) => {
  await page.goto("/");

  await expect(page.locator("html")).toHaveAttribute("lang", "tr");
  await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Polsan Leave Manager");
});

test("shows connected against real backend and database (AC-2)", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("status")).toHaveText(CONNECTED);
});

test("shows unreachable on 503 without technical detail (AC-4)", async ({ page }) => {
  await page.route(HEALTH, (route) =>
    route.fulfill({ status: 503, json: { status: "unavailable" } }),
  );

  await page.goto("/");

  await expect(page.getByRole("status")).toHaveText(UNREACHABLE);
});

test("health request goes to the page origin (AC-20)", async ({ page }) => {
  const healthRequest = page.waitForRequest((request) => request.url().endsWith("/api/health/"));

  await page.goto("/");
  const request = await healthRequest;

  expect(new URL(request.url()).origin).toBe(new URL(page.url()).origin);
  expect((await request.response())?.status()).toBe(200);
});

test.describe("axe finds no WCAG 2.1 AA violations (AC-19)", () => {
  test("while checking", async ({ page }) => {
    await page.route(HEALTH, () => {}); // never answers: the page stays in the checking state

    await page.goto("/");

    await expect(page.getByRole("status")).toHaveText(CHECKING);
    await expectNoWcagAaViolations(page);
  });

  test("when connected", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("status")).toHaveText(CONNECTED);
    await expectNoWcagAaViolations(page);
  });

  test("when unreachable", async ({ page }) => {
    await page.route(HEALTH, (route) => route.abort("connectionrefused"));

    await page.goto("/");

    await expect(page.getByRole("status")).toHaveText(UNREACHABLE);
    await expectNoWcagAaViolations(page);
  });
});
