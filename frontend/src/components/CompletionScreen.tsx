import type { QuestionResponse } from '../types/session';
import type { Test } from '../types/test';

interface SessionInfo {
  session_id: string;
  iteration: number;
  started_at: string;
}

interface Props {
  score: number;
  total: number;
  responses: QuestionResponse[];
  test: Test;
  studentName: string;
  sessionInfo: SessionInfo;
  onRetake: () => void;
}

const CONFIDENCE_THRESHOLDS = {
  confident: 0.67,   // < 67% of session average
  uncertain: 1.33,   // < 133% of session average
  // else: struggling
};

type ConfidenceLevel = 'confident' | 'uncertain' | 'struggling';

function getConfidence(time: number, average: number): ConfidenceLevel {
  const ratio = time / average;
  if (ratio < CONFIDENCE_THRESHOLDS.confident) return 'confident';
  if (ratio < CONFIDENCE_THRESHOLDS.uncertain) return 'uncertain';
  return 'struggling';
}

function formatTime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return s === 0 ? `${m}m` : `${m}m ${s}s`;
}

const CONFIDENCE_LABELS: Record<ConfidenceLevel, string> = {
  confident: 'Confident',
  uncertain: 'Uncertain',
  struggling: 'Struggling',
};

export default function CompletionScreen({
  score, total, responses, test, studentName, sessionInfo, onRetake,
}: Props) {
  const pct = Math.round((score / total) * 100);
  const avgTime = Math.round(responses.reduce((s, r) => s + r.time_spent_seconds, 0) / responses.length);

  // Build per-question detail rows
  const rows = responses.map(r => {
    const q = test.questions.find(q => q.id === r.question_id)!;
    const conf = getConfidence(r.time_spent_seconds, avgTime);
    return { r, q, conf };
  });

  // Topic summary
  const topicMap: Record<string, { correct: number; total: number; totalTime: number }> = {};
  for (const { r, q } of rows) {
    for (const tag of q.topic_tags) {
      if (!topicMap[tag]) topicMap[tag] = { correct: 0, total: 0, totalTime: 0 };
      topicMap[tag].total++;
      topicMap[tag].totalTime += r.time_spent_seconds;
      if (r.is_correct) topicMap[tag].correct++;
    }
  }
  const topics = Object.entries(topicMap).map(([tag, stats]) => ({
    tag,
    ...stats,
    avgTime: Math.round(stats.totalTime / stats.total),
    conf: getConfidence(Math.round(stats.totalTime / stats.total), avgTime),
  })).sort((a, b) => b.avgTime - a.avgTime);

  return (
    <div className="completion-screen">
      <div className="completion-header">
        <h1>Session Complete</h1>
        <p className="student-name">{studentName} — Session {sessionInfo.iteration}</p>
        <div className="score-display">
          <span className="score-big">{score}/{total}</span>
          <span className="score-pct">{pct}%</span>
        </div>
        <p className="avg-time">Average time per question: {formatTime(avgTime)}</p>
      </div>

      <div className="topic-summary">
        <h3>Topic Breakdown</h3>
        <table>
          <thead>
            <tr>
              <th>Topic</th>
              <th>Score</th>
              <th>Avg Time</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {topics.map(t => (
              <tr key={t.tag}>
                <td>{t.tag.replace(/_/g, ' ')}</td>
                <td>{t.correct}/{t.total}</td>
                <td>{formatTime(t.avgTime)}</td>
                <td>
                  <span className={`conf-badge conf-${t.conf}`}>
                    {CONFIDENCE_LABELS[t.conf]}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="question-breakdown">
        <h3>Question by Question</h3>
        {rows.map(({ r, q, conf }, i) => (
          <div key={r.question_id} className={`q-row ${r.is_correct ? 'correct' : 'incorrect'}`}>
            <div className="q-row-left">
              <span className="q-num">Q{i + 1}</span>
              <span className={`q-result ${r.is_correct ? 'correct' : 'incorrect'}`}>
                {r.is_correct ? '✓' : '✗'}
              </span>
              <span className="q-topic">{q.topic_tags.join(', ').replace(/_/g, ' ')}</span>
            </div>
            <div className="q-row-right">
              <span className="q-time">{formatTime(r.time_spent_seconds)}</span>
              <span className={`conf-badge conf-${conf}`}>{CONFIDENCE_LABELS[conf]}</span>
            </div>
          </div>
        ))}
      </div>

      <button className="btn-primary retake-btn" onClick={onRetake}>
        Take Another Test
      </button>
    </div>
  );
}
