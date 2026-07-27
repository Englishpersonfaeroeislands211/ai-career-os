import type { MatchAnalysis, MatchResult } from "../types";
import { Badge, Card } from "./ui";

interface MatchResultPanelProps {
  analysis: MatchAnalysis | null;
  profileName?: string;
  jobTitle?: string;
}

const recommendationLabels: Record<string, { label: string; variant: "success" | "warning" | "danger" }> = {
  apply: { label: "Apply", variant: "success" },
  maybe: { label: "Maybe", variant: "warning" },
  skip: { label: "Skip", variant: "danger" },
};

function ScoreRing({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 70 ? "text-success" : pct >= 40 ? "text-warning" : "text-danger";

  return (
    <div className="flex flex-col items-center gap-1">
      <span className={`text-4xl font-bold tabular-nums ${color}`}>{pct}%</span>
      <span className="text-xs text-text-muted">match score</span>
    </div>
  );
}

function ResultContent({ result }: { result: MatchResult }) {
  const rec = result.recommendation
    ? recommendationLabels[result.recommendation]
    : null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-6">
        {result.match_score != null && <ScoreRing score={result.match_score} />}
        {rec && <Badge variant={rec.variant}>{rec.label}</Badge>}
      </div>

      {result.summary && (
        <div>
          <h3 className="mb-2 text-sm font-medium text-text-muted">Summary</h3>
          <p className="text-sm leading-relaxed text-text">{result.summary}</p>
        </div>
      )}

      {result.strengths && result.strengths.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-medium text-success">Strengths</h3>
          <ul className="space-y-3">
            {result.strengths.map((s, i) => (
              <li
                key={i}
                className="rounded-lg border border-success/20 bg-success/5 px-4 py-3"
              >
                <p className="text-sm font-medium text-text">{s.point}</p>
                {s.evidence && (
                  <p className="mt-1 text-xs text-text-muted italic">
                    &ldquo;{s.evidence}&rdquo;
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.gaps && result.gaps.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-medium text-warning">Gaps</h3>
          <ul className="space-y-3">
            {result.gaps.map((g, i) => (
              <li
                key={i}
                className="rounded-lg border border-warning/20 bg-warning/5 px-4 py-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm text-text">{g.point}</p>
                  <Badge variant={g.severity === "blocker" ? "danger" : "warning"}>
                    {g.severity}
                  </Badge>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function PendingState() {
  return (
    <div className="flex flex-col items-center gap-3 py-8 text-center">
      <div className="size-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      <p className="text-sm text-text-muted">
        Analysis pending — the AI matcher isn&apos;t wired yet.
      </p>
      <p className="max-w-sm text-xs text-text-muted">
        Once the matcher service lands, results will appear here with score, strengths, gaps, and
        evidence.
      </p>
    </div>
  );
}

export function MatchResultPanel({ analysis, profileName, jobTitle }: MatchResultPanelProps) {
  if (!analysis) {
    return (
      <Card title="Match result" description="Run an analysis to see explainable output here">
        <p className="py-8 text-center text-sm text-text-muted">
          Save a profile and job, then click &ldquo;Analyze match&rdquo;.
        </p>
      </Card>
    );
  }

  const statusVariant =
    analysis.status === "completed"
      ? "success"
      : analysis.status === "failed"
        ? "danger"
        : "info";

  return (
    <Card
      title="Match result"
      description={
        profileName && jobTitle
          ? `${profileName} → ${jobTitle}`
          : "Explainable match analysis"
      }
      action={<Badge variant={statusVariant}>{analysis.status}</Badge>}
    >
      {analysis.status === "pending" && <PendingState />}

      {analysis.status === "failed" && (
        <div className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {analysis.error ?? "Analysis failed"}
        </div>
      )}

      {analysis.status === "completed" && analysis.result && (
        <ResultContent result={analysis.result} />
      )}

      {analysis.status === "completed" && !analysis.result && (
        <p className="py-4 text-center text-sm text-text-muted">No result data yet.</p>
      )}
    </Card>
  );
}
