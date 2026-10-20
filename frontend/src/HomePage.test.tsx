import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { HomePage, type Profile } from "./HomePage";

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
});
