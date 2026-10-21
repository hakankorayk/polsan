import { useEffect, useState } from "react";

import { api } from "./api/client";
import type { components } from "./api/schema";
import {
  formatDate,
  formatDays,
  formatDaysMagnitude,
  formatSignedDays,
  isNegative,
  MINUS,
} from "./formatDays";
import { LEDGER_KIND_LABELS, MESSAGES } from "./messages";

type Summary = components["schemas"]["BalanceSummary"];
type State = { kind: "loading" } | { kind: "error" } | { kind: "ready"; summary: Summary };

/** A day amount whose minus sign a screen reader says as "eksi" (spec 0003, Accessibility). */
function Days({ value, signed = false }: { value: string; signed?: boolean }) {
  const text = signed ? formatSignedDays(value) : formatDays(value);
  if (!isNegative(value)) return <>{text}</>;
  return (
    <>
      <span aria-hidden="true">{MINUS}</span>
      <span className="visually-hidden">eksi </span>
      {formatDaysMagnitude(value)}
    </>
  );
}

/** Spec 0003, AC-22 … AC-28: the signed-in employee's own balance, loaded on its own so a
 * failure here leaves the rest of the home page standing. */
export function BalanceSection() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let current = true;
    api
      .GET("/api/balance/")
      .then(({ data }) => {
        if (current) setState(data ? { kind: "ready", summary: data } : { kind: "error" });
      })
      .catch(() => {
        if (current) setState({ kind: "error" });
      });
    return () => {
      current = false;
    };
  }, []);

  return (
    <section aria-labelledby="balance-heading">
      <h2 id="balance-heading">İzin bakiyem</h2>
      {state.kind === "loading" && <p role="status">{MESSAGES.balanceLoading}</p>}
      {state.kind === "error" && <p role="alert">{MESSAGES.balanceFailed}</p>}
      {state.kind === "ready" && <BalanceDetails summary={state.summary} />}
    </section>
  );
}

function BalanceDetails({ summary }: { summary: Summary }) {
  const { balance, next_accrual: next, entries } = summary;
  return (
    <>
      <p>
        Bakiye:{" "}
        <strong>
          <Days value={balance} />
        </strong>
      </p>
      {next && (
        <p>
          Sonraki hak ediş: {formatDate(next.date)} — {formatDays(next.days)}
        </p>
      )}
      {entries.length === 0 ? (
        <p>{MESSAGES.balanceEmpty}</p>
      ) : (
        <table className="ledger">
          <caption>Hareketler</caption>
          <thead>
            <tr>
              <th scope="col">Tarih</th>
              <th scope="col">Tür</th>
              <th scope="col">Miktar</th>
              <th scope="col">Gerekçe</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.id}>
                <td>{formatDate(entry.date)}</td>
                <td>{LEDGER_KIND_LABELS[entry.kind] ?? entry.kind}</td>
                <td>
                  <Days value={entry.amount} signed />
                </td>
                <td>{entry.reason ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
