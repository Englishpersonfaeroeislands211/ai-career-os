import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { Button } from "../components/ui";
import { Layout } from "../components/Layout";

export function WelcomePage() {
  const [hasProfiles, setHasProfiles] = useState(false);

  useEffect(() => {
    api.profiles.list().then((profiles) => setHasProfiles(profiles.length > 0)).catch(console.error);
  }, []);

  return (
    <Layout subtitle="Your intelligent career assistant">
      <main className="mx-auto flex max-w-2xl flex-col items-center px-6 py-24 text-center">
        <div className="mb-8 inline-flex size-16 items-center justify-center rounded-2xl bg-accent/15 text-2xl">
          ◈
        </div>
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Understand why a job fits
        </h2>
        <p className="mt-4 text-lg text-text-muted">
          Evidence-based career matching — not auto-apply. Upload your resume, add a job
          description, and get an explainable match analysis.
        </p>
        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <Link to="/onboarding/ai">
            <Button className="min-w-40 px-8 py-3 text-base">Get started</Button>
          </Link>
          {hasProfiles && (
            <Link to="/dashboard">
              <Button variant="secondary" className="min-w-40 px-8 py-3 text-base">
                Go to dashboard
              </Button>
            </Link>
          )}
        </div>
        <p className="mt-12 text-sm text-text-muted">
          Connect your AI provider, upload your resume as a PDF, and review before matching.
        </p>
      </main>
    </Layout>
  );
}
