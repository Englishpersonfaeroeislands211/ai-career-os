import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Job, MatchAnalysis } from "../types";
import { JobBoard } from "../components/JobBoard";
import { Layout } from "../components/Layout";
import { AiLoadingState, PageLoader } from "../components/AiLoadingState";
import { useActiveProfile } from "../hooks/useActiveProfile";
import { pendingAnalysesCount, scoreFromResult, latestAnalysisForJob } from "../lib/matches";
import { Button } from "../components/ui";

export function HomePage() {
  const { profile, loading, requireProfile } = useActiveProfile();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [analyses, setAnalyses] = useState<MatchAnalysis[]>([]);
  const [dataLoading, setDataLoading] = useState(true);

  const refreshAnalyses = useCallback(async () => {
    if (!profile) return;
    const analysisList = await api.matchAnalyses.list();
    setAnalyses(analysisList.filter((a) => a.profile_id === profile.id));
  }, [profile]);

  useEffect(() => {
    if (!loading && !profile) {
      requireProfile();
    }
  }, [loading, profile, requireProfile]);

  useEffect(() => {
    if (!profile) return;
    async function load() {
      try {
        const [jobList, analysisList] = await Promise.all([
          api.jobs.list(),
          api.matchAnalyses.list(),
        ]);
        setJobs(jobList);
        setAnalyses(analysisList.filter((a) => a.profile_id === profile!.id));
      } catch (err) {
        console.error(err);
      } finally {
        setDataLoading(false);
      }
    }
    load();
  }, [profile]);

  const pendingCount = profile ? pendingAnalysesCount(analyses, profile.id) : 0;

  useEffect(() => {
    if (!profile || pendingCount === 0) return;

    let cancelled = false;
    async function poll() {
      try {
        await refreshAnalyses();
      } catch (err) {
        if (!cancelled) console.error(err);
      }
    }

    const interval = window.setInterval(poll, 2000);
    poll();
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [profile, pendingCount, refreshAnalyses]);

  if (loading || !profile) {
    return (
      <Layout title="Pipeline" subtitle="Your job opportunities">
        <PageLoader variant="page" />
      </Layout>
    );
  }

  const analyzedCount = jobs.filter((job) => {
    const a = latestAnalysisForJob(analyses, profile.id, job.id);
    return a?.status === "completed";
  }).length;

  const topMatch = jobs
    .map((job) => ({
      job,
      score: scoreFromResult(latestAnalysisForJob(analyses, profile.id, job.id)?.result),
    }))
    .filter((item) => item.score != null)
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))[0];

  return (
    <Layout title="Pipeline" subtitle="Your job opportunities">
      <div className="space-y-8">
        <section className="rounded-2xl border border-border bg-surface-raised p-6 shadow-sm sm:p-8">
          <div className="relative z-10 flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-accent">Your profile</p>
              <h2 className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">{profile.name}</h2>
              {profile.headline && (
                <p className="mt-2 max-w-xl text-text-muted">{profile.headline}</p>
              )}
              <Link
                to="/profile"
                className="mt-4 inline-block text-sm font-medium text-accent hover:underline"
              >
                View full profile →
              </Link>
            </div>
            <div className="flex flex-wrap gap-6">
              <Stat label="Jobs tracked" value={String(jobs.length)} />
              <Stat label="Analyzed" value={`${analyzedCount}/${jobs.length}`} />
              {topMatch?.score != null && (
                <Stat label="Best match" value={`${Math.round(topMatch.score)}%`} />
              )}
            </div>
          </div>
        </section>

        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-semibold">Opportunities</h3>
              <p className="text-sm text-text-muted">
                {pendingCount > 0
                  ? `Analyzing ${pendingCount} job${pendingCount === 1 ? "" : "s"}…`
                  : "Ranked by match score — each job is analyzed when you add it."}
              </p>
            </div>
            <Link to="/jobs/new">
              <Button>Add job</Button>
            </Link>
          </div>

          {dataLoading ? (
            <AiLoadingState variant="page" size="md" />
          ) : (
            <JobBoard jobs={jobs} analyses={analyses} profileId={profile.id} />
          )}
        </section>
      </div>
    </Layout>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-[5rem]">
      <p className="text-2xl font-bold tabular-nums">{value}</p>
      <p className="text-xs text-text-muted">{label}</p>
    </div>
  );
}
