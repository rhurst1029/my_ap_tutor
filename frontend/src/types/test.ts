export interface GuidingQuestion {
  id: string;
  text: string;
  options?: Record<string, string>;  // present → render as MC; absent → render as textarea
  answer_key?: string;
}

export interface FRQTestCase {
  description: string;
  expected_output: string;
}

export interface FRQPart {
  part: string;           // "a", "b", "c"
  description: string;
  points: number;
  starter_code: string;
  test_cases: FRQTestCase[];
  line_concepts: Record<string, string>; // line number → concept name
}

export interface Question {
  id: string;
  type: 'multiple_choice' | 'code_trace' | 'frq';
  topic_tags: string[];
  unit: number;
  prompt: string;
  code_block?: string;
  options: Record<string, string>;   // empty for frq
  answer_key: string;                // empty for frq
  guiding_questions: GuidingQuestion[];
  // FRQ only
  parts?: FRQPart[];
  total_points?: number;
}

export interface Test {
  test_id: string;
  title: string;
  questions: Question[];
}
