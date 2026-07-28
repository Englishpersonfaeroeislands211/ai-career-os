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

export function hasScreenPreview(analysis: MatchAnalysis | null | undefined): boolean {
  return analysis?.status === "pending" && analysis.result?.depth === "screen";
}

export function hasMatchResult(analysis: MatchAnalysis | null | undefined): boolean {
  if (!analysis?.result) return false;
  return analysis.status === "completed" || hasScreenPreview(analysis);
}

export function isFullMatch(analysis: MatchAnalysis | null | undefined): boolean {
  return analysis?.status === "completed" && analysis.result?.depth !== "screen";
}

export function recommendationVariant(
  recommendation: MatchResult["recommendation"] | undefined,
): "success" | "warning" | "danger" | "default" {
  if (recommendation === "apply") return "success";
  if (recommendation === "maybe apply") return "warning";
  if (recommendation === "do not apply") return "danger";
  return "default";
}

export function pendingAnalysesCount(analyses: MatchAnalysis[], profileId: string): number {
  return analyses.filter((a) => a.profile_id === profileId && a.status === "pending").length;
}

export function jobsNeedingAnalysis(
  jobs: { id: string }[],
  analyses: MatchAnalysis[],
  profileId: string,
): number {
  return jobs.filter((job) => {
    const latest = latestAnalysisForJob(analyses, profileId, job.id);
    return !latest || latest.status === "failed";
  }).length;
}

export function recommendationLabel(recommendation: MatchResult["recommendation"] | undefined) {
  if (recommendation === "apply") return "Apply";
  if (recommendation === "maybe apply") return "Maybe";
  if (recommendation === "do not apply") return "Skip";
  return null;
}
