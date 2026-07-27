export interface ExperienceEntry {
  title: string;
  company: string;
  duration?: string | null;
  highlights: string[];
}

export interface EducationEntry {
  degree: string;
  school: string;
  duration?: string | null;
  highlights: string[];
}

export interface ProjectEntry {
  name: string;
  description?: string | null;
  highlights: string[];
}

export interface ResumeStructuredData {
  name: string;
  headline?: string | null;
  email?: string | null;
  phone?: string | null;
  skills: string[];
  experience: ExperienceEntry[];
  education: EducationEntry[];
  projects: ProjectEntry[];
}

export interface ResumeParseResult {
  name: string | null;
  headline: string | null;
  resume_text: string;
  structured_data: ResumeStructuredData | null;
}

export interface Profile {
  id: string;
  name: string;
  headline: string | null;
  resume_text: string;
  structured_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface Job {
  id: string;
  title: string;
  company: string;
  description: string;
  location: string | null;
  url: string | null;
  source: string | null;
  raw_metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface MatchAnalysis {
  id: string;
  profile_id: string;
  job_id: string;
  status: "pending" | "completed" | "failed";
  result: MatchResult | null;
  error: string | null;
  created_at: string;
}

export interface MatchStrength {
  point: string;
  evidence: string;
}

export interface MatchGap {
  point: string;
  severity: "blocker" | "minor";
}

export interface MatchResult {
  match_score?: number;
  recommendation?: "apply" | "maybe" | "skip";
  strengths?: MatchStrength[];
  gaps?: MatchGap[];
  summary?: string;
}

export interface ProfileCreate {
  name: string;
  headline?: string;
  resume_text: string;
  structured_data?: ResumeStructuredData | null;
}

export interface JobCreate {
  title: string;
  company: string;
  description: string;
  location?: string;
  url?: string;
}
