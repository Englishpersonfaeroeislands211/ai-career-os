import type { ResumeStructuredData } from "../types";
import { Badge } from "./ui";

interface StructuredProfileViewProps {
  data: ResumeStructuredData;
  compact?: boolean;
}

export function StructuredProfileView({ data, compact = false }: StructuredProfileViewProps) {
  return (
    <div className="space-y-6">
      {!compact && (
        <section className="grid gap-4 sm:grid-cols-2">
          {data.email && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-text-muted">Email</p>
              <p className="mt-1 text-sm">{data.email}</p>
            </div>
          )}
          {data.phone && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-text-muted">Phone</p>
              <p className="mt-1 text-sm">{data.phone}</p>
            </div>
          )}
        </section>
      )}

      {data.skills.length > 0 && (
        <section>
          <h3 className="mb-3 text-xs font-medium uppercase tracking-wide text-text-muted">Skills</h3>
          <div className="flex flex-wrap gap-2">
            {data.skills.map((skill) => (
              <Badge key={skill} variant="info">
                {skill}
              </Badge>
            ))}
          </div>
        </section>
      )}

      {data.experience.length > 0 && (
        <section>
          <h3 className="mb-3 text-xs font-medium uppercase tracking-wide text-text-muted">
            Experience
          </h3>
          <div className="space-y-4">
            {data.experience.map((entry, index) => (
              <article
                key={`${entry.company}-${entry.title}-${index}`}
                className="rounded-lg border border-border bg-surface px-4 py-3"
              >
                <p className="font-medium">{entry.title}</p>
                <p className="text-sm text-text-muted">
                  {entry.company}
                  {entry.duration ? ` · ${entry.duration}` : ""}
                </p>
                {entry.highlights.length > 0 && (
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-text-muted">
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

      {data.education.length > 0 && (
        <section>
          <h3 className="mb-3 text-xs font-medium uppercase tracking-wide text-text-muted">
            Education
          </h3>
          <div className="space-y-3">
            {data.education.map((entry, index) => (
              <article
                key={`${entry.school}-${entry.degree}-${index}`}
                className="rounded-lg border border-border bg-surface px-4 py-3"
              >
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

      {data.projects.length > 0 && (
        <section>
          <h3 className="mb-3 text-xs font-medium uppercase tracking-wide text-text-muted">
            Projects
          </h3>
          <div className="space-y-3">
            {data.projects.map((entry, index) => (
              <article
                key={`${entry.name}-${index}`}
                className="rounded-lg border border-border bg-surface px-4 py-3"
              >
                <p className="font-medium">{entry.name}</p>
                {entry.description && (
                  <p className="mt-1 text-sm text-text-muted">{entry.description}</p>
                )}
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function parseStructuredData(raw: Record<string, unknown> | null): ResumeStructuredData | null {
  if (!raw || typeof raw !== "object") return null;
  const name = typeof raw.name === "string" ? raw.name : "";
  if (!name) return null;
  return {
    name,
    headline: typeof raw.headline === "string" ? raw.headline : null,
    email: typeof raw.email === "string" ? raw.email : null,
    phone: typeof raw.phone === "string" ? raw.phone : null,
    skills: Array.isArray(raw.skills) ? raw.skills.filter((s): s is string => typeof s === "string") : [],
    experience: Array.isArray(raw.experience) ? (raw.experience as ResumeStructuredData["experience"]) : [],
    education: Array.isArray(raw.education) ? (raw.education as ResumeStructuredData["education"]) : [],
    projects: Array.isArray(raw.projects) ? (raw.projects as ResumeStructuredData["projects"]) : [],
  };
}

export { parseStructuredData };
