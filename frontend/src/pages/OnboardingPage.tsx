import { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { Layout } from "../components/Layout";
import { OnboardingSteps } from "../components/OnboardingSteps";
import { Button, ErrorBanner } from "../components/ui";

export function OnboardingPage() {
  const navigate = useNavigate();
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
        navigate("/onboarding/review", { state: { parsed } });
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to parse resume");
      } finally {
        setUploading(false);
      }
    },
    [navigate],
  );

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  return (
    <Layout subtitle="Upload your resume">
      <main className="mx-auto max-w-xl space-y-6 px-6 py-12">
        <OnboardingSteps current={2} />

        <div>
          <h2 className="text-2xl font-semibold">Upload your resume</h2>
          <p className="mt-2 text-text-muted">
            We&apos;ll extract and structure your resume with AI so you can review it before saving.
          </p>
        </div>

        {error && <ErrorBanner message={error} />}

        <div
          role="button"
          tabIndex={0}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-16 transition ${
            dragging
              ? "border-accent bg-accent/5"
              : "border-border bg-surface-raised hover:border-accent/50"
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
              <p className="mt-4 text-sm text-text-muted">Extracting and structuring resume…</p>
            </>
          ) : (
            <>
              <p className="text-4xl">📄</p>
              <p className="mt-4 font-medium">Drop your resume PDF here</p>
              <p className="mt-1 text-sm text-text-muted">or click to browse · max 10 MB</p>
            </>
          )}
        </div>

        <div className="flex justify-between">
          <Button variant="ghost" onClick={() => navigate("/onboarding/ai")}>
            Back
          </Button>
        </div>
      </main>
    </Layout>
  );
}
