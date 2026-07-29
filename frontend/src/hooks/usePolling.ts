import { useEffect, useRef } from "react";

/** Poll `callback` on an interval while `enabled` is true. */
export function usePolling(
  callback: () => void | Promise<void>,
  enabled: boolean,
  intervalMs = 2000,
) {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  useEffect(() => {
    if (!enabled) return;

    let cancelled = false;

    async function tick() {
      if (cancelled) return;
      try {
        await callbackRef.current();
      } catch (err) {
        if (!cancelled) console.error(err);
      }
    }

    const interval = window.setInterval(tick, intervalMs);
    tick();

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [enabled, intervalMs]);
}
