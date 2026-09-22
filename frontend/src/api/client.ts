import type {
  ApiResponse,
  AdminUser,
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
  NegotiationStart,
  NegotiationAnswer,
  NegotiationSummary,
  SalaryReference,
  SalaryBenchmarkInfo,
  User,
  PresetProvider,
  ModelConfig,
  TraceItem,
  TraceDetail,
  CostSummary,
  ResumeGenerationResult,
  ResumeGenerationEducation,
  ResumeGenerationExperience,
  RecommendSkillsResult,
  CommunityPost,
  CommunityPostDetail,
  Feedback,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "";

const CONNECTION_ERROR_MESSAGE = "无法连接后端服务，请确认后端已启动";

const getToken = (): string | null => {
  return localStorage.getItem("access_token");
};

function handleUnauthorized() {
  localStorage.removeItem("access_token");
  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

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
    if (res.status === 401) {
      handleUnauthorized();
    }
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
  email: string,
  password: string,
): Promise<ApiResponse<LoginResponse>> {
  return request("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ username: email, password }),
  });
}

export async function registerRequest(
  account: string,
  name: string,
  password: string,
): Promise<ApiResponse<{ id: string; name: string; email?: string; created_at: string }>> {
  return request("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ account, name, password }),
  });
}

export async function sendResetCode(
  account: string,
  email?: string,
): Promise<ApiResponse<{ message: string; email_masked?: string }>> {
  return request("/api/v1/auth/forgot-password/send-code", {
    method: "POST",
    body: JSON.stringify({ account, email: email || null }),
  });
}

export async function resetPassword(
  account: string,
  email: string,
  code: string,
  newPassword: string,
): Promise<ApiResponse<{ message: string }>> {
  return request("/api/v1/auth/forgot-password/reset", {
    method: "POST",
    body: JSON.stringify({ account, email, code, new_password: newPassword }),
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
    changePassword: (oldPassword: string, newPassword: string) =>
      request<{ message: string }>("/api/v1/auth/change-password", {
        method: "POST",
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
      }),
    updateProfile: (name: string) =>
      request<User>("/api/v1/auth/profile", {
        method: "PATCH",
        body: JSON.stringify({ name }),
      }),
    sendChangeEmailCode: (newEmail: string) =>
      request<{ message: string; email_masked?: string }>(
        "/api/v1/auth/change-email/send-code",
        {
          method: "POST",
          body: JSON.stringify({ new_email: newEmail }),
        },
      ),
    changeEmail: (newEmail: string, code: string) =>
      request<User>("/api/v1/auth/change-email", {
        method: "POST",
        body: JSON.stringify({ new_email: newEmail, code }),
      }),
  },

  admin: {
    listUsers: () => request<AdminUser[]>("/api/v1/admin/users"),
    updateRole: (id: string, role: "admin" | "user") =>
      request<AdminUser>(`/api/v1/admin/users/${id}/role`, {
        method: "PUT",
        body: JSON.stringify({ role }),
      }),
    updateActive: (id: string, is_active: boolean) =>
      request<AdminUser>(`/api/v1/admin/users/${id}/active`, {
        method: "PUT",
        body: JSON.stringify({ is_active }),
      }),
    resetPassword: (id: string, new_password: string) =>
      request<{ id: string; name: string }>(
        `/api/v1/admin/users/${id}/reset_password`,
        {
          method: "POST",
          body: JSON.stringify({ new_password }),
        },
      ),
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
    update: (
      id: string,
      payload: { company?: string; position?: string },
    ) =>
      request<{ id: string; company?: string; position?: string }>(
        `/api/v1/jd/${id}`,
        {
          method: "PUT",
          body: JSON.stringify(payload),
        },
      ),
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
    optimize: (resumeId: string, jdText: string, jdId?: string) =>
      request<OptimizeResult>("/api/v1/resume/optimize", {
        method: "POST",
        body: JSON.stringify({
          resume_id: resumeId,
          jd_text: jdText,
          jd_id: jdId || null,
        }),
      }),
    versions: (resumeId: string) =>
      request<ResumeItem[]>(`/api/v1/resume/${resumeId}/versions`),
    rollback: (resumeId: string, versionId: string) =>
      request<{ id: string; version: number }>(
        `/api/v1/resume/${resumeId}/versions/${versionId}/rollback`,
        { method: "POST" },
      ),
    exportData: async (): Promise<Blob> => {
      const headers: HeadersInit = {};
      const token = getToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetchResponse(`${BASE_URL}/api/v1/resume/export-data`, {
        headers,
      });
      if (!res.ok) throw new Error(`导出失败 HTTP ${res.status}`);
      return res.blob();
    },
    delete: (resumeId: string) =>
      request<{ deleted: number }>(`/api/v1/resume/${resumeId}`, {
        method: "DELETE",
      }),
    deleteAll: () =>
      request<{ deleted: number }>("/api/v1/resume/all", { method: "DELETE" }),
  },

  resumeGeneration: {
    generate: (payload: {
      name: string;
      position: string;
      phone?: string;
      email?: string;
      github?: string;
      summary?: string;
      direction?: string;
      education: ResumeGenerationEducation[];
      experiences: ResumeGenerationExperience[];
      skills: string[];
      certifications?: string[];
      jd_text?: string;
      jd_id?: string;
    }) =>
      request<ResumeGenerationResult>("/api/v1/resume-generation/generate", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    regenerateSection: (payload: {
      resume_id: string;
      structured: Record<string, unknown>;
      section: string;
      index?: number;
      jd_text?: string;
      jd_id?: string;
    }) =>
      request<ResumeGenerationResult>(
        "/api/v1/resume-generation/regenerate-section",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      ),
    regenerateSectionVariants: (payload: {
      resume_id: string;
      structured: Record<string, unknown>;
      section: string;
      index?: number;
      jd_text?: string;
      jd_id?: string;
    }) =>
      request<{ candidates: unknown[] }>(
        "/api/v1/resume-generation/regenerate-section-variants",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      ),
    save: (payload: {
      resume_id: string;
      structured: Record<string, unknown>;
      jd_text?: string;
      jd_id?: string;
    }) =>
      request<ResumeGenerationResult>("/api/v1/resume-generation/save", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    recommendSkills: (direction?: string, limit?: number) =>
      request<RecommendSkillsResult>(
        `/api/v1/resume-generation/recommend-skills?direction=${direction ?? ""}&limit=${limit ?? 12}`,
      ),
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
    simulateFinish: (sessionId: string) =>
      request<null>(`/api/v1/interview/simulate/${sessionId}/finish`, {
        method: "POST",
      }),
  },

  salaryNegotiation: {
    start: (payload: {
      scenario: string;
      target_salary?: string;
      bottom_salary?: string;
      context?: string;
    }) =>
      request<NegotiationStart>("/api/v1/salary-negotiation/start", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    answer: (sessionId: string, answer: string) =>
      request<NegotiationAnswer>(`/api/v1/salary-negotiation/${sessionId}/answer`, {
        method: "POST",
        body: JSON.stringify({ answer }),
      }),
    summary: (sessionId: string) =>
      request<NegotiationSummary>(`/api/v1/salary-negotiation/${sessionId}/summary`),
    reference: (payload: {
      resume_id?: string;
      resume_text?: string;
      target_city?: string;
      position_hint?: string;
    }) =>
      request<SalaryReference>("/api/v1/salary-negotiation/reference", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    benchmarkInfo: () =>
      request<SalaryBenchmarkInfo>("/api/v1/salary-negotiation/benchmark/info"),
    benchmarkRefresh: () =>
      request<SalaryBenchmarkInfo>("/api/v1/salary-negotiation/benchmark/refresh", {
        method: "POST",
      }),
    benchmarkImport: (payload: {
      data: Record<string, unknown>;
      data_year?: string;
      source?: string;
      note?: string;
    }) =>
      request<SalaryBenchmarkInfo>("/api/v1/salary-negotiation/benchmark/import", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
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

  observability: {
    summary: () => request<CostSummary>("/api/v1/observability/summary"),
    traces: (page = 1, pageSize = 20, operation?: string) =>
      request<TraceItem[]>(
        `/api/v1/observability/traces?page=${page}&page_size=${pageSize}${
          operation ? `&operation=${encodeURIComponent(operation)}` : ""
        }`,
      ),
    traceDetail: (traceId: string) =>
      request<TraceDetail>(`/api/v1/observability/traces/${traceId}`),
  },

  community: {
    createPost: (payload: { title: string; content: string; category?: string; tags?: string[] }) =>
      request<{ id: string }>("/api/v1/community/posts", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    listPosts: (category?: string, page = 1, pageSize = 20) =>
      request<{ items: CommunityPost[]; total: number }>(
        `/api/v1/community/posts?page=${page}&page_size=${pageSize}${
          category ? `&category=${encodeURIComponent(category)}` : ""
        }`,
      ),
    postDetail: (id: string) => request<CommunityPostDetail>(`/api/v1/community/posts/${id}`),
    addComment: (id: string, content: string) =>
      request<{ id: string }>(`/api/v1/community/posts/${id}/comments`, {
        method: "POST",
        body: JSON.stringify({ content }),
      }),
    toggleLike: (id: string) =>
      request<{ liked: boolean; like_count: number }>(`/api/v1/community/posts/${id}/like`, {
        method: "POST",
      }),
    deletePost: (id: string) =>
      request<null>(`/api/v1/community/posts/${id}`, { method: "DELETE" }),
    deleteComment: (id: string) =>
      request<null>(`/api/v1/community/comments/${id}`, { method: "DELETE" }),
  },

  feedback: {
    create: (payload: { category?: string; title: string; content: string }) =>
      request<{ id: string }>("/api/v1/feedback", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    list: (category?: string, page = 1, pageSize = 20, status?: string) =>
      request<{ items: Feedback[]; total: number }>(
        `/api/v1/feedback?page=${page}&page_size=${pageSize}${
          category ? `&category=${encodeURIComponent(category)}` : ""
        }${status ? `&status=${encodeURIComponent(status)}` : ""}`,
      ),
    mine: () => request<Feedback[]>("/api/v1/feedback/mine"),
    toggleLike: (id: string) =>
      request<{ liked: boolean; like_count: number }>(`/api/v1/feedback/${id}/like`, {
        method: "POST",
      }),
    adminUpdate: (id: string, payload: { status?: string; admin_reply?: string }) =>
      request<{ id: string; status: string }>(`/api/v1/feedback/${id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
  },

  corpus: {
    getConsent: () => request<{ allow_corpus: boolean }>("/api/v1/corpus/consent"),
    setConsent: (allow: boolean) =>
      request<{ allow_corpus: boolean }>("/api/v1/corpus/consent", {
        method: "POST",
        body: JSON.stringify({ allow }),
      }),
  },
};
