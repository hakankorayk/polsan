import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StartPage } from "./StartPage";

describe("StartPage", () => {
  it("shows product name as the single h1 (AC-1)", () => {
    render(<StartPage status="checking" />);

    const headings = screen.getAllByRole("heading", { level: 1 });
    expect(headings).toHaveLength(1);
    expect(headings[0]).toHaveTextContent("Polsan Leave Manager");
  });

  it("shows checking message while pending (AC-3)", () => {
    render(<StartPage status="checking" />);

    expect(screen.getByRole("status")).toHaveTextContent("Sunucu bağlantısı kontrol ediliyor…");
  });

  it("shows connected message (AC-2)", () => {
    render(<StartPage status="connected" />);

    expect(screen.getByRole("status")).toHaveTextContent("Sunucu bağlantısı: Bağlı");
  });

  it("error message has no technical detail (AC-4)", () => {
    render(<StartPage status="unreachable" />);

    expect(screen.getByRole("status").textContent).toBe(
      "Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin.",
    );
  });

  it("status message is in a live status region (AC-19)", () => {
    render(<StartPage status="connected" />);

    expect(screen.getByRole("status")).toHaveAttribute("aria-live", "polite");
  });
});
