import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Job } from "../types";
import { Button, Card, Field, Input, Textarea } from "./ui";

interface JobPanelProps {
  selectedId: string | null;
  onSelect: (job: Job) => void;
  onSaved: (job: Job) => void;
}

export function JobPanel({ selectedId, onSelect, onSaved }: JobPanelProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);

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
    }
  }, [selectedId, jobs]);

  async function handleSave() {
    if (!title.trim() || !company.trim() || !description.trim()) return;
    setSaving(true);
    try {
      const payload = {
        title: title.trim(),
        company: company.trim(),
        description: description.trim(),
        location: location.trim() || undefined,
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
    setTitle("");
    setCompany("");
    setLocation("");
    setDescription("");
  }

  return (
    <Card
      title="Job"
      description="Paste a job description to analyze fit"
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
      <Field label="Description">
        <Textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Paste the full job description here..."
          rows={12}
        />
      </Field>
      <div className="flex gap-2">
        <Button
          onClick={handleSave}
          loading={saving}
          disabled={!title.trim() || !company.trim() || !description.trim()}
        >
          {selectedId ? "Update job" : "Save job"}
        </Button>
        {selectedId && (
          <Button variant="ghost" onClick={handleNew}>
            New
          </Button>
        )}
      </div>
    </Card>
  );
}
