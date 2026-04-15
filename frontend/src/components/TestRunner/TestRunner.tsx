import { useState, useEffect, useRef } from 'react';
import type { Test, Question } from '../../types/test';
import type { QuestionResponse } from '../../types/session';
import { startSession, saveSession } from '../../api';
import QuestionCard from './QuestionCard';

interface GuidingResponse {
  guiding_question_id: string;
  text_response: string;
}

interface SessionInfo {
  session_id: string;
  iteration: number;
  started_at: string;
}

interface CompletionResult {
  score: number;        // weighted: sum of score_weight values
  rawCorrect: number;   // unweighted: how many they eventually got right
  total: number;
  responses: QuestionResponse[];
  test: Test;
  studentName: string;
  sessionInfo: SessionInfo;
}

interface Props {
  test: Test;
  studentName: string;
  onComplete: (result: CompletionResult) => void;
}

export default function TestRunner({ test, studentName, onComplete }: Props) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [error, setError] = useState('');

  // Keep responses in a ref so handleAnswer/handleNext always see the latest
  // value without stale closure issues.
  const responsesRef = useRef<QuestionResponse[]>([]);
  const questionStartTime = useRef<number>(Date.now());

  useEffect(() => {
    const started_at = new Date().toISOString();
    startSession(studentName, test.test_id, test.questions.length)
      .then(({ session_id, iteration }) => {
        setSessionInfo({ session_id, iteration, started_at });
      })
      .catch(() => setError('Could not start session. Is the backend running?'));
  }, []);

  useEffect(() => {
    questionStartTime.current = Date.now();
  }, [currentIndex]);

  // Called when the student clicks "Next" (or "Finish" on the last question).
  // Receives the final guiding responses so they're recorded after the student
  // has had a chance to answer the reflection MC questions.
  const handleAnswer = async (answer: string, guidingResponses: GuidingResponse[], attemptNumber: number, scoreWeight: number) => {
    if (!sessionInfo) return;

    const question: Question = test.questions[currentIndex];
    const timeSpent = Math.round((Date.now() - questionStartTime.current) / 1000);

    const response: QuestionResponse = {
      question_id: question.id,
      question_type: question.type,
      selected_answer: answer,
      frq_parts: [],
      is_correct: scoreWeight > 0,
      attempt_number: attemptNumber,
      score_weight: scoreWeight,
      time_spent_seconds: timeSpent,
      guiding_question_responses: guidingResponses.map(gr => ({
        guiding_question_id: gr.guiding_question_id,
        text_response: gr.text_response || null,
        audio_file: null,
        transcript: null,
        transcript_confidence: null,
      })),
    };

    const updated = [...responsesRef.current, response];
    responsesRef.current = updated;

    const isLast = currentIndex === test.questions.length - 1;

    if (isLast) {
      const completed_at = new Date().toISOString();
      try {
        await saveSession({
          session_id: sessionInfo.session_id,
          student_name: studentName,
          test_id: test.test_id,
          iteration: sessionInfo.iteration,
          started_at: sessionInfo.started_at,
          completed_at,
          responses: updated,
        });
      } catch {
        // Non-fatal — still show results
      }
      const weightedScore = parseFloat(updated.reduce((sum, r) => sum + r.score_weight, 0).toFixed(1));
      const rawCorrect = updated.filter(r => r.is_correct).length;
      onComplete({
        score: weightedScore,
        rawCorrect,
        total: test.questions.length,
        responses: updated,
        test,
        studentName,
        sessionInfo,
      });
    }
  };

  // Called by QuestionCard "Next Question" button on non-final questions.
  const handleNext = () => {
    setCurrentIndex(i => i + 1);
  };

  if (error) return <div className="error-screen">{error}</div>;
  if (!sessionInfo) return <div className="loading">Starting session…</div>;

  const question = test.questions[currentIndex];
  const isLast = currentIndex === test.questions.length - 1;

  return (
    <div className="test-runner">
      <div className="test-header">
        <h2>{test.title}</h2>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${(currentIndex / test.questions.length) * 100}%` }}
          />
        </div>
      </div>
      <QuestionCard
        key={question.id}
        question={question}
        index={currentIndex}
        total={test.questions.length}
        isLast={isLast}
        onAnswer={handleAnswer}
        onNext={handleNext}
      />
    </div>
  );
}
