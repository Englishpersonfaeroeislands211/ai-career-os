import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { Layout } from "../components/Layout";
import { ProviderForm } from "../components/ProviderForm";
import { Badge, Button } from "../components/ui";
import type { LLMProvider } from "../types/settings";
import { normalizeProvider, PROVIDER_REGISTRY } from "../types/settings";

export function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [initialProvider, setInitialProvider] = useState<LLMProvider>("openai");
  const [initialModel, setInitialModel] = useState<string>();
  const [initialBaseUrl, setInitialBaseUrl] = useState<string>();
  const [apiKeySet, setApiKeySet] = useState(false);
  const [configured, setConfigured] = useState(false);

  useEffect(() => {
    api.settings
      .get()
      .then((s) => {
        const provider = normalizeProvider(s.llm_provider) ?? "openai";
        setInitialProvider(provider);
        if (s.llm_model) setInitialModel(s.llm_model);
        if (s.llm_base_url) setInitialBaseUrl(s.llm_base_url);
        setApiKeySet(s.api_key_set);
        setConfigured(s.configured);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout subtitle="Settings">
      <main className="mx-auto max-w-2xl space-y-8 px-6 py-12">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold">AI provider</h2>
            <p className="mt-2 text-text-muted">
              Update your LLM provider and credentials. Keys are stored on the server only.
            </p>
          </div>
          <Badge variant={configured ? "success" : "warning"}>
            {configured ? "Connected" : "Not configured"}
          </Badge>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <span className="size-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          </div>
        ) : (
          <>
            {saved && (
              <p className="rounded-lg border border-success/30 bg-success/10 px-4 py-3 text-sm text-success">
                Settings saved.
              </p>
            )}
            <ProviderForm
              initialProvider={initialProvider}
              initialModel={initialModel}
              initialBaseUrl={initialBaseUrl}
              apiKeySet={apiKeySet}
              loading={saving}
              submitLabel="Save settings"
              onSubmit={async (data) => {
                setSaving(true);
                setSaved(false);
                try {
                  const updated = await api.settings.update(data);
                  setApiKeySet(updated.api_key_set);
                  setConfigured(updated.configured);
                  setSaved(true);
                } finally {
                  setSaving(false);
                }
              }}
            />
          </>
        )}

        <p className="text-xs text-text-muted">
          Current provider: {PROVIDER_REGISTRY[initialProvider].label}
          {initialModel ? ` · ${initialModel}` : ""}
        </p>

        <Link to="/dashboard">
          <Button variant="ghost">← Back to dashboard</Button>
        </Link>
      </main>
    </Layout>
  );
}
