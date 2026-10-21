import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

import { BALANCE_USER, EMPTY_BALANCE_USER, PASSWORD } from "./users";

// Spec 0003 "İzin bakiyem" section: success, empty, loading and error states (AC-22 … AC-28,
// AC-31). Seed data: backend/scripts/e2e_server.py, relative to the real today.

async function expectNoWcagAaViolations(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
}

async function logIn(page: Page, username: string) {
  await page.goto("/");
  await expect(page.getByRole("form", { name: "Giriş" })).toBeVisible();
  await page.getByLabel("Kullanıcı adı").fill(username);
  await page.getByLabel("Parola", { exact: true }).fill(PASSWORD);
  await page.getByRole("button", { name: "Giriş yap" }).click();
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

const balance = (page: Page) => page.getByRole("region", { name: "İzin bakiyem" });

test("balance, next accrual and movements newest first (AC-22, AC-24, AC-25, AC-31)", async ({
  page,
}) => {
  await logIn(page, BALANCE_USER);

  const section = balance(page);
  // 3 x 14 accrued, −2 and +0,5 adjusted by HR.
  await expect(section.getByText(/^Bakiye:/)).toHaveText("Bakiye: 40,5 gün");
  await expect(section.getByText(/^Sonraki hak ediş:/)).toHaveText(
    /^Sonraki hak ediş: \d{2}\.\d{2}\.\d{4} — 14 gün$/,
  );
  const table = section.getByRole("table", { name: "Hareketler" });
  await expect(table.getByRole("columnheader")).toHaveText(["Tarih", "Tür", "Miktar", "Gerekçe"]);
  const rows = table.getByRole("row").filter({ has: page.getByRole("cell") });
  await expect(rows).toHaveCount(5);
  await expect(rows.nth(0)).toContainText("Düzeltme");
  await expect(rows.nth(0)).toContainText("+0,5 gün");
  await expect(rows.nth(0)).toContainText("Açılış bakiyesi");
  await expect(rows.nth(1)).toContainText("2 gün");
  await expect(rows.nth(1).getByText("eksi", { exact: false })).toBeAttached();
  await expect(rows.nth(1)).toContainText("Eski sistemde kullanılan izin");
  for (const index of [2, 3, 4]) {
    await expect(rows.nth(index)).toContainText("Hak ediş");
    await expect(rows.nth(index)).toContainText("+14 gün");
  }
  await expectNoWcagAaViolations(page);
});

test("the balance section never traps the keyboard (AC-31)", async ({ page }) => {
  await logIn(page, BALANCE_USER);
  await expect(balance(page).getByRole("table", { name: "Hareketler" })).toBeVisible();

  await page.keyboard.press("Tab");

  await expect(page.getByRole("button", { name: "Çıkış yap" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByText("Çıkış yapıldı.")).toBeVisible();
});

test("no movements yet: 0 days and the empty message (AC-26, AC-31)", async ({ page }) => {
  await logIn(page, EMPTY_BALANCE_USER);

  const section = balance(page);
  await expect(section.getByText("Henüz bakiye hareketiniz yok.")).toBeVisible();
  await expect(section.getByText(/^Bakiye:/)).toHaveText("Bakiye: 0 gün");
  await expect(section.getByRole("table")).toHaveCount(0);
  await expectNoWcagAaViolations(page);
});

test("loading message while the balance loads (AC-27, AC-31)", async ({ page }) => {
  const release = await hold(page, "**/api/balance/");
  await logIn(page, BALANCE_USER);

  await expect(balance(page).getByRole("status")).toHaveText("Bakiye yükleniyor…");
  await expectNoWcagAaViolations(page);
  release();
  await expect(balance(page).getByText(/^Bakiye:/)).toHaveText("Bakiye: 40,5 gün");
});

test("error message when the balance fails; the rest of the page stays (AC-28, AC-31)", async ({
  page,
}) => {
  await page.route("**/api/balance/", (route) =>
    route.fulfill({
      status: 500,
      contentType: "application/problem+json",
      body: JSON.stringify({ code: "server_error", detail: "Beklenmeyen bir hata oluştu." }),
    }),
  );
  await logIn(page, BALANCE_USER);

  await expect(balance(page).getByRole("alert")).toHaveText(
    "Bakiye bilgileriniz yüklenemedi. Lütfen sayfayı yenileyin.",
  );
  await expect(page.getByRole("heading", { name: "Hoş geldiniz, Bakiye Sahibi" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Çıkış yap" })).toBeVisible();
  await expectNoWcagAaViolations(page);
});
