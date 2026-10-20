import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "./api/client";
import { LoginForm } from "./LoginForm";

vi.mock("./api/client", async (original) => ({
  ...(await original<typeof import("./api/client")>()),
  api: { GET: vi.fn(), POST: vi.fn() },
}));

const post = vi.mocked(api.POST);

function answer(status: number, body: unknown) {
  post.mockResolvedValue({
    data: status < 400 ? body : undefined,
    error: status >= 400 ? body : undefined,
    response: new Response(null, { status }),
  } as never);
}

async function fillAndSubmit(username = "ayilmaz", password = "yanlis-parola") {
  if (username)
    fireEvent.change(screen.getByLabelText("Kullanıcı adı"), { target: { value: username } });
  if (password) fireEvent.change(screen.getByLabelText("Parola"), { target: { value: password } });
  fireEvent.click(screen.getByRole("button", { name: "Giriş yap" }));
}

afterEach(() => post.mockReset());

describe("LoginForm", () => {
  it("shows generic error and moves focus to it (AC-7, AC-22)", async () => {
    answer(400, { code: "invalid_credentials" });
    render(<LoginForm onSuccess={vi.fn()} />);

    await fillAndSubmit();

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Kullanıcı adı veya parola hatalı.");
    await waitFor(() => expect(alert).toHaveFocus());
  });

  it("shows the lock message (AC-8)", async () => {
    answer(429, { code: "login_locked" });
    render(<LoginForm onSuccess={vi.fn()} />);

    await fillAndSubmit();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Çok fazla hatalı deneme. Lütfen 15 dakika sonra tekrar deneyin.",
    );
  });

  it("shows unreachable server message on network failure", async () => {
    post.mockRejectedValue(new TypeError("Failed to fetch"));
    render(<LoginForm onSuccess={vi.fn()} />);

    await fillAndSubmit();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin.",
    );
  });

  it("errors linked and focus moves to first error (AC-22)", async () => {
    render(<LoginForm onSuccess={vi.fn()} />);

    await fillAndSubmit("", "");

    const username = screen.getByLabelText("Kullanıcı adı");
    expect(username).toHaveAttribute("aria-invalid", "true");
    expect(username).toHaveAccessibleDescription("Bu alan zorunludur.");
    await waitFor(() => expect(username).toHaveFocus());
    expect(post).not.toHaveBeenCalled();
  });

  it("disables the button while submitting and reports success (AC-6)", async () => {
    let resolve!: (value: unknown) => void;
    post.mockReturnValue(new Promise((r) => (resolve = r)) as never);
    const onSuccess = vi.fn();
    render(<LoginForm onSuccess={onSuccess} />);

    await fillAndSubmit("ayilmaz", "Guclu-Parola-2026!");
    expect(screen.getByRole("button", { name: "Giriş yapılıyor…" })).toBeDisabled();
    resolve({ data: { must_change_password: true }, response: new Response(null) });

    await waitFor(() => expect(onSuccess).toHaveBeenCalledWith(true));
  });

  it("shows the notice it is given (AC-13, AC-14)", () => {
    render(<LoginForm notice="sessionExpired" onSuccess={vi.fn()} />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "Oturumunuzun süresi doldu. Lütfen yeniden giriş yapın.",
    );
  });

  it("server error (5xx) shows the unreachable message, not a credentials error (M2)", async () => {
    answer(502, undefined);
    render(<LoginForm onSuccess={vi.fn()} />);

    await fillAndSubmit();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin.",
    );
  });

  it("refreshes the CSRF cookie and retries once on csrf_failed (M2)", async () => {
    const get = vi.mocked(api.GET);
    get.mockResolvedValue({ response: new Response(null, { status: 204 }) } as never);
    post
      .mockResolvedValueOnce({
        error: { code: "csrf_failed" },
        response: new Response(null, { status: 403 }),
      } as never)
      .mockResolvedValueOnce({
        data: { must_change_password: false },
        response: new Response(null),
      } as never);
    const onSuccess = vi.fn();
    render(<LoginForm onSuccess={onSuccess} />);

    await fillAndSubmit("ayilmaz", "Guclu-Parola-2026!");

    await waitFor(() => expect(onSuccess).toHaveBeenCalledWith(false));
    expect(get).toHaveBeenCalledWith("/api/auth/csrf/");
    expect(post).toHaveBeenCalledTimes(2);
  });
});
