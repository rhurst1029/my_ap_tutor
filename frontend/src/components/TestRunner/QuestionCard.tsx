import { useState } from 'react';
import type { Question, GuidingQuestion } from '../../types/test';
import type { FRQPartResponse } from '../../types/session'; // used by FRQCard callback
import CodeTrace from './CodeTrace';
import FRQCard from './FRQCard';

interface GuidingResponse {
  guiding_question_id: string;
  text_response: string;
}

type SubmitState =
  | 'idle'
  | 'submitted_correct'
  | 'submitted_wrong_retry'     // attempt 1 wrong — show guiding + Try Again
  | 'submitted_wrong_final'     // attempt 2 wrong — show explanation forced open
  | 'submitted_correct_retry';  // attempt 2 correct — show 70% credit

interface Props {
  question: Question;
  index: number;
  total: number;
  isLast: boolean;
  onAnswer: (answer: string, guidingResponses: GuidingResponse[], attemptNumber: number, scoreWeight: number) => void;
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
  const [submitState, setSubmitState] = useState<SubmitState>('idle');
  const [explanationOpen, setExplanationOpen] = useState(false);
  // MC guiding questions: track which option was chosen per guiding question id
  const [guidingSelections, setGuidingSelections] = useState<Record<string, string>>({});
  // Free-text guiding questions (fallback for questions without MC options)
  const [guidingTexts, setGuidingTexts] = useState<Record<string, string>>({});

  // ── Build guiding responses helper ───────────────────────────────────────
  const buildGuidingResponses = (): GuidingResponse[] =>
    question.guiding_questions.map(gq => ({
      guiding_question_id: gq.id,
      text_response: gq.options
        ? (guidingSelections[gq.id] ?? '')
        : (guidingTexts[gq.id] ?? ''),
    }));

  // ── Main answer submit (attempt 1) ────────────────────────────────────────
  const handleMCSubmit = () => {
    if (!selected) return;
    const isCorrect = selected === question.answer_key;
    if (isCorrect) {
      setSubmitState('submitted_correct');
      onAnswer(selected, buildGuidingResponses(), 1, 1.0);
    } else {
      setSubmitState('submitted_wrong_retry');
    }
  };

  // ── Retry submit (attempt 2) ──────────────────────────────────────────────
  const handleRetrySubmit = () => {
    if (!selected) return;
    const isCorrect = selected === question.answer_key;
    if (isCorrect) {
      setSubmitState('submitted_correct_retry');
      onAnswer(selected, buildGuidingResponses(), 2, 0.7);
    } else {
      setSubmitState('submitted_wrong_final');
      onAnswer(selected, buildGuidingResponses(), 2, 0.0);
    }
  };

  // ── Guiding MC select (auto-locks on first pick) ──────────────────────────
  const handleGuidingSelect = (gq: GuidingQuestion, key: string) => {
    if (guidingSelections[gq.id] !== undefined) return; // already answered
    setGuidingSelections(prev => ({ ...prev, [gq.id]: key }));
  };

  // ── Next / Finish button ──────────────────────────────────────────────────
  const handleNext = () => {
    if (!isLast) onNext();
  };

  // ── FRQ (unchanged) ───────────────────────────────────────────────────────
  const handleFRQComplete = (frqParts: FRQPartResponse[]) => {
    const allPassed = frqParts.every(p => p.passed);
    onAnswer(allPassed ? 'PASSED' : 'FAILED', [], 1, allPassed ? 1.0 : 0.0);
    if (!isLast) onNext();
  };

  // ── Option disabled logic ─────────────────────────────────────────────────
  const isOptionsDisabled = submitState !== 'idle' && submitState !== 'submitted_wrong_retry';

  // ── Option CSS class helper ───────────────────────────────────────────────
  const optionClass = (key: string) => {
    const classes = ['option'];
    if (selected === key) classes.push('selected');
    const isSubmitted = submitState !== 'idle' && submitState !== 'submitted_wrong_retry';
    if (isSubmitted && key === question.answer_key) classes.push('correct');
    if (isSubmitted && selected === key && key !== question.answer_key) classes.push('incorrect');
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

  // ── Derived booleans for rendering ───────────────────────────────────────
  const showNext =
    submitState === 'submitted_correct' ||
    submitState === 'submitted_correct_retry' ||
    submitState === 'submitted_wrong_final';

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
                  disabled={isOptionsDisabled}
                  checked={selected === key}
                  onChange={() => setSelected(key)}
                />
                <span className="option-key">{key}</span>
                <span className="option-text">{val}</span>
              </label>
            ))}
          </div>

          {/* ── Idle: Submit button ─────────────────────────────────────── */}
          {submitState === 'idle' && (
            <button
              className="btn-primary submit-btn"
              disabled={!selected}
              onClick={handleMCSubmit}
            >
              Submit Answer
            </button>
          )}

          {/* ── Attempt 1 correct ──────────────────────────────────────── */}
          {submitState === 'submitted_correct' && (
            <>
              <div className="feedback feedback-correct">✓ Correct!</div>

              {question.explanation && (
                <div>
                  <button
                    className="btn-explanation-toggle"
                    onClick={() => setExplanationOpen(o => !o)}
                  >
                    {explanationOpen ? 'Hide Explanation' : 'View Explanation'}
                  </button>
                  {explanationOpen && (
                    <div className="explanation-body">{question.explanation}</div>
                  )}
                </div>
              )}

              <button className="btn-next" onClick={handleNext}>
                {isLast ? 'Finish Quiz' : 'Next Question →'}
              </button>
            </>
          )}

          {/* ── Attempt 1 wrong — show guiding + Try Again ─────────────── */}
          {submitState === 'submitted_wrong_retry' && (
            <>
              <div className="feedback feedback-retry">↩ Not quite — take another look and try again.</div>

              {/* Guiding questions */}
              {question.guiding_questions.length > 0 && (
                <div className="guiding-questions">
                  <h4>Work through these to understand why</h4>
                  {question.guiding_questions.map((gq, gi) => (
                    <div key={gq.id} className="guiding-question">
                      <p className="guiding-prompt">
                        <span className="guiding-num">{gi + 1}.</span> {gq.text}
                      </p>
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

              <button
                className="btn-retry"
                disabled={!selected}
                onClick={handleRetrySubmit}
              >
                Try Again
              </button>
            </>
          )}

          {/* ── Attempt 2 correct — 70% credit ─────────────────────────── */}
          {submitState === 'submitted_correct_retry' && (
            <>
              <div className="feedback feedback-correct-retry">
                ✓ Correct on the second try — 70% credit
              </div>

              {question.explanation && (
                <div>
                  <button
                    className="btn-explanation-toggle"
                    onClick={() => setExplanationOpen(o => !o)}
                  >
                    {explanationOpen ? 'Hide Explanation' : 'View Explanation'}
                  </button>
                  {explanationOpen && (
                    <div className="explanation-body">{question.explanation}</div>
                  )}
                </div>
              )}

              <button className="btn-next" onClick={handleNext}>
                {isLast ? 'Finish Quiz' : 'Next Question →'}
              </button>
            </>
          )}

          {/* ── Attempt 2 wrong — forced explanation ────────────────────── */}
          {submitState === 'submitted_wrong_final' && (
            <>
              <div className="feedback feedback-incorrect">
                <div className="feedback-wrong-header">✗ Incorrect — the correct answer is {question.answer_key}</div>
                <div className="feedback-correct-text">
                  {question.options[question.answer_key]}
                </div>
              </div>

              {question.explanation && (
                <div className="explanation-body">{question.explanation}</div>
              )}

              <button className="btn-next" onClick={handleNext}>
                {isLast ? 'Finish Quiz' : 'Next Question →'}
              </button>
            </>
          )}

          {/* Safety net: Next button for any other final state (should not occur) */}
          {!showNext && submitState !== 'idle' && submitState !== 'submitted_wrong_retry' && (
            <button className="btn-next" onClick={handleNext}>
              {isLast ? 'Finish Quiz' : 'Next Question →'}
            </button>
          )}
        </>
      )}
    </div>
  );
}
