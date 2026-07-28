import { useCallback, useRef, useState } from "react";
import { api, ApiError } from "../api/client";
import type { ResumeParseResult } from "../types";
import { Button, ErrorBanner } from "./ui";

interface ResumeUploadZoneProps {
  onParsed: (result: ResumeParseResult) => void;
  compact?: boolean;
}

export function ResumeUploadZone({ onParsed, compact = false }: ResumeUploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (file.type !== "application/pdf") {
        setError("Please upload a PDF file.");
        return;
      }

      setUploading(true);
      setError(null);
      try {
        const parsed = await api.profiles.parseResume(file);
        onParsed(parsed);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to parse resume");
      } finally {
        setUploading(false);
      }
    },
    [onParsed],
  );

  return (
    <div className="space-y-3">
      {error && <ErrorBanner message={error} />}
      <div
        role="button"
        tabIndex={0}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const file = e.dataTransfer.files[0];
          if (file) handleFile(file);
        }}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed transition ${
          compact ? "px-4 py-8" : "px-6 py-14"
        } ${
          dragging
            ? "border-accent bg-accent/5"
            : "border-border bg-surface hover:border-accent/40"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
        {uploading ? (
          <>
            <span className="size-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            <p className="mt-3 text-sm text-text-muted">Extracting resume with AI…</p>
          </>
        ) : (
          <>
            <p className={compact ? "text-2xl" : "text-4xl"}>📄</p>
            <p className="mt-3 font-medium">Drop PDF resume here</p>
            <p className="mt-1 text-sm text-text-muted">or click to browse</p>
          </>
        )}
      </div>
      {!compact && (
        <p className="text-center text-xs text-text-muted">
          We extract structured fields locally via your configured LLM — review before saving.
        </p>
      )}
    </div>
  );
}

export function ResumeUploadButton({
  onParsed,
  label = "Upload new resume",
}: {
  onParsed: (result: ResumeParseResult) => void;
  label?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    if (file.type !== "application/pdf") {
      setError("Please upload a PDF file.");
      return;
    }
    setUploading(true);
    setError(null);
    try {
      onParsed(await api.profiles.parseResume(file));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to parse resume");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      {error && <p className="mb-2 text-sm text-danger">{error}</p>}
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      <Button
        variant="secondary"
        loading={uploading}
        onClick={() => inputRef.current?.click()}
      >
        {label}
      </Button>
    </div>
  );
}
