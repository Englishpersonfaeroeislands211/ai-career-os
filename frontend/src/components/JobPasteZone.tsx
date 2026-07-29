import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api/client";
import type { JobParseResult } from "../types";
import { AiLoadingState } from "./AiLoadingState";
import { Button, ErrorBanner, Textarea } from "./ui";

const MIN_CHARS = 100;

interface JobPasteZoneProps {
  onParsed: (result: JobParseResult) => void;
  initialText?: string;
}

export function JobPasteZone({ onParsed, initialText = "" }: JobPasteZoneProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [pasteText, setPasteText] = useState(initialText);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const charCount = pasteText.trim().length;
  const canExtract = charCount >= MIN_CHARS;

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  async function handleExtract() {
    if (!canExtract) {
      setError(`Paste at least ${MIN_CHARS} characters of the job description`);
      return;
    }
    setExtracting(true);
    setError(null);
    try {
      const result = await api.jobs.parseText(pasteText);
      onParsed(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to extract job fields");
    } finally {
      setExtracting(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && canExtract && !extracting) {
      e.preventDefault();
      void handleExtract();
    }
  }

  return (
    <div className="space-y-4">
      {error && <ErrorBanner message={error} />}

      <div
        className={`rounded-xl border-2 border-dashed transition ${
          extracting
            ? "border-accent/40 bg-accent/5"
            : "border-border bg-surface hover:border-accent/30"
        }`}
      >
        <div className="p-5 sm:p-6">
          {extracting ? (
            <div className="py-8">
              <AiLoadingState variant="job-extract" size="md" />
            </div>
          ) : (
            <>
              <Textarea
                ref={textareaRef}
                value={pasteText}
                onChange={(e) => setPasteText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Paste any job description with all details — title, company, requirements, responsibilities…"
                rows={16}
                className="min-h-[320px] border-0 bg-transparent p-0 shadow-none focus:ring-0"
              />
              <p className="mt-3 text-xs text-text-muted">
                Include every detail you have — the more complete the description, the better the
                match.{" "}
                <kbd className="rounded border border-border bg-surface-overlay px-1.5 py-0.5 font-mono text-[10px]">
                  ⌘ Enter
                </kbd>{" "}
                to extract.
              </p>
            </>
          )}
        </div>
      </div>

      {!extracting && (
        <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-text-muted">
            {charCount > 0
              ? `${charCount.toLocaleString()} characters${
                  canExtract ? " · ready" : ` · ${MIN_CHARS - charCount} more needed`
                }`
              : `At least ${MIN_CHARS} characters required`}
          </p>
          <Button onClick={handleExtract} disabled={!canExtract} className="sm:min-w-[180px]">
            Extract job details →
          </Button>
        </div>
      )}
    </div>
  );
}
