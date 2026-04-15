import type { Test } from './types/test';
import type { SessionSaveRequest, SessionMetadata } from './types/session';

const BASE = 'http://localhost:8000/api';

export async function fetchTest(testId: string): Promise<Test> {
  const res = await fetch(`${BASE}/tests/${testId}`);
  if (!res.ok) throw new Error('Failed to load test');
  return res.json();
}

export async function startSession(
  studentName: string,
  testId: string,
  totalQuestions: number
): Promise<{ session_id: string; iteration: number }> {
  const res = await fetch(`${BASE}/sessions/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_name: studentName, test_id: testId, total_questions: totalQuestions }),
  });
  if (!res.ok) throw new Error('Failed to start session');
  return res.json();
}

export async function saveSession(payload: SessionSaveRequest): Promise<void> {
  const res = await fetch(`${BASE}/sessions/${payload.student_name}/${payload.session_id}/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to save session');
}

export async function fetchHistory(studentName: string): Promise<{ sessions: SessionMetadata[]; reports: unknown[] }> {
  const res = await fetch(`${BASE}/sessions/${encodeURIComponent(studentName)}/history`);
  if (!res.ok) throw new Error('Failed to fetch history');
  return res.json();
}

export async function fetchNextTest(studentName: string): Promise<{ test_id: string; iteration: number }> {
  const res = await fetch(`${BASE}/sessions/${encodeURIComponent(studentName)}/next-test`);
  if (!res.ok) throw new Error('Failed to fetch next test');
  return res.json();
}
