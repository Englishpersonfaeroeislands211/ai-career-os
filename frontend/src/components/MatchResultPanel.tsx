import type { MatchAnalysis, MatchResult } from "../types";
import { AiLoadingState } from "./AiLoadingState";
import { ScoreRing } from "./ScoreRing";
import { Badge, Card } from "./ui";

interface MatchResultPanelProps {
  analysis: MatchAnalysis | null;
  profileName?: string;
  jobTitle?: string;
  /** When true, strengths/gaps collapse behind "Show details" after full analysis */
  compactWhenComplete?: boolean;
}

const recommendationLabels: Record<
  MatchResult["recommendation"],
  { label: string; variant: "success" | "warning" | "danger" }
> = {
  apply: { label: "Apply", variant: "success" },
  "maybe apply": { label: "Maybe", variant: "warning" },
  "do not apply": { label: "Skip", variant: "danger" },
};

function ResultContent({
  result,
  compactDetails = false,
}: {
  result: MatchResult;
  compactDetails?: boolean;
}) {
  const rec = recommendationLabels[result.recommendation];
  const isScreen = result.depth === "screen";
  const hasDetails =
    !isScreen && ((result.strengths?.length ?? 0) > 0 || (result.gaps?.length ?? 0) > 0);

  const detailsBlock = (
    <>
      {!isScreen && (result.strengths?.length ?? 0) > 0 && (
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

      {!isScreen && (result.gaps?.length ?? 0) > 0 && (
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
    </>
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-6">
        <ScoreRing score={result.score} size="lg" />
        <div className="flex flex-wrap gap-2">
          <Badge variant={rec.variant}>{rec.label}</Badge>
          <Badge variant={isScreen ? "info" : "default"}>
            {isScreen ? "Screening" : "Full analysis"}
          </Badge>
        </div>
      </div>

      {isScreen && result.reason && (
        <p className="text-sm text-text-muted">{result.reason}</p>
      )}

      <div>
        <h3 className="mb-2 text-sm font-medium text-text-muted">Summary</h3>
        <p className="text-sm leading-relaxed text-text">{result.summary}</p>
      </div>

      {compactDetails && hasDetails ? (
        <details className="group">
          <summary className="cursor-pointer text-sm font-medium text-accent hover:underline">
            Show strengths & gaps ({result.strengths?.length ?? 0} strengths,{" "}
            {result.gaps?.length ?? 0} gaps)
          </summary>
          <div className="mt-4 space-y-6">{detailsBlock}</div>
        </details>
      ) : (
        detailsBlock
      )}
    </div>
  );
}

function severityVariant(severity: MatchResult["gaps"][number]["severity"]) {
  if (severity === "high") return "danger";
  if (severity === "medium") return "warning";
  return "info";
}

function PendingState() {
  return <AiLoadingState variant="match-screen" size="md" />;
}

function DeepAnalysisPending() {
  return <AiLoadingState variant="match-progressive" size="sm" />;
}

export function MatchResultPanel({
  analysis,
  profileName,
  jobTitle,
  compactWhenComplete = false,
}: MatchResultPanelProps) {
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

  const screenPreview =
    analysis.status === "pending" && analysis.result?.depth === "screen"
      ? analysis.result
      : null;

  const useCompactDetails =
    compactWhenComplete &&
    analysis.status === "completed" &&
    analysis.result?.depth !== "screen";

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
      {analysis.status === "pending" && !screenPreview && <PendingState />}

      {screenPreview && (
        <div className="space-y-6">
          <ResultContent result={screenPreview} />
          <DeepAnalysisPending />
        </div>
      )}

      {analysis.status === "failed" && (
        <div className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {analysis.error ?? "Analysis failed"}
        </div>
      )}

      {analysis.status === "completed" && analysis.result && (
        <div className="space-y-4">
          <ResultContent result={analysis.result} compactDetails={useCompactDetails} />
          {analysis.error && (
            <div className="rounded-lg border border-warning/30 bg-warning/10 px-4 py-3 text-sm text-warning">
              {analysis.error}
            </div>
          )}
        </div>
      )}

      {analysis.status === "completed" && !analysis.result && (
        <p className="py-4 text-center text-sm text-text-muted">No result data yet.</p>
      )}
    </Card>
  );
}
