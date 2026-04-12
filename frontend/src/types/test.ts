export interface GuidingQuestion {
  id: string;
  text: string;
}

export interface Question {
  id: string;
  type: 'multiple_choice' | 'code_trace';
  topic_tags: string[];
  prompt: string;
  code_block?: string;
  options: Record<string, string>;
  answer_key: string;
  guiding_questions: GuidingQuestion[];
}

export interface Test {
  test_id: string;
  title: string;
  questions: Question[];
}
