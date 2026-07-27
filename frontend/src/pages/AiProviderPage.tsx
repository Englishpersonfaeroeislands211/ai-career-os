import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { LLMProvider } from "../types/settings";
import { normalizeProvider } from "../types/settings";
import { Layout } from "../components/Layout";
import { OnboardingSteps } from "../components/OnboardingSteps";
import { ProviderForm } from "../components/ProviderForm";
import { Button } from "../components/ui";

export function AiProviderPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [initialProvider, setInitialProvider] = useState<LLMProvider>("openai");
  const [initialModel, setInitialModel] = useState<string>();
  const [initialBaseUrl, setInitialBaseUrl] = useState<string>();
  const [apiKeySet, setApiKeySet] = useState(false);

  useEffect(() => {
    api.settings
      .get()
      .then((s) => {
        const provider = normalizeProvider(s.llm_provider) ?? "openai";
        setInitialProvider(provider);
        if (s.llm_model) setInitialModel(s.llm_model);
        if (s.llm_base_url) setInitialBaseUrl(s.llm_base_url);
        setApiKeySet(s.api_key_set);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout subtitle="Connect your AI provider">
      <main className="mx-auto max-w-2xl space-y-8 px-6 py-12">
        <OnboardingSteps current={1} />

        <div>
          <h2 className="text-2xl font-semibold">Choose your AI provider</h2>
          <p className="mt-2 text-text-muted">
            Bring your own API key. We use structured LLM outputs for resume parsing and job
            matching — provider-agnostic by design.
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <span className="size-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          </div>
        ) : (
          <ProviderForm
            initialProvider={initialProvider}
            initialModel={initialModel}
            initialBaseUrl={initialBaseUrl}
            apiKeySet={apiKeySet}
            loading={saving}
            submitLabel="Continue to upload"
            onSubmit={async (data) => {
              setSaving(true);
              try {
                await api.settings.update(data);
                navigate("/onboarding/upload");
              } finally {
                setSaving(false);
              }
            }}
          />
        )}

        <div className="flex justify-between border-t border-border pt-6">
          <Button variant="ghost" onClick={() => navigate("/")}>
            Back
          </Button>
        </div>
      </main>
    </Layout>
  );
}
