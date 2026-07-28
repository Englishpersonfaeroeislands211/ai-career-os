import { useNavigate } from "react-router-dom";
import { JobPanel } from "../components/JobPanel";
import { Layout } from "../components/Layout";
import { useActiveProfile } from "../hooks/useActiveProfile";
import { Button } from "../components/ui";

export function JobNewPage() {
  const navigate = useNavigate();
  const { profile, loading, requireProfile } = useActiveProfile();

  if (!loading && !profile) {
    requireProfile();
  }

  if (loading || !profile) {
    return (
      <Layout subtitle="Add opportunity">
        <main className="flex min-h-[50vh] items-center justify-center">
          <span className="size-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        </main>
      </Layout>
    );
  }

  return (
    <Layout subtitle="Add opportunity">
      <main className="mx-auto max-w-3xl space-y-6 px-6 py-8">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Add a job</h2>
            <p className="mt-1 text-sm text-text-muted">
              Paste a listing — we extract fields and analyze the match against your profile.
            </p>
          </div>
          <Button variant="ghost" onClick={() => navigate("/")}>
            ← Back
          </Button>
        </div>
        <JobPanel
          selectedId={null}
          profileId={profile.id}
          onSelect={() => {}}
          onSaved={(job) => navigate(`/jobs/${job.id}`, { replace: true })}
        />
      </main>
    </Layout>
  );
}
