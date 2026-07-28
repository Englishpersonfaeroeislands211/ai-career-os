import type { Job, JobExtraction } from "../types";

const MIN_EXTRACT_CHARS = 100;

export function extractionMetadata(
  extraction: JobExtraction,
  jobText?: string,
): Record<string, unknown> {
  return {
    employment_type: extraction.employment_type ?? null,
    salary_range: extraction.salary_range ?? null,
    requirements: extraction.requirements,
    work_mode: extraction.work_mode ?? null,
    match_summary: extraction.match_summary,
    ...(jobText ? { job_text: jobText } : {}),
  };
}

export function buildJobExtractSource(job: Pick<Job, "title" | "company" | "location" | "description" | "raw_metadata">): string {
  const stored = job.raw_metadata?.job_text;
  if (typeof stored === "string" && stored.trim().length >= MIN_EXTRACT_CHARS) {
    return stored.trim();
  }

  const header = [job.title, [job.company, job.location].filter(Boolean).join(" · ")].filter(Boolean).join("\n");
  return [header, "", job.description].join("\n").trim();
}

export function canExtractFromText(text: string): boolean {
  return text.trim().length >= MIN_EXTRACT_CHARS;
}
