import type { Job, JobCreate, JobParseResult, MatchAnalysis, Profile, ProfileCreate, ResumeParseResult } from "../types";
import type { AppSettings, ListModelsRequest, ModelListResponse, SettingsUpdate } from "../types/settings";

const BASE = "/api/v1";

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers);
  if (options?.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      if (body.detail) {
        message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // ignore parse errors
    }
    throw new ApiError(res.status, message);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  profiles: {
    list: () => request<Profile[]>("/profiles"),
    create: (data: ProfileCreate) =>
      request<Profile>("/profiles", { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: Partial<ProfileCreate>) =>
      request<Profile>(`/profiles/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    parseResume: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return request<ResumeParseResult>("/profiles/parse-resume", {
        method: "POST",
        body: form,
      });
    },
  },

  jobs: {
    list: () => request<Job[]>("/jobs"),
    create: (data: JobCreate) =>
      request<Job>("/jobs", { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: Partial<JobCreate>) =>
      request<Job>(`/jobs/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    parseText: (text: string) =>
      request<JobParseResult>("/jobs/parse-text", {
        method: "POST",
        body: JSON.stringify({ text }),
      }),
  },

  matchAnalyses: {
    list: () => request<MatchAnalysis[]>("/match-analyses"),
    get: (id: string) => request<MatchAnalysis>(`/match-analyses/${id}`),
    create: (profileId: string, jobId: string) =>
      request<MatchAnalysis>("/match-analyses", {
        method: "POST",
        body: JSON.stringify({ profile_id: profileId, job_id: jobId }),
      }),
  },

  settings: {
    get: () => request<AppSettings>("/settings"),
    update: (data: SettingsUpdate) =>
      request<AppSettings>("/settings", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
  },

  llm: {
    listModels: (data: ListModelsRequest) =>
      request<ModelListResponse>("/llm/models", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
};

export { ApiError };
