import { useNavigate } from "react-router-dom";
import { Layout } from "../components/Layout";
import { OnboardingSteps } from "../components/OnboardingSteps";
import { ResumeUploadZone } from "../components/ResumeUploadZone";
import { Button } from "../components/ui";

export function OnboardingPage() {
  const navigate = useNavigate();

  return (
    <Layout showSidebar={false}>
      <div className="mx-auto max-w-xl space-y-6 px-6 py-12">
        <OnboardingSteps current={2} />

        <div>
          <h2 className="text-2xl font-semibold">Upload your resume</h2>
          <p className="mt-2 text-text-muted">
            We&apos;ll extract and structure your resume with AI so you can review it before saving.
          </p>
        </div>

        <ResumeUploadZone
          onParsed={(parsed) => navigate("/onboarding/review", { state: { parsed } })}
        />

        <div className="flex justify-between">
          <Button variant="ghost" onClick={() => navigate("/onboarding/ai")}>
            Back
          </Button>
        </div>
      </div>
    </Layout>
  );
}
