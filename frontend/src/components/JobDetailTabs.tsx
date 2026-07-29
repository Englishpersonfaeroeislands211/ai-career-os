import { useEffect, useRef, useState } from "react";
import type { CompanyBrief, Job, MatchAnalysis } from "../types";
import { isFullMatch } from "../lib/matches";
import { CompanyResearchPanel } from "./CompanyResearchPanel";
import { CoverLetterPanel } from "./CoverLetterPanel";
import { MatchResultPanel } from "./MatchResultPanel";
import { MatchAnalysisProgress } from "./MatchAnalysisProgress";
import { ResumeOptimizationPanel } from "./ResumeOptimizationPanel";

export type JobDetailTab = "match" | "company" | "resume" | "cover";

interface JobDetailTabsProps {
  job: Job;
  analysis: MatchAnalysis | null;
  profileName: string;
  showProgress?: boolean;
  onJobUpdated: (job: Job) => void;
  onReAnalyze: () => void;
  profileId: string;
}

const TABS: { id: JobDetailTab; label: string; shortLabel: string; description: string }[] = [
  {
    id: "match",
    label: "Match analysis",
    shortLabel: "Match",
    description: "Explainable fit score, strengths, and gaps",
  },
  {
    id: "company",
    label: "Company research",
    shortLabel: "Research",
    description: "Culture, news, and interview signals from the web",
  },
  {
    id: "resume",
    label: "Resume improvements",
    shortLabel: "Resume",
    description: "AI suggestions tailored to this job's gaps",
  },
  {
    id: "cover",
    label: "Cover letter",
    shortLabel: "Cover letter",
    description: "Short, targeted draft you can copy and edit",
  },
];

function tabUnlocked(tab: JobDetailTab, analysis: MatchAnalysis | null): boolean {
  if (tab === "match") return !!analysis;
  return isFullMatch(analysis);
}

export function JobDetailTabs({
  job,
  analysis,
  profileName,
  showProgress = false,
  onJobUpdated,
  onReAnalyze,
  profileId,
}: JobDetailTabsProps) {
  const tabsRef = useRef<HTMLDivElement>(null);
  const prevStatusRef = useRef(analysis?.status);
  const [activeTab, setActiveTab] = useState<JobDetailTab>("match");
  const [actionsReady, setActionsReady] = useState(false);

  const analysisComplete = isFullMatch(analysis);
  const visibleTabs = analysisComplete ? TABS : TABS.filter((tab) => tab.id === "match");

  useEffect(() => {
    if (!analysisComplete) {
      setActiveTab("match");
    }
  }, [analysisComplete]);

  useEffect(() => {
    const wasPending = prevStatusRef.current === "pending";
    const nowComplete = analysis?.status === "completed";
    if (wasPending && nowComplete) {
      setActionsReady(true);
      setActiveTab("match");
      window.setTimeout(() => setActionsReady(false), 6000);
    }
    prevStatusRef.current = analysis?.status;
  }, [analysis?.status]);

  function handleTabClick(tab: JobDetailTab) {
    if (!tabUnlocked(tab, analysis)) return;
    setActiveTab(tab);
  }

  return (
    <div ref={tabsRef} id="job-tools" className="scroll-mt-4 space-y-4">
      {showProgress && <MatchAnalysisProgress analysis={analysis} showUnlocks={analysisComplete} />}

      {analysisComplete && (
        <div className="sticky top-0 z-10 -mx-4 border-b border-border bg-surface/95 px-4 lg:-mx-8 lg:px-8">
          <div
            className="flex gap-x-3 overflow-x-auto sm:gap-x-6 lg:gap-x-8 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
            role="tablist"
            aria-label="Job tools"
          >
            {visibleTabs.map((tab) => {
              const active = activeTab === tab.id;
              const isActionTab = tab.id !== "match";
              const highlight = actionsReady && isActionTab;

              return (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => handleTabClick(tab.id)}
                  className={`group relative shrink-0 border-b-2 px-2.5 py-2.5 transition sm:px-3 ${
                    active
                      ? "border-accent text-text"
                      : "border-transparent text-text-muted hover:border-border hover:text-text"
                  } ${highlight ? "ring-1 ring-accent/40 ring-offset-2 ring-offset-surface rounded-t-md" : ""}`}
                >
                  <span className="inline-flex items-center gap-1.5 whitespace-nowrap text-[13px] font-medium sm:text-sm">
                    {tab.shortLabel}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {!analysisComplete && analysis?.status === "pending" && (
        <p className="text-sm text-text-muted">
          Match analysis running — company research, resume improvements, and cover letter unlock
          when full analysis completes.
        </p>
      )}

      <div role="tabpanel" className="min-h-[200px]">
        {activeTab === "match" && (
          <div className="space-y-3">
            {analysisComplete && (
              <div className="hidden lg:block">
                <h3 className="text-lg font-semibold">{TABS[0].label}</h3>
                <p className="text-sm text-text-muted">{TABS[0].description}</p>
              </div>
            )}
            <MatchResultPanel
              analysis={analysis}
              profileName={profileName}
              jobTitle={`${job.title} @ ${job.company}`}
            />
          </div>
        )}

        {activeTab === "company" && (
          <div className="space-y-3">
            <div>
              <h3 className="text-lg font-semibold">{TABS[1].label}</h3>
              <p className="text-sm text-text-muted">{TABS[1].description}</p>
            </div>
            <CompanyResearchPanel
              job={job}
              onUpdated={(brief: CompanyBrief) => onJobUpdated({ ...job, company_brief: brief })}
            />
          </div>
        )}

        {activeTab === "resume" && analysis && (
          <div className="space-y-3">
            <div>
              <h3 className="text-lg font-semibold">{TABS[2].label}</h3>
              <p className="text-sm text-text-muted">{TABS[2].description}</p>
            </div>
            <ResumeOptimizationPanel
              analysis={analysis}
              profileId={profileId}
              onApplied={() => {}}
              onReAnalyze={onReAnalyze}
            />
          </div>
        )}

        {activeTab === "cover" && analysis && (
          <div className="space-y-3">
            <div>
              <h3 className="text-lg font-semibold">{TABS[3].label}</h3>
              <p className="text-sm text-text-muted">{TABS[3].description}</p>
            </div>
            <CoverLetterPanel analysis={analysis} />
          </div>
        )}
      </div>
    </div>
  );
}
