import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { ResumeParseResult, ResumeStructuredData } from "../types";
import { Layout } from "../components/Layout";
import { OnboardingSteps } from "../components/OnboardingSteps";
import { Button, ErrorBanner, Field, Input, Textarea } from "../components/ui";
import { setActiveProfileId } from "../lib/profile";

function skillsToText(skills: string[]) {
  return skills.join("\n");
}

function textToSkills(value: string) {
  return value
    .split(/[\n,]/)
    .map((skill) => skill.trim())
    .filter(Boolean);
}

export function ReviewPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const parsed = location.state?.parsed as ResumeParseResult | undefined;

  const [name, setName] = useState("");
  const [headline, setHeadline] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [skillsText, setSkillsText] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [structuredData, setStructuredData] = useState<ResumeStructuredData | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!parsed) {
      navigate("/onboarding/upload", { replace: true });
      return;
    }
    const structured = parsed.structured_data;
    setName(parsed.name ?? structured?.name ?? "");
    setHeadline(parsed.headline ?? structured?.headline ?? "");
    setEmail(structured?.email ?? "");
    setPhone(structured?.phone ?? "");
    setSkillsText(skillsToText(structured?.skills ?? []));
    setResumeText(parsed.resume_text);
    setStructuredData(structured);
  }, [parsed, navigate]);

  if (!parsed) return null;

  async function handleSave() {
    if (!name.trim() || !resumeText.trim()) return;
    setSaving(true);
    setError(null);

    const skills = textToSkills(skillsText);
    const payloadStructured: ResumeStructuredData | null = structuredData
      ? {
          ...structuredData,
          name: name.trim(),
          headline: headline.trim() || null,
          email: email.trim() || null,
          phone: phone.trim() || null,
          skills,
        }
      : null;

    try {
      const profile = await api.profiles.create({
        name: name.trim(),
        headline: headline.trim() || undefined,
        resume_text: resumeText.trim(),
        structured_data: payloadStructured,
      });
      setActiveProfileId(profile.id);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Layout subtitle="Review your profile">
      <main className="mx-auto max-w-2xl space-y-6 px-6 py-12">
        <OnboardingSteps current={3} />

        <div>
          <h2 className="text-2xl font-semibold">Review & confirm</h2>
          <p className="mt-2 text-text-muted">
            We structured your resume with AI. Edit anything that looks wrong before continuing.
          </p>
        </div>

        {error && <ErrorBanner message={error} />}

        <div className="space-y-4 rounded-xl border border-border bg-surface-raised p-5">
          <Field label="Name">
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
            />
          </Field>
          <Field label="Headline" hint="Optional">
            <Input
              value={headline}
              onChange={(e) => setHeadline(e.target.value)}
              placeholder="Senior Backend Engineer"
            />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Email" hint="Optional">
              <Input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
              />
            </Field>
            <Field label="Phone" hint="Optional">
              <Input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1 555 0100"
              />
            </Field>
          </div>
          <Field label="Skills" hint="One skill per line">
            <Textarea
              value={skillsText}
              onChange={(e) => setSkillsText(e.target.value)}
              rows={4}
              placeholder="Python&#10;FastAPI&#10;PostgreSQL"
            />
          </Field>
          <Field label="Resume text">
            <Textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              rows={12}
            />
          </Field>
        </div>

        {structuredData && structuredData.experience.length > 0 && (
          <section className="space-y-3 rounded-xl border border-border bg-surface-raised p-5">
            <h3 className="text-sm font-medium uppercase tracking-wide text-text-muted">
              Experience
            </h3>
            <div className="space-y-4">
              {structuredData.experience.map((entry, index) => (
                <article key={`${entry.company}-${entry.title}-${index}`} className="space-y-1">
                  <p className="font-medium">{entry.title}</p>
                  <p className="text-sm text-text-muted">
                    {entry.company}
                    {entry.duration ? ` · ${entry.duration}` : ""}
                  </p>
                  {entry.highlights.length > 0 && (
                    <ul className="list-disc space-y-1 pl-5 text-sm text-text-muted">
                      {entry.highlights.map((highlight) => (
                        <li key={highlight}>{highlight}</li>
                      ))}
                    </ul>
                  )}
                </article>
              ))}
            </div>
          </section>
        )}

        {structuredData && structuredData.education.length > 0 && (
          <section className="space-y-3 rounded-xl border border-border bg-surface-raised p-5">
            <h3 className="text-sm font-medium uppercase tracking-wide text-text-muted">
              Education
            </h3>
            <div className="space-y-3">
              {structuredData.education.map((entry, index) => (
                <article key={`${entry.school}-${entry.degree}-${index}`}>
                  <p className="font-medium">{entry.degree}</p>
                  <p className="text-sm text-text-muted">
                    {entry.school}
                    {entry.duration ? ` · ${entry.duration}` : ""}
                  </p>
                </article>
              ))}
            </div>
          </section>
        )}

        <div className="flex justify-between">
          <Button variant="ghost" onClick={() => navigate("/onboarding/upload")}>
            Re-upload
          </Button>
          <Button
            onClick={handleSave}
            loading={saving}
            disabled={!name.trim() || !resumeText.trim()}
            className="px-8"
          >
            Save & continue
          </Button>
        </div>
      </main>
    </Layout>
  );
}
