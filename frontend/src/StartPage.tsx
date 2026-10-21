import "./StartPage.css";

import type { ReactNode } from "react";

import type { ServerStatus } from "./useServerStatus";

export const STATUS_MESSAGES: Record<ServerStatus, string> = {
  checking: "Sunucu bağlantısı kontrol ediliyor…",
  connected: "Sunucu bağlantısı: Bağlı",
  unreachable: "Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin.",
};

/** Product name + server status (spec 0001), and since spec 0002 the login form as children. */
export function StartPage({ status, children }: { status: ServerStatus; children?: ReactNode }) {
  return (
    <main className="start-page">
      <h1>Polsan Leave Manager</h1>
      <p role="status" aria-live="polite" className={`server-status server-status--${status}`}>
        {STATUS_MESSAGES[status]}
      </p>
      {children}
    </main>
  );
}
