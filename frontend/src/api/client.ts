import type { ApiResponse, JDItem, JDParseResult, Application, InterviewQuestion, MatchResult } from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<ApiResponse<T>> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  return res.json();
}

export const api = {
  health: () => request<{ status: string; message: string }>("/api/health"),

  jd: {
    parse: (rawText: string) =>
      request<{ id: string; parsed: JDParseResult }>("/api/v1/jd/parse", {
        method: "POST",
        body: JSON.stringify({ raw_text: rawText }),
      }),
    list: () => request<JDItem[]>("/api/v1/jd/list"),
    delete: (id: string) =>
      request<null>(`/api/v1/jd/${id}`, { method: "DELETE" }),
  },

  resume: {
    list: () => request<unknown[]>("/api/v1/resume/list"),
  },

  match: {
    rankings: () => request<MatchResult[]>("/api/v1/match/rankings"),
  },

  interview: {
    questions: () => request<InterviewQuestion[]>("/api/v1/interview/questions"),
  },

  applications: {
    list: () => request<Application[]>("/api/v1/applications"),
  },
};
