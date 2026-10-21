import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "./api/client";
import { App } from "./App";

vi.mock("./api/client", async (original) => ({
  ...(await original<typeof import("./api/client")>()),
  api: { GET: vi.fn(), POST: vi.fn() },
}));

const get = vi.mocked(api.GET);
const post = vi.mocked(api.POST);

const ok = (data: unknown) => ({ data, response: new Response(null, { status: 200 }) });
const problem = (status: number, code: string) => ({
  error: { code },
  response: new Response(null, { status }),
});

/** Routes GET calls by path; /api/me/ answers come from the queue, in order. */
function server(...meAnswers: unknown[]) {
  get.mockImplementation(((path: string) => {
    if (path === "/api/health/") return Promise.resolve(ok({ status: "ok" }));
    if (path === "/api/auth/csrf/") return Promise.resolve({ response: new Response(null) });
    if (path === "/api/balance/") return Promise.resolve(ok(emptyBalance)); // spec 0003
    return Promise.resolve(meAnswers.length > 1 ? meAnswers.shift() : meAnswers[0]);
  }) as never);
}

const emptyBalance = { balance: "0.0", next_accrual: null, entries: [] };
const profile = { first_name: "Ayşe", last_name: "Yılmaz", roles: ["employee"], team: null };

beforeEach(() => window.sessionStorage.clear());
afterEach(() => {
  get.mockReset();
  post.mockReset();
});

describe("App", () => {
  it("anonymous shows login (AC-18)", async () => {
    server(problem(403, "not_authenticated"));

    render(<App />);

    expect(await screen.findByRole("form", { name: "Giriş" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Polsan Leave Manager");
    expect(screen.queryByText(/Oturumunuzun süresi doldu/)).not.toBeInTheDocument();
  });

  it("routes to password change (AC-10)", async () => {
    server(problem(403, "password_change_required"));

    render(<App />);

    expect(await screen.findByRole("heading", { name: "Parolanızı değiştirin" })).toBeVisible();
  });

  it("shows home after a valid session (AC-15)", async () => {
    server(ok(profile));

    render(<App />);

    expect(
      await screen.findByRole("heading", { level: 1, name: "Hoş geldiniz, Ayşe Yılmaz" }),
    ).toBeVisible();
  });

  it("shows expired message after lost session (AC-13)", async () => {
    window.sessionStorage.setItem("plm.hadSession", "1");
    server(problem(403, "not_authenticated"));

    render(<App />);

    expect(
      await screen.findByText("Oturumunuzun süresi doldu. Lütfen yeniden giriş yapın."),
    ).toBeInTheDocument();
  });

  it("logout shows message (AC-14)", async () => {
    server(ok(profile));
    post.mockResolvedValue({ response: new Response(null, { status: 204 }) } as never);
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Çıkış yap" }));

    expect(await screen.findByText("Çıkış yapıldı.")).toBeInTheDocument();
    expect(post).toHaveBeenCalledWith("/api/auth/logout/");
  });

  it("shows profile error when the profile cannot load after login (AC-15 error state)", async () => {
    server(problem(403, "not_authenticated"), problem(500, "server_error"));
    post.mockResolvedValue(ok({ must_change_password: false }) as never);
    render(<App />);

    fireEvent.change(await screen.findByLabelText("Kullanıcı adı"), {
      target: { value: "ayilmaz" },
    });
    fireEvent.change(screen.getByLabelText("Parola"), { target: { value: "Guclu-Parola-2026!" } });
    fireEvent.click(screen.getByRole("button", { name: "Giriş yap" }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Bilgileriniz yüklenemedi. Lütfen sayfayı yenileyin.",
      ),
    );
  });

  it("shows loading, not the form, while the profile loads after login (L8)", async () => {
    let resolveMe!: (value: unknown) => void;
    let meCalls = 0;
    get.mockImplementation(((path: string) => {
      if (path === "/api/health/") return Promise.resolve(ok({ status: "ok" }));
      if (path === "/api/auth/csrf/") return Promise.resolve({ response: new Response(null) });
      if (path === "/api/balance/") return Promise.resolve(ok(emptyBalance)); // spec 0003
      meCalls += 1;
      if (meCalls === 1) return Promise.resolve(problem(403, "not_authenticated"));
      return new Promise((r) => (resolveMe = r));
    }) as never);
    post.mockResolvedValue(ok({ must_change_password: false }) as never);
    render(<App />);

    fireEvent.change(await screen.findByLabelText("Kullanıcı adı"), {
      target: { value: "ayilmaz" },
    });
    fireEvent.change(screen.getByLabelText("Parola"), { target: { value: "Guclu-Parola-2026!" } });
    fireEvent.click(screen.getByRole("button", { name: "Giriş yap" }));

    expect(await screen.findByText("Yükleniyor…")).toBeInTheDocument();
    expect(screen.queryByRole("form", { name: "Giriş" })).not.toBeInTheDocument();
    resolveMe(ok(profile));
    expect(
      await screen.findByRole("heading", { level: 1, name: "Hoş geldiniz, Ayşe Yılmaz" }),
    ).toBeVisible();
  });
});
