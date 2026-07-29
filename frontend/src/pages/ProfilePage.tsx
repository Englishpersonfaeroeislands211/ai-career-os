import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { ResumeParseResult } from "../types";
import { Layout } from "../components/Layout";
import { PageLoader } from "../components/AiLoadingState";
import { parseStructuredData, StructuredProfileView } from "../components/StructuredProfileView";
import { ResumeUploadZone } from "../components/ResumeUploadZone";
import { useActiveProfile } from "../hooks/useActiveProfile";
import { api } from "../api/client";
import { Button, ErrorBanner } from "../components/ui";

export function ProfilePage() {
  const navigate = useNavigate();
  const { profile, loading, requireProfile } = useActiveProfile();
  const [showUpload, setShowUpload] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !profile) requireProfile();
  }, [loading, profile, requireProfile]);

  function handleParsed(parsed: ResumeParseResult) {
    if (!profile) return;
    navigate("/onboarding/review", {
      state: {
        parsed,
        profileId: profile.id,
        mode: "update",
        returnTo: "/profile",
      },
    });
  }

  async function handleDownloadPdf() {
    if (!profile) return;
    setDownloading(true);
    setDownloadError(null);
    try {
      await api.profiles.downloadResumePdf(profile.id);
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : "Failed to download resume PDF");
    } finally {
      setDownloading(false);
    }
  }

  if (loading || !profile) {
    return (
      <Layout title="Profile" subtitle="Your career data">
        <PageLoader variant="page" />
      </Layout>
    );
  }

  const structured = parseStructuredData(profile.structured_data);

  return (
    <Layout title="Profile" subtitle={profile.name}>
      <div className="space-y-8">
        {downloadError && <ErrorBanner message={downloadError} />}

        <section className="rounded-2xl border border-border bg-surface-raised p-6 sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                Primary profile
              </p>
              <h2 className="mt-1 text-2xl font-bold">{profile.name}</h2>
              {profile.headline && <p className="mt-2 text-text-muted">{profile.headline}</p>}
              <p className="mt-3 text-xs text-text-muted">
                Updated {new Date(profile.updated_at).toLocaleDateString()}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" onClick={handleDownloadPdf} loading={downloading}>
                Download PDF
              </Button>
              <Button variant="secondary" onClick={() => setShowUpload((v) => !v)}>
                {showUpload ? "Cancel upload" : "Upload new resume"}
              </Button>
            </div>
          </div>
        </section>

        {showUpload && (
          <section className="rounded-xl border border-accent/30 bg-accent/5 p-6">
            <h3 className="mb-4 font-semibold">Replace resume</h3>
            <p className="mb-4 text-sm text-text-muted">
              Upload a new PDF — we&apos;ll re-extract structured fields for you to review before
              updating.
            </p>
            <ResumeUploadZone onParsed={handleParsed} compact />
          </section>
        )}

        {structured ? (
          <section className="rounded-xl border border-border bg-surface-raised p-6">
            <StructuredProfileView data={structured} />
          </section>
        ) : (
          <section className="rounded-xl border border-dashed border-border bg-surface-raised p-8 text-center">
            <p className="text-text-muted">
              No structured resume data yet. Upload a PDF to extract skills, experience, and
              education.
            </p>
            <Button className="mt-4" onClick={() => setShowUpload(true)}>
              Upload resume
            </Button>
          </section>
        )}

        <details className="rounded-xl border border-border bg-surface-raised">
          <summary className="cursor-pointer px-5 py-4 text-sm font-medium text-text-muted">
            Raw resume text
          </summary>
          <pre className="max-h-96 overflow-auto border-t border-border px-5 py-4 text-xs whitespace-pre-wrap text-text-muted">
            {profile.resume_text}
          </pre>
        </details>
      </div>
    </Layout>
  );
}
