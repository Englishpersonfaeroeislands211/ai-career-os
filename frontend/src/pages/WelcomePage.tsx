import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api } from "../api/client";
import { Layout } from "../components/Layout";
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
      <Layout showNav={false} subtitle="Your intelligent career assistant">
        <main className="flex min-h-[50vh] items-center justify-center">
          <span className="size-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        </main>
      </Layout>
    );
  }

  return (
    <Layout showNav={false} subtitle="Your intelligent career assistant">
      <main className="mx-auto flex max-w-2xl flex-col items-center px-6 py-24 text-center">
        <div className="mb-8 inline-flex size-16 items-center justify-center rounded-2xl bg-accent/15 text-2xl">
          ◈
        </div>
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
