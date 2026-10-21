/** Display formatting only (spec 0003, AC-25): the server computes every amount, this file just
 * writes the decimal strings it sends ("12.5", "-2.0") the Turkish way. No arithmetic here
 * (docs/architecture.md, Forbidden dependencies 6). */

/** U+2212, the typographic minus: "−2 gün". */
export const MINUS = "−";

type Parts = { negative: boolean; digits: string };

/** "-12.50" -> { negative: true, digits: "12,5" }; "14.0" -> { negative: false, digits: "14" } */
function parts(value: string): Parts {
  const negative = value.startsWith("-");
  const [whole, fraction = ""] = value.replace(/^[-+]/, "").split(".");
  const trimmed = fraction.replace(/0+$/, "");
  return { negative, digits: trimmed ? `${whole},${trimmed}` : whole };
}

export function isNegative(value: string): boolean {
  const { negative, digits } = parts(value);
  return negative && digits !== "0";
}

/** "12.5" -> "12,5 gün"; "-3.0" -> "−3 gün" (balances may be negative after an HR adjustment). */
export function formatDays(value: string): string {
  const { digits } = parts(value);
  return `${isNegative(value) ? MINUS : ""}${digits} gün`;
}

/** Ledger movements always carry their sign: "+14 gün", "−2 gün". */
export function formatSignedDays(value: string): string {
  return isNegative(value) ? formatDays(value) : `+${parts(value).digits} gün`;
}

/** Magnitude only, for markup that renders the sign separately (screen reader "eksi"). */
export function formatDaysMagnitude(value: string): string {
  return `${parts(value).digits} gün`;
}

/** ISO calendar date "2027-03-10" -> "10.03.2027". */
export function formatDate(iso: string): string {
  const [year, month, day] = iso.split("-");
  return `${day}.${month}.${year}`;
}
