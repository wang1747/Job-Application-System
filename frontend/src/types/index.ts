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
  email?: string;
  role?: string;
  is_active?: boolean;
  created_at: string;
}

export interface AdminUser {
  id: string;
  name: string;
  email?: string;
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
    changes?: ChangeItem[];
    kind?: string;
    parent_id?: string;
    target_jd?: { id?: string | null; company?: string; position?: string };
    added_keywords?: string[];
    generation?: ResumeGenerationResult;
  } | null;
  created_at?: string;
  version_count?: number;
  document_id?: string;
}

export interface AtsResult {
  score: number;
  issues: string[];
  suggestions: string[];
  matched_keywords?: string[];
  missing_keywords?: string[];
}

export interface ChangeItem {
  section: string;
  before: string;
  after: string;
  reason: string;
}

export interface OptimizeResult {
  optimized: string;
  changes: ChangeItem[];
  added_keywords: string[];
  removed_keywords: string[];
  removed: string[];
  length_warning: string;
  gap: {
    matched: string[];
    missing: string[];
    partial: string[];
  };
  target_jd: { id: string | null; company: string; position: string };
  ats: AtsResult;
  ats_after: AtsResult;
  preservation: {
    score: number;
    passed: boolean;
    fallback: boolean;
    missing_facts: string[];
    critical_facts?: Record<string, number>;
  };
  edits_applied?: number;
  new_version: { id: string; version: number } | null;
}

export interface ResumeGenerationContact {
  phone?: string;
  email?: string;
  github?: string;
}

export interface ResumeGenerationEducation {
  school: string;
  major: string;
  degree: string;
  start: string;
  end: string;
  courses?: string;
  gpa?: string;
  honors?: string;
  detail?: string;
}

export interface ResumeGenerationExperience {
  type: "project" | "internship" | "work";
  name: string;
  role: string;
  start: string;
  end: string;
  bullets: string[];
}

export interface ResumeGenerationResult {
  id: string;
  version: number;
  resume_text: string;
  name: string;
  position: string;
  contact: ResumeGenerationContact;
  summary: string;
  education: ResumeGenerationEducation[];
  experiences: ResumeGenerationExperience[];
  skills: string[];
  certifications: string[];
  sections: string[];
  tips: string[];
  risks?: Array<{
    section: string;
    level: string;
    issue: string;
    suggestion: string;
  }>;
  jd_alignment?: Array<{
    exp: number;
    keywords: string[];
  }>;
  reference_source?: string;
  ats: AtsResult;
  gap: {
    matched: string[];
    missing: string[];
    partial: string[];
  };
  fidelity?: {
    passed: boolean;
    added_skills: string[];
    added_certifications: string[];
    added_contacts: string[];
    added_schools: string[];
    added_companies: string[];
  };
}

export interface RecommendSkillsResult {
  direction?: string;
  skills?: string[];
  directions?: Record<string, string[]>;
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
  answer?: string;
  suspicious_numbers?: string[];
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

// ===== 薪资谈判 =====
export interface NegotiationStart {
  session_id: string;
  hr_message: string;
  round_count: number;
}

export interface NegotiationAnswer {
  coaching: string;
  next_hr_message: string | null;
  is_finished: boolean;
  round_count: number;
}

export interface NegotiationMessage {
  role: "hr" | "user";
  content: string;
}

export interface NegotiationCoaching {
  hr: string;
  answer: string;
  coaching: string;
}

export interface NegotiationSummary {
  summary: string;
  round_count: number;
  messages: NegotiationMessage[];
  coaching: NegotiationCoaching[];
  status: string;
  scenario: string;
  target_salary: string | null;
  bottom_salary: string | null;
}

export interface SalaryReference {
  salary_range: { low: number; high: number };
  suggest_ask: number;
  suggest_target: number;
  suggest_bottom: number;
  degree: string;
  school_tier: string;
  direction: string;
  position: string;
  city: string;
  city_tier: string;
  highlights: string[];
  analysis: string;
  market_basis: string;
  sources: string[];
  data_version: number;
  data_year: string;
  data_source: string;
  data_updated_at: string | null;
  caveats: string[];
}

export interface SalaryBenchmarkInfo {
  version: number;
  data_year: string;
  source: string;
  note: string;
  updated_at: string | null;
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

export interface CommunityPost {
  id: string;
  user_id: string;
  author: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  like_count: number;
  comment_count: number;
  created_at: string;
}

export interface CommunityComment {
  id: string;
  user_id: string;
  author: string;
  content: string;
  created_at: string;
}

export interface CommunityPostDetail extends CommunityPost {
  comments: CommunityComment[];
}

export interface Feedback {
  id: string;
  user_id: string;
  author: string;
  category: string;
  title: string;
  content: string;
  status: string;
  admin_reply: string | null;
  like_count: number;
  created_at: string;
  updated_at: string;
}
