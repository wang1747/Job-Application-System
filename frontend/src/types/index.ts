// ===== 通用 =====
export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
}

// ===== 认证 =====
export interface User {
  id: string;
  name: string;
  role?: string;
  is_active?: boolean;
  created_at: string;
}

export interface AdminUser {
  id: string;
  name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ===== JD =====
export interface JDParseResult {
  company?: string;
  position?: string;
  must_have: string[];
  nice_to_have: string[];
  tech_stack: {
    backend: string[];
    frontend: string[];
    infra: string[];
    other: string[];
  };
  hidden_signals: string[];
}

export interface JDItem {
  id: string;
  company?: string;
  position?: string;
  raw_text?: string;
  must_have?: string[];
  nice_to_have?: string[];
  tech_stack?: Record<string, string[]>;
  hidden_signals?: string[];
  created_at?: string;
}

// ===== 简历 =====
export interface ResumeItem {
  id: string;
  version: number;
  raw_text: string;
  source_file?: string | null;
  parsed_json?: {
    sections?: string[];
    skills?: string[];
    changes?: string[];
    kind?: string;
    parent_id?: string;
  } | null;
  created_at?: string;
}

export interface AtsResult {
  score: number;
  issues: string[];
  suggestions: string[];
}

export interface OptimizeResult {
  optimized: string;
  changes: string[];
  ats: AtsResult;
  ats_after: AtsResult;
  new_version: { id: string; version: number } | null;
}

// ===== 匹配 =====
export interface MatchResult {
  id?: string;
  jd_id: string;
  resume_id: string;
  company?: string;
  position?: string;
  score: number;
  skill_match_detail?: {
    matched?: string[];
    missing?: string[];
    partial?: string[];
  };
  gap_analysis?: {
    hard_gap?: string[];
    soft_gap?: string[];
    suggestion?: string;
  };
  suggestion?: string;
}

// ===== 投递 =====
export interface Application {
  id: string;
  company: string;
  position: string;
  status: string;
  jd_id?: string;
  resume_id?: string;
  applied_date?: string;
  next_action?: string;
  next_action_date?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export type ApplicationStatus =
  | "saved"
  | "applied"
  | "online_test"
  | "first_interview"
  | "second_interview"
  | "hr_round"
  | "offered"
  | "accepted"
  | "rejected";

export interface ApplicationStats {
  total: number;
  status_counts: Record<string, number>;
  status_order: ApplicationStatus[];
  conversion_rate: {
    applied_to_interview: number;
    interview_to_offer: number;
  };
}

export interface ReminderItem {
  id: string;
  company: string;
  position: string;
  status: string;
  next_action?: string;
  next_action_date?: string;
  days_until?: number;
  updated_at?: string;
  days_since_update?: number;
}

export interface Reminders {
  overdue: ReminderItem[];
  overdue_count: number;
  upcoming: ReminderItem[];
  upcoming_count: number;
  has_reminders: boolean;
}

// ===== 面试 =====
export interface InterviewArticle {
  id: string;
  company: string;
  position?: string | null;
  raw_content: string;
  source: string;
  questions?: string[] | null;
  tags?: string[] | null;
  difficulty?: string | null;
  created_at?: string;
}

export interface InterviewQuestion {
  id: string;
  article_id?: string | null;
  question: string;
  answer?: string;
  category?: string;
  difficulty?: string;
}

export interface GeneratedQuestion {
  question: string;
  category: string;
  difficulty: string;
}

export interface SimulateSession {
  session_id: string;
  question: string;
  question_number: number;
}

export interface SimulateAnswer {
  feedback: string;
  next_question: string | null;
  is_finished: boolean;
  question_number: number;
}

// ===== 模型设置（BYOK） =====
export interface PresetProvider {
  key: string;
  base_url: string;
  model: string;
}

export interface ModelConfig {
  provider: string;
  base_url: string;
  model: string;
  api_key_masked: string;
  has_config: boolean;
}

// ===== 可观测（成本看板 / 执行追踪） =====
export interface TraceItem {
  id: string;
  operation: string;
  status: string;
  total_tokens: number;
  total_cost: number;
  duration_ms: number;
  span_count: number;
  created_at: string | null;
}

export interface SpanItem {
  id: string;
  run_id: string | null;
  model: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost: number | null;
  duration_ms: number;
  start_offset_ms: number;
  status: string;
}

export interface TraceDetail {
  trace: TraceItem;
  spans: SpanItem[];
}

export interface OperationCost {
  operation: string;
  cost: number;
  tokens: number;
  count: number;
}

export interface ModelCost {
  model: string;
  cost: number;
  tokens: number;
  count: number;
}

export interface CostSummary {
  total_cost: number;
  total_tokens: number;
  trace_count: number;
  by_operation: OperationCost[];
  by_model: ModelCost[];
}
