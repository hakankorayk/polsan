import { describe, expect, it } from "vitest";

import {
  formatDate,
  formatDays,
  formatDaysMagnitude,
  formatSignedDays,
  isNegative,
} from "./formatDays";

describe("formatDays (spec 0003, AC-25)", () => {
  it.each([
    ["12.5", "12,5 gün"],
    ["14.0", "14 gün"],
    ["0.0", "0 gün"],
    ["100", "100 gün"],
    ["-3.0", "−3 gün"],
    ["-0.5", "−0,5 gün"],
  ])("%s -> %s", (value, text) => {
    expect(formatDays(value)).toBe(text);
  });

  it.each([
    ["14.0", "+14 gün"],
    ["12.5", "+12,5 gün"],
    ["-2.0", "−2 gün"],
  ])("signed %s -> %s", (value, text) => {
    expect(formatSignedDays(value)).toBe(text);
  });

  it("magnitude drops the sign", () => {
    expect(formatDaysMagnitude("-2.5")).toBe("2,5 gün");
    expect(isNegative("-2.5")).toBe(true);
    expect(isNegative("-0.0")).toBe(false);
  });

  it("dates as DD.MM.YYYY", () => {
    expect(formatDate("2027-03-10")).toBe("10.03.2027");
  });
});
