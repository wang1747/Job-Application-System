import type {
  ApiResponse,
  Application,
  ApplicationStats,
  GeneratedQuestion,
  InterviewArticle,
  InterviewQuestion,
  JDItem,
  JDParseResult,
  LoginResponse,
  MatchResult,
  OptimizeResult,
  Reminders,
  ResumeItem,
  SimulateAnswer,
  SimulateSession,
  User,
  PresetProvider,
  ModelConfig,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "";

const CONNECTION_ERROR_MESSAGE = "无法连接后端服务，请确认后端已启动";

const getToken = (): string | null => {
  return localStorage.getItem("access_token");
};

async function fetchResponse(input: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init);
  } catch {
    throw new Error(CONNECTION_ERROR_MESSAGE);
  }
}

async function parseResponse<T>(res: Response): Promise<ApiResponse<T>> {
  const text = await res.text();
  let body: ApiResponse<T>;
  try {
    body = JSON.parse(text);
  } catch {
    throw new Error(`HTTP ${res.status}: 响应不是有效 JSON`);
  }
  if (!res.ok) {
    const detail = (body as { detail?: string }).detail || `HTTP ${res.status}`;
    throw new Error(detail);
  }
  return body;
}

async function request<T>(path: string, options?: RequestInit): Promise<ApiResponse<T>> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetchResponse(`${BASE_URL}${path}`, {
    headers,
    ...options,
  });
  return parseResponse<T>(res);
}

async function requestForm<T>(path: string, formData: FormData): Promise<ApiResponse<T>> {
  const headers: HeadersInit = {};
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetchResponse(`${BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: formData,
  });
  return parseResponse<T>(res);
}

export async function downloadResumeExport(
  resumeId: string,
  format: "pdf" | "word",
): Promise<Blob> {
  const headers: HeadersInit = {};
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetchResponse(
    `${BASE_URL}/api/v1/resume/${resumeId}/export?format=${format}`,
    { headers },
  );
  if (!res.ok) {
    const text = await res.text();
    let detail = `HTTP ${res.status}`;
    try {
      const body = JSON.parse(text) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // keep HTTP fallback
    }
    throw new Error(detail);
  }
  return res.blob();
}

export async function loginRequest(
  username: string,
  password: string,
): Promise<ApiResponse<LoginResponse>> {
  return request("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function registerRequest(
  name: string,
  password: string,
): Promise<ApiResponse<{ id: string; name: string; created_at: string }>> {
  return request("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ name, password }),
  });
}

export const api = {
  health: () => request<{ status: string; message: string }>("/api/health"),

  auth: {
    register: registerRequest,
    login: loginRequest,
    me: () => request<User>("/api/v1/auth/me"),
    logout: () =>
      request<{ message: string }>("/api/v1/auth/logout", {
        method: "POST",
      }),
  },

  jd: {
    parse: (rawText: string) =>
      request<{ id: string; parsed: JDParseResult }>("/api/v1/jd/parse", {
        method: "POST",
        body: JSON.stringify({ raw_text: rawText }),
      }),
    ocr: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return requestForm<{
        id: string;
        parsed: JDParseResult;
        ocr_text: string;
      }>("/api/v1/jd/ocr", formData);
    },
    list: () => request<JDItem[]>("/api/v1/jd/list"),
    delete: (id: string) =>
      request<null>(`/api/v1/jd/${id}`, { method: "DELETE" }),
  },

  resume: {
    export: downloadResumeExport,
    list: () => request<ResumeItem[]>("/api/v1/resume/list"),
    upload: (rawText: string, sourceFile?: string) =>
      request<{ id: string; version: number }>("/api/v1/resume/upload", {
        method: "POST",
        body: JSON.stringify({ raw_text: rawText, source_file: sourceFile }),
      }),
    uploadFile: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return requestForm<{ id: string; version: number; filename: string }>(
        "/api/v1/resume/upload-file",
        formData,
      );
    },
    optimize: (resumeId: string, jdText: string) =>
      request<OptimizeResult>("/api/v1/resume/optimize", {
        method: "POST",
        body: JSON.stringify({ resume_id: resumeId, jd_text: jdText }),
      }),
    versions: (resumeId: string) =>
      request<ResumeItem[]>(`/api/v1/resume/${resumeId}/versions`),
  },

  match: {
    run: (jdId: string, resumeId: string) =>
      request<MatchResult>("/api/v1/match", {
        method: "POST",
        body: JSON.stringify({ jd_id: jdId, resume_id: resumeId }),
      }),
    batch: (resumeId: string, jdTexts: string[]) =>
      request<{
        results: Array<{
          index: number;
          success: boolean;
          error?: string | null;
          match?: MatchResult | null;
        }>;
      }>("/api/v1/match/batch", {
        method: "POST",
        body: JSON.stringify({ resume_id: resumeId, jd_texts: jdTexts }),
      }),
    rankings: () => request<MatchResult[]>("/api/v1/match/rankings"),
    detail: (matchId: string) =>
      request<MatchResult>(`/api/v1/match/${matchId}`),
  },

  interview: {
    articles: () =>
      request<{ items: InterviewArticle[]; total: number }>(
        "/api/v1/interview/articles",
      ),
    delete: (id: string) =>
      request<null>(`/api/v1/interview/articles/${id}`, { method: "DELETE" }),
    importArticle: (company: string, rawContent: string, position?: string) =>
      request<{
        id: string;
        duplicate: boolean;
        questions: string[];
        question_count: number;
        tags: string[];
        difficulty: string | null;
      }>("/api/v1/interview/articles", {
        method: "POST",
        body: JSON.stringify({ company, position, raw_content: rawContent }),
      }),
    uploadArticle: (company: string, file: File) => {
      const formData = new FormData();
      formData.append("company", company);
      formData.append("file", file);
      return requestForm<{
        id: string;
        duplicate: boolean;
        filename: string;
        question_count: number;
      }>("/api/v1/interview/articles/upload", formData);
    },
    ocrArticle: (company: string, file: File, position?: string) => {
      const formData = new FormData();
      formData.append("company", company);
      formData.append("file", file);
      if (position) formData.append("position", position);
      return requestForm<{
        id: string;
        duplicate: boolean;
        filename: string;
        question_count: number;
        ocr_text: string;
      }>("/api/v1/interview/articles/ocr", formData);
    },
    questions: () =>
      request<{ items: InterviewQuestion[]; total: number }>(
        "/api/v1/interview/questions",
      ),
    generate: (resumeId: string, jdId: string, articleId?: string) =>
      request<{ questions: GeneratedQuestion[] }>("/api/v1/interview/generate", {
        method: "POST",
        body: JSON.stringify({
          resume_id: resumeId,
          jd_id: jdId,
          article_id: articleId,
        }),
      }),
    simulateStart: (resumeId: string, jdId: string) =>
      request<SimulateSession>("/api/v1/interview/simulate/start", {
        method: "POST",
        body: JSON.stringify({ resume_id: resumeId, jd_id: jdId }),
      }),
    simulateAnswer: (sessionId: string, answer: string) =>
      request<SimulateAnswer>(
        `/api/v1/interview/simulate/${sessionId}/answer`,
        {
          method: "POST",
          body: JSON.stringify({ answer }),
        },
      ),
    simulateSummary: (sessionId: string) =>
      request<{
        summary: string;
        total_questions: number;
        questions: string[];
        answers: string[];
        feedbacks: string[];
        status: string;
      }>(`/api/v1/interview/simulate/${sessionId}/summary`),
  },

  applications: {
    list: () => request<Application[]>("/api/v1/applications"),
    create: (company: string, position: string, jdId?: string, resumeId?: string) =>
      request<{ id: string }>("/api/v1/applications", {
        method: "POST",
        body: JSON.stringify({
          company,
          position,
          jd_id: jdId,
          resume_id: resumeId,
        }),
      }),
    update: (
      id: string,
      payload: {
        status?: string;
        applied_date?: string;
        next_action?: string;
        next_action_date?: string;
        notes?: string;
      },
    ) =>
      request<Application>(`/api/v1/applications/${id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      }),
    updateStatus: (id: string, status: string) =>
      request<{ id: string; status: string }>(
        `/api/v1/applications/${id}/status`,
        {
          method: "PUT",
          body: JSON.stringify({ status }),
        },
      ),
    remove: (id: string) =>
      request<null>(`/api/v1/applications/${id}`, { method: "DELETE" }),
    stats: () => request<ApplicationStats>("/api/v1/applications/stats"),
    reminders: () => request<Reminders>("/api/v1/applications/reminders"),
    addEvent: (
      id: string,
      payload: {
        event_type: string;
        from_status?: string;
        to_status?: string;
        description?: string;
      },
    ) =>
      request<{
        id: string;
        event_type: string;
        from_status?: string;
        to_status?: string;
        description?: string;
        event_date: string;
      }>(`/api/v1/applications/${id}/events`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    interviewArticles: (id: string) =>
      request<InterviewArticle[]>(
        `/api/v1/applications/${id}/interview-articles`,
      ),
  },

  modelConfig: {
    presets: () => request<PresetProvider[]>("/api/v1/user/model-config/presets"),
    get: () => request<ModelConfig>("/api/v1/user/model-config/"),
    save: (payload: { provider: string; base_url: string; model: string; api_key: string }) =>
      request<{ message: string; config: ModelConfig }>("/api/v1/user/model-config/", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    test: (payload: { base_url: string; model: string; api_key: string }) =>
      request<{ message: string }>("/api/v1/user/model-config/test", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    clear: () => request<{ message: string }>("/api/v1/user/model-config/", {
      method: "DELETE",
    }),
  },
};
