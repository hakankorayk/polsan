import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

import { NEW_PASSWORD, PASSWORD, TEMPORARY } from "./users";

async function expectNoWcagAaViolations(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
}

async function logIn(page: Page, username: string, password: string) {
  await page.getByLabel("Kullanıcı adı").fill(username);
  await page.getByLabel("Parola", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Giriş yap" }).click();
}

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("form", { name: "Giriş" })).toBeVisible();
});

test("login screen keeps product name and server status; axe on empty form (AC-21, AC-22)", async ({
  page,
}) => {
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Polsan Leave Manager");
  await expect(page.getByText("Sunucu bağlantısı: Bağlı")).toBeVisible();
  await expectNoWcagAaViolations(page);
});

test("login reaches home with name, roles and sorted team (AC-6, AC-15, AC-16, AC-22)", async ({
  page,
}) => {
  await logIn(page, "yonetici", PASSWORD);

  await expect(page.getByRole("heading", { name: "Hoş geldiniz, Zeynep Yönetici" })).toBeVisible();
  await expect(page.getByText("Rolleriniz: Çalışan, Yönetici")).toBeVisible();
  await expect(page.getByRole("region", { name: "Ekibim" }).getByRole("listitem")).toHaveText([
    "Mehmet Çelik",
    "Ece Demir",
  ]);
  await expectNoWcagAaViolations(page);
});

test("non manager home has no team section (AC-16, AC-22)", async ({ page }) => {
  await logIn(page, "calisan", PASSWORD);

  await expect(page.getByRole("heading", { name: "Hoş geldiniz, Ece Demir" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Ekibim" })).toHaveCount(0);
  await expectNoWcagAaViolations(page);
});

test("wrong password shows the generic error (AC-7, AC-22)", async ({ page }) => {
  await logIn(page, "calisan", "yanlis-parola-123");

  await expect(page.getByRole("alert")).toHaveText("Kullanıcı adı veya parola hatalı.");
  await expect(page.getByRole("alert")).toBeFocused();
  await expectNoWcagAaViolations(page);
});

test("lock message after five failures (AC-8, AC-22)", async ({ page }) => {
  for (let attempt = 1; attempt <= 4; attempt++) {
    await logIn(page, "kilit", "yanlis-parola-123");
    await expect(page.getByRole("alert")).toHaveText("Kullanıcı adı veya parola hatalı.");
  }
  await logIn(page, "kilit", "yanlis-parola-123");
  await expect(page.getByRole("alert")).toHaveText(
    "Çok fazla hatalı deneme. Lütfen 15 dakika sonra tekrar deneyin.",
  );

  await logIn(page, "kilit", PASSWORD); // correct password is refused while locked
  await expect(page.getByRole("alert")).toHaveText(/Çok fazla hatalı deneme/);
  await expectNoWcagAaViolations(page);
});

test("forced change before home (AC-10, AC-11, AC-22)", async ({ page }) => {
  await logIn(page, "gecici", TEMPORARY);
  await expect(page.getByRole("heading", { name: "Parolanızı değiştirin" })).toBeVisible();
  await expectNoWcagAaViolations(page);

  await page.getByLabel("Yeni parola", { exact: true }).fill("kisa");
  await page.getByLabel("Yeni parola (tekrar)").fill("kisa");
  await page.getByRole("button", { name: "Parolayı değiştir" }).click();
  const field = page.getByLabel("Yeni parola", { exact: true });
  await expect(field).toHaveAttribute("aria-invalid", "true");
  await expect(field).toBeFocused();
  await expectNoWcagAaViolations(page);

  await field.fill(NEW_PASSWORD);
  await page.getByLabel("Yeni parola (tekrar)").fill(NEW_PASSWORD);
  await page.getByRole("button", { name: "Parolayı değiştir" }).click();
  await expect(page.getByRole("heading", { name: "Hoş geldiniz, Geçici Kullanıcı" })).toBeVisible();
});

test("logout shows message (AC-14, AC-22)", async ({ page }) => {
  await logIn(page, "cikis", PASSWORD);
  await page.getByRole("button", { name: "Çıkış yap" }).click();

  await expect(page.getByText("Çıkış yapıldı.")).toBeVisible();
  await page.reload();
  await expect(page.getByRole("form", { name: "Giriş" })).toBeVisible(); // session really ended
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Hoş geldiniz/ })).toHaveCount(0);
});

test("logged-out notice passes axe (AC-22)", async ({ page }) => {
  await logIn(page, "cikis", PASSWORD);
  await page.getByRole("button", { name: "Çıkış yap" }).click();
  await expect(page.getByText("Çıkış yapıldı.")).toBeVisible();

  await expectNoWcagAaViolations(page);
});

test("expired session redirects with message (AC-13, AC-22)", async ({ page, context }) => {
  await logIn(page, "cikis", PASSWORD);
  await expect(page.getByRole("heading", { name: /Hoş geldiniz/ })).toBeVisible();

  await context.clearCookies({ name: "sessionid" }); // what a 30-minute idle timeout leaves behind
  await page.reload();

  await expect(
    page.getByText("Oturumunuzun süresi doldu. Lütfen yeniden giriş yapın."),
  ).toBeVisible();
  await expectNoWcagAaViolations(page);
});

test("keyboard only flow (AC-23)", async ({ page }) => {
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("Kullanıcı adı")).toBeFocused();
  await page.keyboard.type("klavye");
  await page.keyboard.press("Tab");
  await page.keyboard.type(TEMPORARY);
  await page.keyboard.press("Enter");

  await expect(page.getByRole("heading", { name: "Parolanızı değiştirin" })).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("Yeni parola", { exact: true })).toBeFocused();
  await page.keyboard.type(NEW_PASSWORD);
  await page.keyboard.press("Tab");
  await page.keyboard.type(NEW_PASSWORD);
  await page.keyboard.press("Enter");

  await expect(page.getByRole("heading", { name: "Hoş geldiniz, Klavye Kullanıcı" })).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "Çıkış yap" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByText("Çıkış yapıldı.")).toBeVisible();
});
