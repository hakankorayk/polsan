import { useEffect, useState } from "react";

import { api } from "./api/client";

export type ServerStatus = "checking" | "connected" | "unreachable";

/** Spec 0001, AC-4: no answer within this time counts as unreachable. */
export const STATUS_TIMEOUT_MS = 5000;

async function isServerHealthy(signal: AbortSignal): Promise<boolean> {
  try {
    const { data, response } = await api.GET("/api/health/", { signal });
    return response.ok && data?.status === "ok";
  } catch {
    return false; // network failure or timeout abort
  }
}

/** Asks the server once, on mount, whether it and its database are reachable. */
export function useServerStatus(): ServerStatus {
  const [status, setStatus] = useState<ServerStatus>("checking");

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), STATUS_TIMEOUT_MS);
    let active = true;

    void isServerHealthy(controller.signal).then((healthy) => {
      clearTimeout(timer);
      if (active) setStatus(healthy ? "connected" : "unreachable");
    });

    return () => {
      active = false;
      clearTimeout(timer);
      controller.abort();
    };
  }, []);

  return status;
}
