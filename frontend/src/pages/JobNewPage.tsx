import { useNavigate } from "react-router-dom";
import { JobPanel } from "../components/JobPanel";
import { Layout } from "../components/Layout";
import { Button } from "../components/ui";

export function JobNewPage() {
  const navigate = useNavigate();

  return (
    <Layout subtitle="Add opportunity">
      <main className="mx-auto max-w-3xl space-y-6 px-6 py-8">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Add a job</h2>
            <p className="mt-1 text-sm text-text-muted">
              Paste a listing — AI extracts the fields for you to review.
            </p>
          </div>
          <Button variant="ghost" onClick={() => navigate("/")}>
            ← Back
          </Button>
        </div>
        <JobPanel
          selectedId={null}
          onSelect={() => {}}
          onSaved={(job) => navigate(`/jobs/${job.id}`, { replace: true })}
        />
      </main>
    </Layout>
  );
}
