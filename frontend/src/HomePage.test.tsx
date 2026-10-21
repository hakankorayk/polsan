import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { api } from "./api/client";
import { HomePage, type Profile } from "./HomePage";

// The balance section loads on its own (spec 0003); here it only needs an answer.
vi.mock("./api/client", async (original) => ({
  ...(await original<typeof import("./api/client")>()),
  api: { GET: vi.fn() },
}));
vi.mocked(api.GET).mockImplementation(
  () => Promise.resolve({ error: { code: "server_error" }, response: new Response(null) }) as never,
);

const manager: Profile = {
  first_name: "Zeynep",
  last_name: "Yönetici",
  roles: ["employee", "manager", "hr"],
  team: [
    { first_name: "Mehmet", last_name: "Çelik" },
    { first_name: "Ece", last_name: "Demir" },
  ],
};

describe("HomePage", () => {
  it("shows name and roles (AC-15)", () => {
    render(<HomePage profile={manager} loggingOut={false} onLogout={vi.fn()} />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Hoş geldiniz, Zeynep Yönetici",
    );
    expect(screen.getByText("Rolleriniz: Çalışan, Yönetici, İK")).toBeInTheDocument();
  });

  it("lists the team in the order the server sends (AC-16)", () => {
    render(<HomePage profile={manager} loggingOut={false} onLogout={vi.fn()} />);

    const team = screen.getByRole("region", { name: "Ekibim" });
    expect(
      within(team)
        .getAllByRole("listitem")
        .map((li) => li.textContent),
    ).toEqual(["Mehmet Çelik", "Ece Demir"]);
  });

  it("no team section for non manager (AC-16)", () => {
    render(
      <HomePage
        profile={{ ...manager, roles: ["employee"], team: null }}
        loggingOut={false}
        onLogout={vi.fn()}
      />,
    );

    expect(screen.queryByRole("region", { name: "Ekibim" })).not.toBeInTheDocument();
  });

  it("renders two reports with the same name without key collisions (L8)", () => {
    const errors = vi.spyOn(console, "error").mockImplementation(() => {});
    const twins = { ...manager, team: [manager.team![0], manager.team![0]] };

    render(<HomePage profile={twins} loggingOut={false} onLogout={vi.fn()} />);

    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(errors).not.toHaveBeenCalled();
    errors.mockRestore();
  });

  it("keeps the rest of the page when the balance fails to load (spec 0003, AC-28)", async () => {
    render(<HomePage profile={manager} loggingOut={false} onLogout={vi.fn()} />);

    const balance = screen.getByRole("region", { name: "İzin bakiyem" });
    expect(await within(balance).findByRole("alert")).toBeVisible();
    expect(screen.getByRole("heading", { level: 1 })).toBeVisible();
    expect(screen.getByRole("region", { name: "Ekibim" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Çıkış yap" })).toBeVisible();
  });
});
