import type { MatchAnalysis, MatchResult } from "../types";

export function latestAnalysisForJob(
  analyses: MatchAnalysis[],
  profileId: string,
  jobId: string,
): MatchAnalysis | undefined {
  return analyses
    .filter((a) => a.profile_id === profileId && a.job_id === jobId)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];
}

export function scoreFromResult(result: MatchResult | null | undefined): number | null {
  if (!result || typeof result.score !== "number") return null;
  return result.score;
}

export function recommendationVariant(
  recommendation: MatchResult["recommendation"] | undefined,
): "success" | "warning" | "danger" | "default" {
  if (recommendation === "apply") return "success";
  if (recommendation === "maybe apply") return "warning";
  if (recommendation === "do not apply") return "danger";
  return "default";
}

export function recommendationLabel(recommendation: MatchResult["recommendation"] | undefined) {
  if (recommendation === "apply") return "Apply";
  if (recommendation === "maybe apply") return "Maybe";
  if (recommendation === "do not apply") return "Skip";
  return null;
}
