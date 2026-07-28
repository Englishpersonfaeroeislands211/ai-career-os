import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Job, JobExtraction, MatchAnalysis } from "../types";
import { Layout } from "../components/Layout";
import { MatchResultPanel } from "../components/MatchResultPanel";
import { useActiveProfile } from "../hooks/useActiveProfile";
import { latestAnalysisForJob } from "../lib/matches";
import {
  buildJobExtractSource,
  canExtractFromText,
  extractionMetadata,
} from "../lib/jobExtraction";
import { Badge, Button, ErrorBanner } from "../components/ui";

export function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { profile, loading: profileLoading, requireProfile } = useActiveProfile();
  const [job, setJob] = useState<Job | null>(null);
  const [analysis, setAnalysis] = useState<MatchAnalysis | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [reExtracting, setReExtracting] = useState(false);
  const [applyingExtraction, setApplyingExtraction] = useState(false);
  const [pendingExtraction, setPendingExtraction] = useState<{
    extraction: JobExtraction;
    jobText: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!profileLoading && !profile) requireProfile();
  }, [profileLoading, profile, requireProfile]);

  useEffect(() => {
    if (!id || !profile) return;
    async function load() {
      try {
        const [jobData, analyses] = await Promise.all([
          api.jobs.list().then((jobs) => jobs.find((j) => j.id === id) ?? null),
          api.matchAnalyses.list(),
        ]);
        if (!jobData) {
          navigate("/", { replace: true });
          return;
        }
        setJob(jobData);
        setAnalysis(latestAnalysisForJob(analyses, profile!.id, jobData.id) ?? null);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id, profile, navigate]);

  useEffect(() => {
    if (!analysis || analysis.status !== "pending") return;
    const analysisId = analysis.id;
    let cancelled = false;
    async function poll() {
      try {
        const updated = await api.matchAnalyses.get(analysisId);
        if (!cancelled) setAnalysis(updated);
      } catch (err) {
        console.error(err);
      }
    }
    const interval = window.setInterval(poll, 2000);
    poll();
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [analysis?.id, analysis?.status]);

  async function handleAnalyze() {
    if (!profile || !job) return;
    setAnalyzing(true);
    setError(null);
    try {
      const created = await api.matchAnalyses.create(profile.id, job.id);
      setAnalysis(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start analysis");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleReExtract() {
    if (!job) return;
    const sourceText = buildJobExtractSource(job);
    if (!canExtractFromText(sourceText)) {
      setError("Not enough job text to re-extract — edit the job and add a longer description");
      return;
    }

    setReExtracting(true);
    setError(null);
    try {
      const result = await api.jobs.parseText(sourceText);
      setPendingExtraction({
        extraction: result.structured_data,
        jobText: result.job_text,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to re-extract job fields");
    } finally {
      setReExtracting(false);
    }
  }

  async function handleApplyExtraction() {
    if (!job || !pendingExtraction) return;
    setApplyingExtraction(true);
    setError(null);
    try {
      const { extraction, jobText } = pendingExtraction;
      const updated = await api.jobs.update(job.id, {
        title: extraction.title,
        company: extraction.company,
        description: extraction.description,
        location: extraction.location ?? undefined,
        raw_metadata: {
          ...(job.raw_metadata ?? {}),
          ...extractionMetadata(extraction, jobText),
        },
      });
      setJob(updated);
      setPendingExtraction(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update job");
    } finally {
      setApplyingExtraction(false);
    }
  }

  if (profileLoading || loading || !profile || !job) {
    return (
      <Layout subtitle="Job">
        <main className="flex min-h-[50vh] items-center justify-center">
          <span className="size-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        </main>
      </Layout>
    );
  }

  const requirements = Array.isArray(job.raw_metadata?.requirements)
    ? (job.raw_metadata.requirements as string[])
    : [];
  const canReExtract = canExtractFromText(buildJobExtractSource(job));
  const analysisPending = analysis?.status === "pending";
  const showAnalyzeButton = !analysisPending;
  const analyzeLabel =
    analysis?.status === "failed"
      ? "Retry analysis"
      : analysis?.status === "completed"
        ? "Re-analyze match"
        : "Analyze match";

  return (
    <Layout subtitle={`${job.title} @ ${job.company}`}>
      <main className="mx-auto max-w-3xl space-y-6 px-6 py-8">
        <Link to="/" className="text-sm text-text-muted hover:text-accent">
          ← All opportunities
        </Link>

        {error && <ErrorBanner message={error} />}

        <section className="rounded-xl border border-border bg-surface-raised p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">{job.title}</h2>
              <p className="mt-1 text-text-muted">
                {job.company}
                {job.location ? ` · ${job.location}` : ""}
              </p>
              {job.url && (
                <a
                  href={job.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-block text-sm text-accent hover:underline"
                >
                  View posting
                </a>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {showAnalyzeButton && (
                <Button onClick={handleAnalyze} loading={analyzing}>
                  {analyzeLabel}
                </Button>
              )}
              <Button
                variant="ghost"
                onClick={handleReExtract}
                loading={reExtracting}
                disabled={!canReExtract}
              >
                Re-extract fields
              </Button>
            </div>
          </div>

          {pendingExtraction && (
            <section className="mt-4 rounded-lg border border-accent/30 bg-accent/5 p-4">
              <h3 className="text-sm font-medium">Review extracted fields</h3>
              <p className="mt-1 text-sm text-text-muted">
                Apply these changes to update the saved job, or cancel to keep the current version.
              </p>
              <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-text-muted">Title</dt>
                  <dd className="font-medium">{pendingExtraction.extraction.title}</dd>
                </div>
                <div>
                  <dt className="text-text-muted">Company</dt>
                  <dd className="font-medium">{pendingExtraction.extraction.company}</dd>
                </div>
                <div>
                  <dt className="text-text-muted">Location</dt>
                  <dd className="font-medium">{pendingExtraction.extraction.location ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-text-muted">Employment</dt>
                  <dd className="font-medium">{pendingExtraction.extraction.employment_type ?? "—"}</dd>
                </div>
              </dl>
              {pendingExtraction.extraction.requirements.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {pendingExtraction.extraction.requirements.slice(0, 8).map((req) => (
                    <Badge key={req} variant="info">
                      {req}
                    </Badge>
                  ))}
                </div>
              )}
              <div className="mt-4 flex gap-2">
                <Button onClick={handleApplyExtraction} loading={applyingExtraction}>
                  Apply changes
                </Button>
                <Button variant="ghost" onClick={() => setPendingExtraction(null)}>
                  Cancel
                </Button>
              </div>
            </section>
          )}

          {requirements.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {requirements.slice(0, 8).map((req) => (
                <Badge key={req} variant="info">
                  {req}
                </Badge>
              ))}
            </div>
          )}

          <div className="mt-6">
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-text-muted">
              Description
            </h3>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-text">{job.description}</p>
          </div>
        </section>

        <MatchResultPanel
          analysis={analysis}
          profileName={profile.name}
          jobTitle={`${job.title} @ ${job.company}`}
        />
      </main>
    </Layout>
  );
}
