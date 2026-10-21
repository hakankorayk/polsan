import { render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "./api/client";
import { BalanceSection } from "./BalanceSection";

vi.mock("./api/client", async (original) => ({
  ...(await original<typeof import("./api/client")>()),
  api: { GET: vi.fn() },
}));

const get = vi.mocked(api.GET);
const ok = (data: unknown) => Promise.resolve({ data, response: new Response(null) }) as never;

const summary = {
  balance: "88.5",
  next_accrual: { date: "2027-03-10", days: "20.0" },
  entries: [
    { id: "a", date: "2026-10-21", kind: "ADJUSTMENT", amount: "-1.5", reason: "Eski kullanım" },
    { id: "b", date: "2026-03-10", kind: "ACCRUAL", amount: "20.0", reason: null },
  ],
};

afterEach(() => get.mockReset());

describe("BalanceSection (spec 0003)", () => {
  it("shows the balance and the next accrual (AC-22)", async () => {
    get.mockReturnValue(ok(summary));

    render(<BalanceSection />);

    const section = await screen.findByRole("region", { name: "İzin bakiyem" });
    expect(await within(section).findByText(/^Bakiye:/)).toHaveTextContent("Bakiye: 88,5 gün");
    expect(within(section).getByText("Sonraki hak ediş: 10.03.2027 — 20 gün")).toBeVisible();
    expect(get).toHaveBeenCalledWith("/api/balance/");
  });

  it("hides the next accrual line when the server sends none (AC-23)", async () => {
    get.mockReturnValue(ok({ ...summary, next_accrual: null }));

    render(<BalanceSection />);

    expect(await screen.findByText(/^Bakiye:/)).toBeVisible();
    expect(screen.queryByText(/Sonraki hak ediş/)).not.toBeInTheDocument();
  });

  it("lists entries in server order with kind, signed amount and reason (AC-24, AC-25)", async () => {
    get.mockReturnValue(ok(summary));

    render(<BalanceSection />);

    const table = await screen.findByRole("table", { name: "Hareketler" });
    expect(
      within(table)
        .getAllByRole("columnheader")
        .map((th) => th.textContent),
    ).toEqual(["Tarih", "Tür", "Miktar", "Gerekçe"]);
    const rows = within(table).getAllByRole("row").slice(1);
    expect(rows.map((row) => row.textContent)).toEqual([
      "21.10.2026Düzeltme−eksi 1,5 günEski kullanım",
      "10.03.2026Hak ediş+20 gün",
    ]);
  });

  it("reads a negative amount with 'eksi' but shows the minus sign (Accessibility)", async () => {
    get.mockReturnValue(ok({ ...summary, balance: "-3.0", entries: [] }));

    render(<BalanceSection />);

    const strong = (await screen.findByText(/^Bakiye:/)).querySelector("strong")!;
    expect(strong.querySelector('[aria-hidden="true"]')).toHaveTextContent("−");
    expect(strong.querySelector(".visually-hidden")).toHaveTextContent("eksi");
    expect(strong).toHaveTextContent("eksi 3 gün");
  });

  it("shows the empty state (AC-26)", async () => {
    get.mockReturnValue(ok({ balance: "0.0", next_accrual: null, entries: [] }));

    render(<BalanceSection />);

    expect(await screen.findByText("Henüz bakiye hareketiniz yok.")).toBeVisible();
    expect(screen.getByText(/^Bakiye:/)).toHaveTextContent("Bakiye: 0 gün");
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("shows loading while the balance loads (AC-27)", () => {
    get.mockReturnValue(new Promise(() => {}) as never);

    render(<BalanceSection />);

    expect(screen.getByRole("status")).toHaveTextContent("Bakiye yükleniyor…");
  });

  it.each([
    [
      "a problem response",
      () =>
        Promise.resolve({
          error: { code: "server_error" },
          response: new Response(null, { status: 500 }),
        }),
    ],
    ["an unreachable server", () => Promise.reject(new TypeError("Failed to fetch"))],
  ])("shows the error message on %s (AC-28)", async (_name, answer) => {
    get.mockImplementation(answer as never);

    render(<BalanceSection />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Bakiye bilgileriniz yüklenemedi. Lütfen sayfayı yenileyin.",
    );
  });
});
