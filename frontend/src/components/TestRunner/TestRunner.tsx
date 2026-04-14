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
  score: number;
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
  const [responses, setResponses] = useState<QuestionResponse[]>([]);
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [error, setError] = useState('');
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

  const handleAnswer = async (answer: string, guidingResponses: GuidingResponse[]) => {
    if (!sessionInfo) return;

    const question: Question = test.questions[currentIndex];
    const timeSpent = Math.round((Date.now() - questionStartTime.current) / 1000);

    const response: QuestionResponse = {
      question_id: question.id,
      question_type: question.type,
      selected_answer: answer,
      frq_parts: [],
      is_correct: answer === question.answer_key,
      time_spent_seconds: timeSpent,
      guiding_question_responses: guidingResponses.map(gr => ({
        guiding_question_id: gr.guiding_question_id,
        text_response: gr.text_response || null,
        audio_file: null,
        transcript: null,
        transcript_confidence: null,
      })),
    };

    const updatedResponses = [...responses, response];
    setResponses(updatedResponses);

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
          responses: updatedResponses,
        });
      } catch {
        // Non-fatal — still show results
      }
      const score = updatedResponses.filter(r => r.is_correct).length;
      onComplete({
        score,
        total: test.questions.length,
        responses: updatedResponses,
        test,
        studentName,
        sessionInfo,
      });
    } else {
      setTimeout(() => setCurrentIndex(i => i + 1), 800);
    }
  };

  if (error) return <div className="error-screen">{error}</div>;
  if (!sessionInfo) return <div className="loading">Starting session…</div>;

  const question = test.questions[currentIndex];

  return (
    <div className="test-runner">
      <div className="test-header">
        <h2>{test.title}</h2>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${((currentIndex) / test.questions.length) * 100}%` }}
          />
        </div>
      </div>
      <QuestionCard
        key={question.id}
        question={question}
        index={currentIndex}
        total={test.questions.length}
        onAnswer={handleAnswer}
      />
    </div>
  );
}
