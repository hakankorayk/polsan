import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "./api/client";
import { PasswordChangeForm } from "./PasswordChangeForm";

vi.mock("./api/client", async (original) => ({
  ...(await original<typeof import("./api/client")>()),
  api: { GET: vi.fn(), POST: vi.fn() },
}));

const post = vi.mocked(api.POST);

async function submit(newPassword: string, confirm = newPassword) {
  fireEvent.change(screen.getByLabelText("Yeni parola"), { target: { value: newPassword } });
  fireEvent.change(screen.getByLabelText("Yeni parola (tekrar)"), { target: { value: confirm } });
  fireEvent.click(screen.getByRole("button", { name: "Parolayı değiştir" }));
}

afterEach(() => post.mockReset());

describe("PasswordChangeForm", () => {
  it("shows server field errors, linked, with focus on the first (AC-11, AC-22)", async () => {
    post.mockResolvedValue({
      error: {
        code: "validation_error",
        errors: { new_password: ["Bu parola çok kısa. En az 12 karakter içermelidir."] },
      },
      response: new Response(null, { status: 400 }),
    } as never);
    render(<PasswordChangeForm onDone={vi.fn()} onSessionLost={vi.fn()} />);

    await submit("kisa");

    const field = screen.getByLabelText("Yeni parola");
    await waitFor(() => expect(field).toHaveAttribute("aria-invalid", "true"));
    expect(field).toHaveAccessibleDescription(
      expect.stringContaining("Bu parola çok kısa. En az 12 karakter içermelidir."),
    );
    await waitFor(() => expect(field).toHaveFocus());
  });

  it("shows the mismatch error on the confirmation field (AC-11)", async () => {
    post.mockResolvedValue({
      error: {
        code: "validation_error",
        errors: { new_password_confirm: ["Parolalar eşleşmiyor."] },
      },
      response: new Response(null, { status: 400 }),
    } as never);
    render(<PasswordChangeForm onDone={vi.fn()} onSessionLost={vi.fn()} />);

    await submit("Yepyeni-Parola-2027?", "Baska-Parola-2028!");

    const confirm = screen.getByLabelText("Yeni parola (tekrar)");
    await waitFor(() => expect(confirm).toHaveAccessibleDescription("Parolalar eşleşmiyor."));
    await waitFor(() => expect(confirm).toHaveFocus());
  });

  it("calls onDone after a successful change (AC-11)", async () => {
    post.mockResolvedValue({ response: new Response(null, { status: 204 }) } as never);
    const onDone = vi.fn();
    render(<PasswordChangeForm onDone={onDone} onSessionLost={vi.fn()} />);

    await submit("Yepyeni-Parola-2027?");

    await waitFor(() => expect(onDone).toHaveBeenCalledOnce());
    expect(post).toHaveBeenCalledWith("/api/auth/password/", {
      body: {
        new_password: "Yepyeni-Parola-2027?",
        new_password_confirm: "Yepyeni-Parola-2027?",
      },
    });
  });
});
