import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Job, JobExtraction } from "../types";
import {
  buildJobExtractSource,
  canExtractFromText,
  extractionMetadata,
} from "../lib/jobExtraction";
import { Button, Card, ErrorBanner, Field, Input, Textarea } from "./ui";

interface JobPanelProps {
  selectedId: string | null;
  profileId: string | null;
  onSelect: (job: Job) => void;
  onSaved: (job: Job) => void;
}

export function JobPanel({ selectedId, profileId, onSelect, onSaved }: JobPanelProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [pasteText, setPasteText] = useState("");
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [url, setUrl] = useState("");
  const [jobMetadata, setJobMetadata] = useState<Record<string, unknown> | null>(null);
  const [saving, setSaving] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.jobs.list().then(setJobs).catch(console.error);
  }, []);

  useEffect(() => {
    const job = jobs.find((j) => j.id === selectedId);
    if (job) {
      setTitle(job.title);
      setCompany(job.company);
      setLocation(job.location ?? "");
      setDescription(job.description);
      setUrl(job.url ?? "");
      setJobMetadata(job.raw_metadata);
      setPasteText("");
    }
  }, [selectedId, jobs]);

  function applyExtraction(extraction: JobExtraction, jobText?: string) {
    setTitle(extraction.title);
    setCompany(extraction.company);
    setLocation(extraction.location ?? "");
    setDescription(extraction.description);
    setJobMetadata((prev) => ({
      ...(prev ?? {}),
      ...extractionMetadata(extraction, jobText),
    }));
    onSelect({
      id: "",
      title: extraction.title,
      company: extraction.company,
      description: extraction.description,
      location: extraction.location ?? null,
      url: url.trim() || null,
      source: null,
      raw_metadata: extractionMetadata(extraction, jobText),
      created_at: "",
      updated_at: "",
    });
  }

  async function handleExtract() {
    if (pasteText.trim().length < 100) {
      setError("Paste at least 100 characters of the job posting");
      return;
    }
    setExtracting(true);
    setError(null);
    try {
      const result = await api.jobs.parseText(pasteText);
      applyExtraction(result.structured_data, result.job_text);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to extract job fields");
    } finally {
      setExtracting(false);
    }
  }

  async function handleReExtract() {
    const selectedJob = selectedId ? jobs.find((j) => j.id === selectedId) : null;
    const sourceText =
      pasteText.trim().length >= 100
        ? pasteText
        : selectedJob
          ? buildJobExtractSource(selectedJob)
          : buildJobExtractSource({
              title,
              company,
              location: location || null,
              description,
              raw_metadata: jobMetadata,
            });

    if (!canExtractFromText(sourceText)) {
      setError("Need at least 100 characters to re-extract — paste the full posting or add a longer description");
      return;
    }

    setExtracting(true);
    setError(null);
    try {
      const result = await api.jobs.parseText(sourceText);
      applyExtraction(result.structured_data, result.job_text);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to re-extract job fields");
    } finally {
      setExtracting(false);
    }
  }

  const reExtractSource =
    pasteText.trim().length >= 100
      ? pasteText
      : selectedId
        ? buildJobExtractSource(jobs.find((j) => j.id === selectedId) ?? {
            title,
            company,
            location: location || null,
            description,
            raw_metadata: jobMetadata,
          })
        : buildJobExtractSource({
            title,
            company,
            location: location || null,
            description,
            raw_metadata: jobMetadata,
          });
  const canReExtract = canExtractFromText(reExtractSource);

  async function handleSave() {
    if (!title.trim() || !company.trim() || !description.trim()) return;
    setSaving(true);
    try {
      const payload = {
        title: title.trim(),
        company: company.trim(),
        description: description.trim(),
        location: location.trim() || undefined,
        url: url.trim() || undefined,
        raw_metadata: jobMetadata ?? undefined,
        ...(!selectedId && profileId ? { profile_id: profileId } : {}),
      };
      const saved = selectedId
        ? await api.jobs.update(selectedId, payload)
        : await api.jobs.create(payload);
      setJobs((prev) => {
        const exists = prev.some((j) => j.id === saved.id);
        return exists ? prev.map((j) => (j.id === saved.id ? saved : j)) : [saved, ...prev];
      });
      onSaved(saved);
    } finally {
      setSaving(false);
    }
  }

  function handleNew() {
    onSelect({
      id: "",
      title: "",
      company: "",
      description: "",
      location: null,
      url: null,
      source: null,
      raw_metadata: null,
      created_at: "",
      updated_at: "",
    });
    setPasteText("");
    setTitle("");
    setCompany("");
    setLocation("");
    setDescription("");
    setUrl("");
    setJobMetadata(null);
    setError(null);
  }

  return (
    <Card
      title="Job"
      description="Paste a job posting — we extract fields and run a full match analysis when you save"
      action={
        jobs.length > 0 ? (
          <select
            value={selectedId ?? ""}
            onChange={(e) => {
              if (!e.target.value) {
                handleNew();
                return;
              }
              const job = jobs.find((j) => j.id === e.target.value);
              if (job) onSelect(job);
            }}
            className="rounded-lg border border-border bg-surface px-3 py-1.5 text-sm text-text outline-none focus:border-accent"
          >
            <option value="">New job</option>
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.title} @ {j.company}
              </option>
            ))}
          </select>
        ) : undefined
      }
    >
      {error && <ErrorBanner message={error} />}

      <Field label="Paste job posting" hint="Copy the full listing from any site — text or HTML">
        <Textarea
          value={pasteText}
          onChange={(e) => setPasteText(e.target.value)}
          placeholder="Paste the entire job posting here, then click Extract fields..."
          rows={8}
        />
      </Field>
      <div className="mb-6 flex flex-wrap gap-2">
        <Button onClick={handleExtract} loading={extracting} disabled={pasteText.trim().length < 100}>
          Extract fields
        </Button>
        {canReExtract && (selectedId || title || description) && (
          <Button variant="ghost" onClick={handleReExtract} loading={extracting}>
            Re-extract fields
          </Button>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Title">
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Senior Backend Engineer"
          />
        </Field>
        <Field label="Company">
          <Input
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="Acme Corp"
          />
        </Field>
      </div>
      <Field label="Location" hint="Optional">
        <Input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Remote · Berlin"
        />
      </Field>
      <Field label="Posting URL" hint="Optional — your reference only, never fetched">
        <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…" />
      </Field>
      <Field label="Description">
        <Textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Extracted or edited job description..."
          rows={12}
        />
      </Field>
      <div className="flex gap-2">
        <Button
          onClick={handleSave}
          loading={saving}
          disabled={!title.trim() || !company.trim() || !description.trim()}
        >
          {selectedId ? "Update job" : "Save & analyze match"}
        </Button>
        {(selectedId || title || pasteText) && (
          <Button variant="ghost" onClick={handleNew}>
            New
          </Button>
        )}
      </div>
    </Card>
  );
}
