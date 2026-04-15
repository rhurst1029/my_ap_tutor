export interface GuidingQuestionResponse {
  guiding_question_id: string;
  text_response: string | null;
  audio_file: string | null;
  transcript: string | null;
  transcript_confidence: number | null;
}

export interface FRQRunAttempt {
  attempt_number: number;
  code_snapshot: string;
  stdout: string;
  stderr: string;
  compile_errors: string[];
  passed: boolean;
  timestamp: string;
}

export interface FRQPartResponse {
  part: string;
  final_code: string;
  passed: boolean;
  total_runs: number;
  total_time_seconds: number;
  time_to_first_keystroke_seconds: number;
  run_attempts: FRQRunAttempt[];
  compile_errors_encountered: string[];
  line_time_map: Record<string, number>;
  line_edit_counts: Record<string, number>;
  struggled_lines: number[];
}

export interface QuestionResponse {
  question_id: string;
  question_type: 'multiple_choice' | 'code_trace' | 'frq';
  selected_answer: string | null;
  frq_parts: FRQPartResponse[];
  is_correct: boolean;
  attempt_number: number;      // 1 = first try, 2 = second try
  score_weight: number;        // 1.0 | 0.7 | 0.0
  time_spent_seconds: number;
  guiding_question_responses: GuidingQuestionResponse[];
}

export interface SessionSaveRequest {
  session_id: string;
  student_name: string;
  test_id: string;
  iteration: number;
  started_at: string;
  completed_at: string;
  responses: QuestionResponse[];
}

export interface SessionMetadata {
  session_id: string;
  student_name: string;
  test_id: string;
  iteration: number;
  phase: 'assessment' | 'report_ready' | 'practice_ready' | 'quiz_ready' | 'complete';
  timestamp: string;
  total_questions: number;
  completed: boolean;
  study_completed: boolean;
}
