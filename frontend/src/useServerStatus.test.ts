import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "./api/client";
import { STATUS_TIMEOUT_MS, useServerStatus } from "./useServerStatus";

vi.mock("./api/client", () => ({ api: { GET: vi.fn() } }));

const get = vi.mocked(api.GET);

function answer(status: number, body: unknown) {
  get.mockResolvedValue({
    data: status < 400 ? body : undefined,
    error: status >= 400 ? body : undefined,
    response: new Response(JSON.stringify(body), { status }),
  } as never);
}

afterEach(() => {
  vi.useRealTimers();
  get.mockReset();
});

describe("useServerStatus", () => {
  it("starts as checking (AC-3)", () => {
    get.mockReturnValue(new Promise(() => {}) as never);

    const { result } = renderHook(() => useServerStatus());

    expect(result.current).toBe("checking");
  });

  it("is connected when the server reports ok (AC-2)", async () => {
    answer(200, { status: "ok" });

    const { result } = renderHook(() => useServerStatus());

    await waitFor(() => expect(result.current).toBe("connected"));
    expect(get).toHaveBeenCalledWith("/api/health/", expect.anything());
  });

  it("error on non-2xx (AC-4)", async () => {
    answer(503, { status: "unavailable" });

    const { result } = renderHook(() => useServerStatus());

    await waitFor(() => expect(result.current).toBe("unreachable"));
  });

  it("error on network failure (AC-4)", async () => {
    get.mockRejectedValue(new TypeError("Failed to fetch"));

    const { result } = renderHook(() => useServerStatus());

    await waitFor(() => expect(result.current).toBe("unreachable"));
  });

  it("error after 5s timeout (AC-4)", async () => {
    vi.useFakeTimers();
    get.mockImplementation(
      ((_path: string, init: { signal: AbortSignal }) =>
        new Promise((_resolve, reject) => {
          init.signal.addEventListener("abort", () => reject(new DOMException("aborted")));
        })) as never,
    );

    const { result } = renderHook(() => useServerStatus());

    await act(async () => {
      await vi.advanceTimersByTimeAsync(STATUS_TIMEOUT_MS - 1);
    });
    expect(result.current).toBe("checking");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(result.current).toBe("unreachable");
  });
});
