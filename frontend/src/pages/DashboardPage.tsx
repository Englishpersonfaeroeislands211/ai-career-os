import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Job, MatchAnalysis, Profile } from "../types";
import { JobPanel } from "../components/JobPanel";
import { Layout } from "../components/Layout";
import { MatchResultPanel } from "../components/MatchResultPanel";
import { getActiveProfileId } from "../lib/profile";
import { Badge, Button, ErrorBanner } from "../components/ui";

export function DashboardPage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobTitle, setJobTitle] = useState<string>();
  const [currentAnalysis, setCurrentAnalysis] = useState<MatchAnalysis | null>(null);
  const [history, setHistory] = useState<MatchAnalysis[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const profiles = await api.profiles.list();
        if (profiles.length === 0) {
          navigate("/", { replace: true });
          return;
        }

        const activeId = getActiveProfileId();
        const active = profiles.find((p) => p.id === activeId) ?? profiles[0];
        setProfile(active);

        const analyses = await api.matchAnalyses.list();
        setHistory(analyses);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [navigate]);

  async function handleAnalyze() {
    if (!profile || !jobId) return;
    setAnalyzing(true);
    setError(null);
    try {
      const analysis = await api.matchAnalyses.create(profile.id, jobId);
      setCurrentAnalysis(analysis);
      setHistory((prev) => [analysis, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create analysis");
    } finally {
      setAnalyzing(false);
    }
  }

  function handleHistorySelect(analysis: MatchAnalysis) {
    setCurrentAnalysis(analysis);
    setJobId(analysis.job_id);
  }

  if (loading) {
    return (
      <Layout>
        <main className="flex min-h-[50vh] items-center justify-center">
          <span className="size-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        </main>
      </Layout>
    );
  }

  if (!profile) return null;

  return (
    <Layout subtitle="Match Explorer">
      <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
        {error && <ErrorBanner message={error} />}

        <section className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-surface-raised px-5 py-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
              Active profile
            </p>
            <p className="mt-1 font-semibold">{profile.name}</p>
            {profile.headline && (
              <p className="text-sm text-text-muted">{profile.headline}</p>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <Link to="/settings">
              <Button variant="secondary" className="text-sm">
                AI settings
              </Button>
            </Link>
            <Link to="/onboarding/upload">
              <Button variant="secondary" className="text-sm">
                Upload new resume
              </Button>
            </Link>
          </div>
        </section>

        <JobPanel
          selectedId={jobId}
          onSelect={(j: Job) => {
            setJobId(j.id || null);
            setJobTitle(j.title ? `${j.title} @ ${j.company}` : undefined);
          }}
          onSaved={(j) => {
            setJobId(j.id);
            setJobTitle(`${j.title} @ ${j.company}`);
          }}
        />

        <div className="flex justify-center">
          <Button
            onClick={handleAnalyze}
            loading={analyzing}
            disabled={!jobId}
            className="px-8 py-3 text-base"
          >
            Analyze match
          </Button>
        </div>

        <MatchResultPanel
          analysis={currentAnalysis}
          profileName={profile.name}
          jobTitle={jobTitle}
        />

        {history.length > 0 && (
          <section className="rounded-xl border border-border bg-surface-raised">
            <div className="border-b border-border px-5 py-4">
              <h2 className="text-base font-semibold">Recent analyses</h2>
            </div>
            <ul className="divide-y divide-border">
              {history.map((a) => (
                <li key={a.id}>
                  <button
                    type="button"
                    onClick={() => handleHistorySelect(a)}
                    className="flex w-full items-center justify-between px-5 py-3 text-left text-sm transition hover:bg-surface-overlay"
                  >
                    <span className="text-text-muted">
                      {new Date(a.created_at).toLocaleString()}
                    </span>
                    <Badge
                      variant={
                        a.status === "completed"
                          ? "success"
                          : a.status === "failed"
                            ? "danger"
                            : "info"
                      }
                    >
                      {a.status}
                    </Badge>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>
    </Layout>
  );
}
