import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { MatchAnalysis } from "../types";
import { usePolling } from "./usePolling";

export function useMatchAnalysis(analysisId: string | null | undefined) {
  const [analysis, setAnalysis] = useState<MatchAnalysis | null>(null);
  const [loading, setLoading] = useState(Boolean(analysisId));

  const refresh = useCallback(async () => {
    if (!analysisId) return null;
    const updated = await api.matchAnalyses.get(analysisId);
    setAnalysis(updated);
    return updated;
  }, [analysisId]);

  useEffect(() => {
    if (!analysisId) {
      setAnalysis(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    refresh()
      .catch((err) => {
        if (!cancelled) console.error(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [analysisId, refresh]);

  const poll = useCallback(async () => {
    await refresh();
  }, [refresh]);

  usePolling(poll, analysis?.status === "pending");

  return { analysis, setAnalysis, loading, refresh };
}
