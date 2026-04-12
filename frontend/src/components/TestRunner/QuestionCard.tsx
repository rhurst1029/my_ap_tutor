import { useState } from 'react';
import type { Question } from '../../types/test';
import CodeTrace from './CodeTrace';

interface GuidingResponse {
  guiding_question_id: string;
  text_response: string;
}

interface Props {
  question: Question;
  index: number;
  total: number;
  onAnswer: (answer: string, guidingResponses: GuidingResponse[]) => void;
}

const TOPIC_LABELS: Record<string, string> = {
  strings: 'Strings',
  arrays: 'Arrays',
  '2d_arrays': '2D Arrays',
  arraylist: 'ArrayList',
  loops: 'Loops',
  classes_and_objects: 'Classes & Objects',
  methods: 'Methods',
  operators: 'Operators',
  conditionals: 'Conditionals',
  variables_and_types: 'Variables & Types',
};

export default function QuestionCard({ question, index, total, onAnswer }: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [guidingTexts, setGuidingTexts] = useState<Record<string, string>>({});

  const handleSubmit = () => {
    if (!selected) return;
    setSubmitted(true);
    const guidingResponses = question.guiding_questions.map(gq => ({
      guiding_question_id: gq.id,
      text_response: guidingTexts[gq.id] ?? '',
    }));
    onAnswer(selected, guidingResponses);
  };

  const topicLabel = question.topic_tags
    .map(t => TOPIC_LABELS[t] ?? t)
    .join(', ');

  return (
    <div className="question-card">
      <div className="question-header">
        <span className="question-counter">Question {index + 1} of {total}</span>
        <div className="question-badges">
          <span className={`badge type-badge ${question.type}`}>
            {question.type === 'code_trace' ? 'Code Trace' : 'Multiple Choice'}
          </span>
          {question.topic_tags.map(tag => (
            <span key={tag} className="badge topic-badge">{TOPIC_LABELS[tag] ?? tag}</span>
          ))}
        </div>
      </div>

      <p className="question-prompt">{question.prompt}</p>

      {question.code_block && <CodeTrace code={question.code_block} />}

      <div className="options">
        {Object.entries(question.options).map(([key, val]) => (
          <label
            key={key}
            className={`option ${selected === key ? 'selected' : ''} ${
              submitted && key === question.answer_key ? 'correct' : ''
            } ${submitted && selected === key && key !== question.answer_key ? 'incorrect' : ''}`}
          >
            <input
              type="radio"
              name={`q-${question.id}`}
              value={key}
              disabled={submitted}
              checked={selected === key}
              onChange={() => setSelected(key)}
            />
            <span className="option-key">{key}</span>
            <span className="option-text">{val}</span>
          </label>
        ))}
      </div>

      {question.guiding_questions.length > 0 && (
        <div className="guiding-questions">
          <h4>Reflect</h4>
          {question.guiding_questions.map(gq => (
            <div key={gq.id} className="guiding-question">
              <p>{gq.text}</p>
              <textarea
                placeholder="Type your thoughts here (optional)…"
                value={guidingTexts[gq.id] ?? ''}
                onChange={e => setGuidingTexts(prev => ({ ...prev, [gq.id]: e.target.value }))}
                rows={2}
              />
            </div>
          ))}
        </div>
      )}

      {!submitted && (
        <button
          className="btn-primary submit-btn"
          disabled={!selected}
          onClick={handleSubmit}
        >
          Submit Answer
        </button>
      )}

      {submitted && (
        <div className={`feedback ${selected === question.answer_key ? 'feedback-correct' : 'feedback-incorrect'}`}>
          {selected === question.answer_key
            ? '✓ Correct!'
            : `✗ The correct answer is ${question.answer_key}: ${question.options[question.answer_key]}`}
        </div>
      )}
    </div>
  );
}
