import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { ResumeParseResult, ResumeStructuredData } from "../types";
import { Layout } from "../components/Layout";
import { OnboardingSteps } from "../components/OnboardingSteps";
import { StructuredProfileView } from "../components/StructuredProfileView";
import { Button, ErrorBanner, Field, Input, Textarea } from "../components/ui";
import { setActiveProfileId } from "../lib/profile";

interface ReviewLocationState {
  parsed?: ResumeParseResult;
  profileId?: string;
  mode?: "update";
  returnTo?: string;
}

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
  const state = location.state as ReviewLocationState | null;
  const parsed = state?.parsed;
  const isUpdate = state?.mode === "update" && !!state.profileId;

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
      if (isUpdate && state?.profileId) {
        await api.profiles.update(state.profileId, {
          name: name.trim(),
          headline: headline.trim() || undefined,
          resume_text: resumeText.trim(),
          structured_data: payloadStructured,
        });
        setActiveProfileId(state.profileId);
        navigate(state.returnTo ?? "/profile", { replace: true });
      } else {
        const profile = await api.profiles.create({
          name: name.trim(),
          headline: headline.trim() || undefined,
          resume_text: resumeText.trim(),
          structured_data: payloadStructured,
        });
        setActiveProfileId(profile.id);
        navigate("/", { replace: true });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Layout subtitle={isUpdate ? "Review updated resume" : "Review your profile"} showNav={isUpdate}>
      <main className="mx-auto max-w-2xl space-y-6 px-6 py-12">
        {!isUpdate && <OnboardingSteps current={3} />}

        <div>
          <h2 className="text-2xl font-semibold">Review & confirm</h2>
          <p className="mt-2 text-text-muted">
            We structured your resume with AI. Edit anything that looks wrong before saving.
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

        {structuredData && (
          <section className="rounded-xl border border-border bg-surface-raised p-5">
            <h3 className="mb-4 text-sm font-medium uppercase tracking-wide text-text-muted">
              Extracted preview
            </h3>
            <StructuredProfileView
              data={{
                ...structuredData,
                name: name.trim() || structuredData.name,
                headline: headline.trim() || structuredData.headline,
                email: email.trim() || structuredData.email,
                phone: phone.trim() || structuredData.phone,
                skills: textToSkills(skillsText),
              }}
              compact
            />
          </section>
        )}

        <div className="flex justify-between">
          <Button
            variant="ghost"
            onClick={() =>
              navigate(isUpdate ? (state?.returnTo ?? "/profile") : "/onboarding/upload")
            }
          >
            {isUpdate ? "Cancel" : "Re-upload"}
          </Button>
          <Button
            onClick={handleSave}
            loading={saving}
            disabled={!name.trim() || !resumeText.trim()}
            className="px-8"
          >
            {isUpdate ? "Update profile" : "Save & continue"}
          </Button>
        </div>
      </main>
    </Layout>
  );
}
