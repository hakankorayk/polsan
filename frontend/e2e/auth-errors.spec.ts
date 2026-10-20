import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

import { PASSWORD } from "./users";

// Error states of spec 0002 "User experience" that need a failing server (review L5).

async function expectNoWcagAaViolations(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
}

test("home error state when the profile cannot load (AC-22)", async ({ page }) => {
  await page.route("**/api/me/", (route) =>
    route.fulfill({ status: 500, json: { code: "server_error" } }),
  );

  await page.goto("/");

  await expect(page.getByRole("alert")).toHaveText(
    "Bilgileriniz yüklenemedi. Lütfen sayfayı yenileyin.",
  );
  await expectNoWcagAaViolations(page);
});

test("login attempt while the server is unreachable (AC-22)", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("form", { name: "Giriş" })).toBeVisible();
  await page.route("**/api/auth/login/", (route) => route.abort("connectionrefused"));

  await page.getByLabel("Kullanıcı adı").fill("calisan");
  await page.getByLabel("Parola", { exact: true }).fill(PASSWORD);
  await page.getByRole("button", { name: "Giriş yap" }).click();

  await expect(page.getByRole("alert")).toHaveText(
    "Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin.",
  );
  await expectNoWcagAaViolations(page);
});
