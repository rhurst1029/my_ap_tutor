import { useState } from 'react';
import type { Question, GuidingQuestion } from '../../types/test';
import type { FRQPartResponse } from '../../types/session'; // used by FRQCard callback
import CodeTrace from './CodeTrace';
import FRQCard from './FRQCard';

interface GuidingResponse {
  guiding_question_id: string;
  text_response: string;
}

interface Props {
  question: Question;
  index: number;
  total: number;
  isLast: boolean;
  onAnswer: (answer: string, guidingResponses: GuidingResponse[]) => void;
  onNext: () => void;
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
  inheritance: 'Inheritance',
  recursion: 'Recursion',
  using_objects: 'Using Objects',
  writing_classes: 'Writing Classes',
};

const TYPE_LABELS: Record<string, string> = {
  code_trace: 'Code Trace',
  multiple_choice: 'Multiple Choice',
  frq: 'Free Response',
};

export default function QuestionCard({ question, index, total, isLast, onAnswer, onNext }: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  // submitted = main answer locked in; shows feedback + guiding questions
  const [submitted, setSubmitted] = useState(false);
  // MC guiding questions: track which option was chosen per guiding question id
  const [guidingSelections, setGuidingSelections] = useState<Record<string, string>>({});
  // Free-text guiding questions (fallback for questions without MC options)
  const [guidingTexts, setGuidingTexts] = useState<Record<string, string>>({});

  const isCorrect = selected === question.answer_key;

  // ── Main answer submit ────────────────────────────────────────────────────
  const handleMCSubmit = () => {
    if (!selected) return;
    setSubmitted(true);
  };

  // ── Guiding MC select (auto-locks on first pick) ──────────────────────────
  const handleGuidingSelect = (gq: GuidingQuestion, key: string) => {
    if (guidingSelections[gq.id] !== undefined) return; // already answered
    setGuidingSelections(prev => ({ ...prev, [gq.id]: key }));
  };

  // ── Next / Finish button ──────────────────────────────────────────────────
  const handleNext = () => {
    if (!selected) return;
    // Build guiding responses from whichever mode each question used
    const guidingResponses: GuidingResponse[] = question.guiding_questions.map(gq => ({
      guiding_question_id: gq.id,
      text_response: gq.options
        ? (guidingSelections[gq.id] ?? '')
        : (guidingTexts[gq.id] ?? ''),
    }));
    onAnswer(selected, guidingResponses);
    if (!isLast) onNext();
  };

  // ── FRQ (unchanged) ───────────────────────────────────────────────────────
  const handleFRQComplete = (frqParts: FRQPartResponse[]) => {
    const allPassed = frqParts.every(p => p.passed);
    onAnswer(allPassed ? 'PASSED' : 'FAILED', []);
    if (!isLast) onNext();
  };

  // ── Option CSS class helper ───────────────────────────────────────────────
  const optionClass = (key: string) => {
    const classes = ['option'];
    if (selected === key) classes.push('selected');
    if (submitted && key === question.answer_key) classes.push('correct');
    if (submitted && selected === key && key !== question.answer_key) classes.push('incorrect');
    return classes.join(' ');
  };

  // ── Guiding option CSS class helper ──────────────────────────────────────
  const guidingOptionClass = (gq: GuidingQuestion, key: string) => {
    const classes = ['guiding-option'];
    const picked = guidingSelections[gq.id];
    if (picked === key) classes.push('guiding-selected');
    if (picked !== undefined) {
      // reveal after selection
      if (key === gq.answer_key) classes.push('guiding-correct');
      else if (picked === key) classes.push('guiding-incorrect');
    }
    return classes.join(' ');
  };

  return (
    <div className="question-card">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="question-header">
        <span className="question-counter">Question {index + 1} of {total}</span>
        <div className="question-badges">
          <span className={`badge type-badge ${question.type}`}>
            {TYPE_LABELS[question.type]}
          </span>
          {question.topic_tags.map(tag => (
            <span key={tag} className="badge topic-badge">{TOPIC_LABELS[tag] ?? tag}</span>
          ))}
          {question.unit && (
            <span className="badge unit-badge">Unit {question.unit}</span>
          )}
        </div>
      </div>

      <p className="question-prompt">{question.prompt}</p>

      {question.code_block && <CodeTrace code={question.code_block} />}

      {/* ── FRQ ──────────────────────────────────────────────────────────── */}
      {question.type === 'frq' && question.parts && (
        <FRQCard
          questionId={question.id}
          parts={question.parts}
          onComplete={handleFRQComplete}
        />
      )}

      {/* ── MC / Code Trace ──────────────────────────────────────────────── */}
      {question.type !== 'frq' && (
        <>
          {/* Main options */}
          <div className="options">
            {Object.entries(question.options).map(([key, val]) => (
              <label key={key} className={optionClass(key)}>
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

          {/* Submit button — only before submission */}
          {!submitted && (
            <button
              className="btn-primary submit-btn"
              disabled={!selected}
              onClick={handleMCSubmit}
            >
              Submit Answer
            </button>
          )}

          {/* ── Post-submit: feedback + guiding questions + Next ──────────── */}
          {submitted && (
            <>
              {/* Feedback banner */}
              <div className={`feedback ${isCorrect ? 'feedback-correct' : 'feedback-incorrect'}`}>
                {isCorrect
                  ? '✓ Correct!'
                  : (
                    <>
                      <div className="feedback-wrong-header">✗ Not quite — the correct answer is {question.answer_key}</div>
                      <div className="feedback-correct-text">
                        {question.options[question.answer_key]}
                      </div>
                    </>
                  )
                }
              </div>

              {/* Guiding / reflection questions */}
              {question.guiding_questions.length > 0 && (
                <div className="guiding-questions">
                  <h4>
                    {isCorrect ? 'Reflect' : 'Work through these to understand why'}
                  </h4>

                  {question.guiding_questions.map((gq, gi) => (
                    <div key={gq.id} className="guiding-question">
                      <p className="guiding-prompt">
                        <span className="guiding-num">{gi + 1}.</span> {gq.text}
                      </p>

                      {/* MC guiding question */}
                      {gq.options ? (
                        <div className="guiding-options">
                          {Object.entries(gq.options).map(([key, val]) => (
                            <button
                              key={key}
                              className={guidingOptionClass(gq, key)}
                              onClick={() => handleGuidingSelect(gq, key)}
                              disabled={guidingSelections[gq.id] !== undefined}
                            >
                              <span className="guiding-option-key">{key}</span>
                              <span className="guiding-option-text">{val}</span>
                            </button>
                          ))}
                        </div>
                      ) : (
                        /* Fallback: free-text (for older tests without MC guiding questions) */
                        <textarea
                          placeholder="Type your thoughts here (optional)…"
                          value={guidingTexts[gq.id] ?? ''}
                          onChange={e =>
                            setGuidingTexts(prev => ({ ...prev, [gq.id]: e.target.value }))
                          }
                          rows={2}
                        />
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Next / Finish button */}
              <button className="btn-next" onClick={handleNext}>
                {isLast ? 'Finish Quiz' : 'Next Question →'}
              </button>
            </>
          )}
        </>
      )}
    </div>
  );
}
