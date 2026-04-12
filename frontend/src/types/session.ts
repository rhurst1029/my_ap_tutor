export interface GuidingQuestionResponse {
  guiding_question_id: string;
  text_response: string | null;
  audio_file: string | null;
  transcript: string | null;
  transcript_confidence: number | null;
}

export interface QuestionResponse {
  question_id: string;
  selected_answer: string | null;
  free_response_text: string | null;
  is_correct: boolean;
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
  timestamp: string;
  total_questions: number;
  completed: boolean;
  study_completed: boolean;
}
