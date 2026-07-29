import type { MatchAnalysis, MatchResult } from "../types";
import { AiLoadingState } from "./AiLoadingState";
import { ScoreRing } from "./ScoreRing";
import { Badge, Card } from "./ui";

interface MatchResultPanelProps {
  analysis: MatchAnalysis | null;
  profileName?: string;
  jobTitle?: string;
}

const recommendationLabels: Record<
  MatchResult["recommendation"],
  { label: string; variant: "success" | "warning" | "danger" }
> = {
  apply: { label: "Apply", variant: "success" },
  "maybe apply": { label: "Maybe", variant: "warning" },
  "do not apply": { label: "Skip", variant: "danger" },
};

function ResultContent({ result }: { result: MatchResult }) {
  const rec = recommendationLabels[result.recommendation];
  const isLegacyScreen = result.depth === "screen";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-6">
        <ScoreRing score={result.score} size="lg" />
        <div className="flex flex-wrap gap-2">
          <Badge variant={rec.variant}>{rec.label}</Badge>
        </div>
      </div>

      {isLegacyScreen && result.reason && (
        <p className="text-sm text-text-muted">{result.reason}</p>
      )}

      <div>
        <h3 className="mb-2 text-sm font-medium text-text-muted">Summary</h3>
        <p className="text-sm leading-relaxed text-text">{result.summary}</p>
      </div>

      {!isLegacyScreen && (result.strengths?.length ?? 0) > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-medium text-success">Strengths</h3>
          <ul className="space-y-3">
            {result.strengths.map((s, i) => (
              <li
                key={i}
                className="rounded-lg border border-success/20 bg-success/5 px-4 py-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm text-text">{s.evidence}</p>
                  <Badge variant="success">{s.point.toFixed(1)}/10</Badge>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!isLegacyScreen && (result.gaps?.length ?? 0) > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-medium text-warning">Gaps</h3>
          <ul className="space-y-3">
            {result.gaps.map((g, i) => (
              <li
                key={i}
                className="rounded-lg border border-warning/20 bg-warning/5 px-4 py-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm text-text">{g.evidence}</p>
                  <div className="flex shrink-0 gap-2">
                    <Badge variant={severityVariant(g.severity)}>{g.severity}</Badge>
                    <Badge variant="warning">{g.point.toFixed(1)}/10</Badge>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function severityVariant(severity: MatchResult["gaps"][number]["severity"]) {
  if (severity === "high") return "danger";
  if (severity === "medium") return "warning";
  return "info";
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
      {analysis.status === "pending" && <AiLoadingState variant="match-full" size="md" />}

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
