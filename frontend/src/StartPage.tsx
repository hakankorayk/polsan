import "./StartPage.css";

import type { ServerStatus } from "./useServerStatus";

export const STATUS_MESSAGES: Record<ServerStatus, string> = {
  checking: "Sunucu bağlantısı kontrol ediliyor…",
  connected: "Sunucu bağlantısı: Bağlı",
  unreachable: "Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin.",
};

export function StartPage({ status }: { status: ServerStatus }) {
  return (
    <main className="start-page">
      <h1>Polsan Leave Manager</h1>
      <p role="status" aria-live="polite" className={`server-status server-status--${status}`}>
        {STATUS_MESSAGES[status]}
      </p>
    </main>
  );
}
