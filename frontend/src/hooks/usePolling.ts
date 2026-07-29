import { useEffect } from "react";

/** Poll `callback` on an interval while `enabled` is true. */
export function usePolling(
  callback: () => void | Promise<void>,
  enabled: boolean,
  intervalMs = 2000,
) {
  useEffect(() => {
    if (!enabled) return;

    let cancelled = false;

    async function tick() {
      try {
        await callback();
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
  }, [callback, enabled, intervalMs]);
}
