export type Priority = "HIGH" | "MEDIUM" | "LOW";
export type RoleCategory =
  | "android"
  | "ios"
  | "frontend"
  | "fullstack"
  | "backend"
  | "devops"
  | "data_engineering"
  | "ai_ml";

export interface JobListItem {
  id: number;
  title: string;
  company_name: string;
  role_category: RoleCategory;
  location: string | null;
  source: string;
  url: string;
  experience: string | null;
  discovered_date: string;
  match_score: number | null;
  priority: Priority | null;
  tier: string | null;
  application_status: string | null;
}

export interface JobDetail extends JobListItem {
  description: string | null;
  employment_type: string | null;
  skills: string[];
  created_date: string | null;
  salary_min: number | null;
  salary_max: number | null;
  currency: string | null;
  category: string | null;
  // score breakdown
  skill_score: number | null;
  experience_score: number | null;
  location_score: number | null;
  seniority_score: number | null;
  company_score: number | null;
  interview_likelihood: number | null;
  matched_skills: string[];
  missing_skills: string[];
  scored_by: string | null;
}

export interface OverviewStats {
  totalOpen: number;
  newToday: number;
  companies: number;
  scored: number;
  byPriority: { priority: Priority; count: number }[];
  byRole: { role: RoleCategory; count: number }[];
  bySource: { source: string; count: number }[];
  topCompanies: { company: string; count: number; high: number }[];
  scoreBuckets: { bucket: string; count: number }[];
  discoveries: { day: string; count: number }[];
  highMediumCount: number;
}

export interface ApplicationCard {
  job_id: number;
  status: string;
  title: string;
  company_name: string;
  role_category: RoleCategory;
  location: string | null;
  url: string;
  match_score: number | null;
  priority: Priority | null;
  last_update: string;
}

export interface CompanyRow {
  name: string;
  category: string | null;
  tier: string | null;
  total: number;
  high: number;
  medium: number;
}

export interface JobFacets {
  sources: string[];
  companies: string[];
}
