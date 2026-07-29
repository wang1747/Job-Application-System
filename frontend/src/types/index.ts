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
  must_have?: string[];
  nice_to_have?: string[];
  tech_stack?: Record<string, string[]>;
  hidden_signals?: string[];
  created_at?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
}

export interface MatchResult {
  jd_id: string;
  resume_id: string;
  score: number;
  skill_match_detail?: Record<string, unknown>;
  gap_analysis?: Record<string, unknown>;
  suggestion?: string;
}

export interface Application {
  id: string;
  company: string;
  position: string;
  status: string;
  applied_date?: string;
  next_action?: string;
  next_action_date?: string;
  created_at?: string;
  updated_at?: string;
}

export interface InterviewQuestion {
  id: string;
  question: string;
  answer?: string;
  category?: string;
  difficulty?: string;
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
