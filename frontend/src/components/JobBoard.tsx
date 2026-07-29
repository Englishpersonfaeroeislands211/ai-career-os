import { Link } from "react-router-dom";
import type { Job, MatchAnalysis } from "../types";
import {
  hasMatchResult,
  latestAnalysisForJob,
  recommendationLabel,
  recommendationVariant,
  scoreFromResult,
} from "../lib/matches";
import { Badge, Button } from "./ui";
import { ScoreRing } from "./ScoreRing";

interface JobBoardProps {
  jobs: Job[];
  analyses: MatchAnalysis[];
  profileId: string;
}

export function JobBoard({ jobs, analyses, profileId }: JobBoardProps) {
  if (jobs.length === 0) {
    return (
      <div className="flex flex-col items-center rounded-xl border border-dashed border-border bg-surface-raised px-6 py-16 text-center">
        <p className="text-4xl">💼</p>
        <h3 className="mt-4 text-lg font-semibold">No jobs yet</h3>
        <p className="mt-2 max-w-sm text-sm text-text-muted">
          Paste any job description with all details — we&apos;ll extract fields and run explainable
          match analysis against your profile.
        </p>
        <Link to="/jobs/new" className="mt-6">
          <Button>Add your first job</Button>
        </Link>
      </div>
    );
  }

  const sorted = [...jobs].sort((a, b) => {
    const scoreA = scoreFromResult(latestAnalysisForJob(analyses, profileId, a.id)?.result) ?? -1;
    const scoreB = scoreFromResult(latestAnalysisForJob(analyses, profileId, b.id)?.result) ?? -1;
    return scoreB - scoreA;
  });

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-surface-raised">
      <div className="hidden grid-cols-[1fr_auto_auto_auto] gap-4 border-b border-border px-5 py-3 text-xs font-medium uppercase tracking-wide text-text-muted md:grid">
        <span>Role</span>
        <span className="text-center">Match</span>
        <span className="text-center">Verdict</span>
        <span />
      </div>
      <ul className="divide-y divide-border">
        {sorted.map((job) => {
          const analysis = latestAnalysisForJob(analyses, profileId, job.id);
          const score = hasMatchResult(analysis) ? scoreFromResult(analysis?.result) : null;
          const rec = hasMatchResult(analysis) ? analysis?.result?.recommendation : undefined;
          const recLabel = recommendationLabel(rec);
          const pendingFull =
            analysis?.status === "pending" && analysis.result?.depth !== "screen";

          return (
            <li key={job.id}>
              <Link
                to={`/jobs/${job.id}`}
                className="grid grid-cols-1 items-center gap-4 px-5 py-4 transition hover:bg-surface-overlay md:grid-cols-[1fr_auto_auto_auto]"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium">{job.title}</p>
                  <p className="truncate text-sm text-text-muted">
                    {job.company}
                    {job.location ? ` · ${job.location}` : ""}
                  </p>
                </div>
                <div className="flex md:justify-center">
                  {pendingFull ? (
                    <Badge variant="info">
                      <span className="inline-flex items-center gap-1.5">
                        <span className="size-1.5 animate-pulse rounded-full bg-accent" />
                        Full analysis…
                      </span>
                    </Badge>
                  ) : analysis?.status === "failed" ? (
                    <Badge variant="danger">Failed</Badge>
                  ) : (
                    <ScoreRing score={score} size="sm" label="" />
                  )}
                </div>
                <div className="flex md:justify-center">
                  {recLabel ? (
                    <Badge variant={recommendationVariant(rec)}>{recLabel}</Badge>
                  ) : (
                    <span className="text-sm text-text-muted">Not analyzed</span>
                  )}
                </div>
                <div className="hidden md:flex md:justify-end">
                  <span className="text-sm text-accent">View →</span>
                </div>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
