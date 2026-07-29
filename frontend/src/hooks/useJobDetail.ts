import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Job } from "../types";
import { latestAnalysisForJob } from "../lib/matches";

interface UseJobDetailOptions {
  initialAnalysisId?: string;
}

export function useJobDetail(
  jobId: string | undefined,
  profileId: string | undefined,
  options: UseJobDetailOptions = {},
) {
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [matchAnalysisId, setMatchAnalysisId] = useState<string | undefined>(
    options.initialAnalysisId,
  );
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!jobId || !profileId) return;

    const jobData = await api.jobs.get(jobId);
    setJob(jobData);

    if (options.initialAnalysisId) {
      setMatchAnalysisId(options.initialAnalysisId);
      return;
    }

    const analyses = await api.matchAnalyses.list();
    const latest = latestAnalysisForJob(analyses, profileId, jobData.id);
    setMatchAnalysisId(latest?.id);
  }, [jobId, profileId, options.initialAnalysisId]);

  useEffect(() => {
    if (!jobId || !profileId) return;

    let cancelled = false;
    load()
      .catch((err) => {
        if (!cancelled) {
          console.error(err);
          navigate("/", { replace: true });
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [jobId, profileId, load, navigate]);

  return { job, setJob, matchAnalysisId, setMatchAnalysisId, loading };
}
