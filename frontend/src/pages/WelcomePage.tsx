import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api } from "../api/client";
import { AiLoadingState } from "../components/AiLoadingState";
import { Layout } from "../components/Layout";
import { LogoMark } from "../components/Logo";
import { Button } from "../components/ui";

export function WelcomePage() {
  const [hasProfiles, setHasProfiles] = useState<boolean | null>(null);

  useEffect(() => {
    api.profiles
      .list()
      .then((profiles) => setHasProfiles(profiles.length > 0))
      .catch(() => setHasProfiles(false));
  }, []);

  if (hasProfiles === true) {
    return <Navigate to="/" replace />;
  }

  if (hasProfiles === null) {
    return (
      <Layout showSidebar={false}>
        <div className="flex min-h-screen items-center justify-center p-6">
          <div className="w-full max-w-md">
            <AiLoadingState variant="page" size="lg" />
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout showSidebar={false}>
      <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center px-6 py-24 text-center">
        <LogoMark className="mb-8 size-16" />
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Understand why a job fits
        </h2>
        <p className="mt-4 text-lg text-text-muted">
          Evidence-based career matching — not auto-apply. Upload your resume, add jobs manually,
          and get explainable match scores with strengths, gaps, and evidence.
        </p>
        <div className="mt-10">
          <Link to="/onboarding/ai">
            <Button className="min-w-44 px-8 py-3 text-base">Get started</Button>
          </Link>
        </div>
        <p className="mt-12 text-sm text-text-muted">
          Connect your AI provider, upload your resume as a PDF, and review before matching.
        </p>
      </main>
    </Layout>
  );
}
