import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { LLMProvider, LocalPreset, SettingsUpdate } from "../types/settings";
import {
  CLOUD_PROVIDERS,
  inferLocalPreset,
  LOCAL_PRESETS,
  normalizeProvider,
  PROVIDER_REGISTRY,
} from "../types/settings";
import { Button, Field, Input, Select } from "./ui";

interface ProviderFormProps {
  initialProvider?: LLMProvider;
  initialModel?: string;
  initialBaseUrl?: string;
  apiKeySet?: boolean;
  submitLabel?: string;
  loading?: boolean;
  onSubmit: (data: SettingsUpdate) => Promise<void>;
}

function ProviderGrid({
  providers,
  selected,
  onSelect,
}: {
  providers: LLMProvider[];
  selected: LLMProvider;
  onSelect: (p: LLMProvider) => void;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {providers.map((key) => {
        const item = PROVIDER_REGISTRY[key];
        const isSelected = selected === key;
        return (
          <button
            key={key}
            type="button"
            onClick={() => onSelect(key)}
            className={`rounded-xl border p-4 text-left transition ${
              isSelected
                ? "border-accent bg-accent/10 ring-1 ring-accent"
                : "border-border bg-surface-raised hover:border-accent/40"
            }`}
          >
            <p className="font-medium">{item.label}</p>
            <p className="mt-1 text-xs text-text-muted">{item.description}</p>
          </button>
        );
      })}
    </div>
  );
}

export function ProviderForm({
  initialProvider = "openai",
  initialModel,
  initialBaseUrl,
  apiKeySet = false,
  submitLabel = "Continue",
  loading,
  onSubmit,
}: ProviderFormProps) {
  const normalizedInitial = normalizeProvider(initialProvider) ?? "openai";
  const [provider, setProvider] = useState<LLMProvider>(normalizedInitial);
  const [localPreset, setLocalPreset] = useState<LocalPreset>(() =>
    inferLocalPreset(initialBaseUrl),
  );
  const [model, setModel] = useState(
    initialModel ?? PROVIDER_REGISTRY[normalizedInitial].defaultModel,
  );
  const [baseUrl, setBaseUrl] = useState(
    initialBaseUrl ?? PROVIDER_REGISTRY[normalizedInitial].defaultBaseUrl ?? "",
  );
  const [apiKey, setApiKey] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<string[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);

  const meta = PROVIDER_REGISTRY[provider];
  const isLocal = provider === "local";

  const selectProvider = useCallback((next: LLMProvider) => {
    const nextMeta = PROVIDER_REGISTRY[next];
    setProvider(next);
    setModels([]);
    setModelsError(null);

    if (next === "local") {
      const preset = LOCAL_PRESETS.lmstudio;
      setLocalPreset("lmstudio");
      setModel(preset.defaultModel);
      setBaseUrl(preset.defaultBaseUrl);
      return;
    }

    setModel(nextMeta.defaultModel);
    setBaseUrl(nextMeta.defaultBaseUrl ?? "");
  }, []);

  function applyLocalPreset(preset: LocalPreset) {
    setLocalPreset(preset);
    const defaults = LOCAL_PRESETS[preset];
    setModel(defaults.defaultModel);
    setBaseUrl(defaults.defaultBaseUrl);
    setModels([]);
    setModelsError(null);
  }

  const canFetchModels =
    provider === "local"
      ? !!baseUrl.trim()
      : meta.requiresApiKey
        ? !!apiKey.trim() || apiKeySet
        : true;

  useEffect(() => {
    if (!canFetchModels) {
      setModels([]);
      setModelsLoading(false);
      setModelsError(null);
      return;
    }

    let cancelled = false;
    const timer = setTimeout(async () => {
      setModelsLoading(true);
      setModelsError(null);

      try {
        const result = await api.llm.listModels({
          llm_provider: provider,
          llm_base_url: meta.showBaseUrl ? baseUrl.trim() || undefined : undefined,
          llm_api_key: apiKey.trim() || undefined,
          use_saved_credentials: apiKeySet && !apiKey.trim(),
        });

        if (cancelled) return;

        setModels(result.models);
        setModel((current) => {
          if (result.models.includes(current)) return current;
          return result.models[0] ?? current;
        });
      } catch (err) {
        if (cancelled) return;
        setModels([]);
        setModelsError(err instanceof Error ? err.message : "Failed to load models");
      } finally {
        if (!cancelled) setModelsLoading(false);
      }
    }, 400);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [provider, baseUrl, apiKey, apiKeySet, meta.showBaseUrl, meta.requiresApiKey, canFetchModels]);

  const modelOptions =
    model && models.length > 0 && !models.includes(model) ? [model, ...models] : models;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const payload: SettingsUpdate = {
      llm_provider: provider,
      llm_model: model.trim() || meta.defaultModel,
    };

    if (meta.showBaseUrl) {
      payload.llm_base_url = baseUrl.trim() || meta.defaultBaseUrl || undefined;
    }

    if (provider === "azure_openai" && !payload.llm_base_url) {
      setError("Azure OpenAI requires your deployment base URL.");
      return;
    }

    if (isLocal && !payload.llm_base_url) {
      setError("Local provider requires a base URL.");
      return;
    }

    if (meta.requiresApiKey) {
      if (apiKey.trim()) {
        payload.llm_api_key = apiKey.trim();
      } else if (!apiKeySet) {
        setError(
          "API key is required for this provider (or set via environment variable on the server).",
        );
        return;
      }
    }

    try {
      await onSubmit(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <section className="space-y-3">
        <h3 className="text-sm font-medium uppercase tracking-wide text-text-muted">Local</h3>
        <ProviderGrid providers={["local"]} selected={provider} onSelect={selectProvider} />
      </section>

      <section className="space-y-3">
        <h3 className="text-sm font-medium uppercase tracking-wide text-text-muted">Cloud</h3>
        <ProviderGrid providers={CLOUD_PROVIDERS} selected={provider} onSelect={selectProvider} />
      </section>

      {isLocal && (
        <Field label="Local server preset" hint="Fills default URL and model — you can still edit below">
          <div className="flex flex-wrap gap-2">
            {(Object.keys(LOCAL_PRESETS) as LocalPreset[]).map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => applyLocalPreset(key)}
                className={`rounded-lg border px-3 py-1.5 text-sm transition ${
                  localPreset === key
                    ? "border-accent bg-accent/10 text-accent"
                    : "border-border bg-surface-raised text-text-muted hover:border-accent/40"
                }`}
              >
                {LOCAL_PRESETS[key].label}
              </button>
            ))}
          </div>
        </Field>
      )}

      {meta.showBaseUrl && (
        <Field
          label={provider === "azure_openai" ? "Azure deployment URL" : "Base URL"}
          hint={
            isLocal && localPreset === "lmstudio"
              ? "Enable the OpenAI-compatible server in LM Studio settings"
              : isLocal && localPreset === "ollama"
                ? "Ollama OpenAI-compatible endpoint (/v1)"
                : provider === "azure_openai"
                  ? "e.g. https://<resource>.openai.azure.com/openai/v1"
                  : undefined
          }
        >
          <Input
            value={baseUrl}
            onChange={(e) => {
              setBaseUrl(e.target.value);
              if (isLocal) setLocalPreset(inferLocalPreset(e.target.value));
            }}
            placeholder={meta.defaultBaseUrl ?? "https://..."}
          />
        </Field>
      )}

      {meta.requiresApiKey && (
        <Field
          label="API key"
          hint={
            apiKeySet
              ? "Leave blank to keep your existing key"
              : "Stored on the server only — never sent back to the browser"
          }
        >
          <Input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={apiKeySet ? "••••••••••••" : "sk-..."}
            autoComplete="off"
          />
        </Field>
      )}

      <Field
        label="Model"
        hint={
          modelsLoading
            ? "Loading models from provider…"
            : modelsError
              ? `Could not load models — enter manually. ${modelsError}`
              : modelOptions.length > 0
                ? `${modelOptions.length} model${modelOptions.length === 1 ? "" : "s"} available`
                : canFetchModels
                  ? "Enter a model ID if the list could not be loaded"
                  : meta.requiresApiKey && !apiKeySet
                    ? "Add an API key to load available models"
                    : isLocal
                      ? "Set a base URL to load available models"
                      : `Default for ${meta.label}: ${meta.defaultModel}`
        }
      >
        {modelOptions.length > 0 ? (
          <Select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            disabled={modelsLoading}
          >
            {modelOptions.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </Select>
        ) : (
          <Input
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder={meta.defaultModel}
            disabled={modelsLoading}
          />
        )}
      </Field>

      {error && (
        <p className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </p>
      )}

      <Button type="submit" loading={loading} className="w-full sm:w-auto px-8">
        {submitLabel}
      </Button>
    </form>
  );
}
