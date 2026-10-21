import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

import { PASSWORD, TEMPORARY } from "./users";

// Pending-request states of spec 0002 "User experience" (AC-22, QA verify finding 2): each request
// is held open with page.route so the in-between state can be scanned, then released.

async function expectNoWcagAaViolations(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
}

/** Holds every request matching `url` until the returned function is called. */
async function hold(page: Page, url: string): Promise<() => void> {
  let release!: () => void;
  const released = new Promise<void>((resolve) => (release = resolve));
  await page.route(url, async (route) => {
    await released;
    await route.continue();
  });
  return release;
}

test("loading screen while the profile loads (AC-22)", async ({ page }) => {
  const release = await hold(page, "**/api/me/");
  await page.goto("/");

  await expect(page.getByText("Yükleniyor…")).toBeVisible();
  await expectNoWcagAaViolations(page);
  release();
  await expect(page.getByRole("form", { name: "Giriş" })).toBeVisible();
});

test("loading screen after login while the profile loads (AC-22)", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("form", { name: "Giriş" })).toBeVisible();
  const release = await hold(page, "**/api/me/");

  await page.getByLabel("Kullanıcı adı").fill("calisan");
  await page.getByLabel("Parola", { exact: true }).fill(PASSWORD);
  await page.getByRole("button", { name: "Giriş yap" }).click();

  await expect(page.getByText("Yükleniyor…")).toBeVisible();
  await expectNoWcagAaViolations(page);
  release();
  await expect(page.getByRole("heading", { name: "Hoş geldiniz, Ece Demir" })).toBeVisible();
});

test("submitting login and password forms, then the mismatch error (AC-11, AC-22)", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("form", { name: "Giriş" })).toBeVisible();

  const releaseLogin = await hold(page, "**/api/auth/login/");
  await page.getByLabel("Kullanıcı adı").fill("bekleyen");
  await page.getByLabel("Parola", { exact: true }).fill(TEMPORARY);
  await page.getByRole("button", { name: "Giriş yap" }).click();
  await expect(page.getByRole("button", { name: "Giriş yapılıyor…" })).toBeDisabled();
  await expectNoWcagAaViolations(page);
  releaseLogin();
  await expect(page.getByRole("heading", { name: "Parolanızı değiştirin" })).toBeVisible();

  const releaseChange = await hold(page, "**/api/auth/password/");
  await page.getByLabel("Yeni parola", { exact: true }).fill("Yepyeni-Parola-2027?");
  await page.getByLabel("Yeni parola (tekrar)").fill("Baska-Parola-2028!");
  await page.getByRole("button", { name: "Parolayı değiştir" }).click();
  await expect(page.getByRole("button", { name: "Kaydediliyor…" })).toBeDisabled();
  await expectNoWcagAaViolations(page);
  releaseChange();

  const confirm = page.getByLabel("Yeni parola (tekrar)");
  await expect(confirm).toHaveAttribute("aria-invalid", "true");
  await expect(confirm).toHaveAccessibleDescription("Parolalar eşleşmiyor.");
  await expect(confirm).toBeFocused();
  await expectNoWcagAaViolations(page);
});
