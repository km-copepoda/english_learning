export interface UserOut {
  id: number;
  username: string;
  role: 'parent' | 'child';
  email?: string;
}

export interface ChildOut {
  id: number;
  username: string;
  created_at: string;
}

export interface QuizWord {
  id: number;
  english: string;
  japanese: string;
  english_katakana: string;
}

export interface AnswerResult {
  is_correct: boolean;
  correct_answer: string;
  english_katakana: string;
}

export interface MenuStatus {
  today: number;
  review_week: number;
  review_month: number;
  review_over_month: number;
  review_all: number;
  weak_month: number;
  weak_over_month: number;
  weak_all: number;
}

export interface DailyStat {
  date: string;
  today_correct: number;
  today_hint: number;
  today_incorrect: number;
  review_correct: number;
  review_hint: number;
  review_incorrect: number;
  weak_correct: number;
  weak_hint: number;
  weak_incorrect: number;
}

export interface WeakWordOut {
  id: number;
  english: string;
  japanese: string;
  english_katakana: string;
  total_attempts: number;
  correct_count: number;
  hint_count: number;
  accuracy: number;
}
