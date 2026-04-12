import { useState } from 'react';
import { fetchHistory } from '../api';
import type { SessionMetadata } from '../types/session';

interface Props {
  onStart: (name: string) => void;
}

export default function NameEntry({ onStart }: Props) {
  const [name, setName] = useState('');
  const [history, setHistory] = useState<SessionMetadata[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const lookup = async () => {
    if (!name.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await fetchHistory(name.trim());
      setHistory(data.sessions);
    } catch {
      // New student — no history
      setHistory([]);
    } finally {
      setLoading(false);
    }
  };

  const completedSessions = history?.filter(s => s.completed) ?? [];
  const resumable = history?.find(s => !s.completed);
  const isReturning = completedSessions.length > 0;

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') lookup();
  };

  return (
    <div className="name-entry">
      <h1>AP Computer Science A</h1>
      <p className="subtitle">Adaptive Practice Platform</p>

      <div className="name-form">
        <input
          type="text"
          placeholder="Enter your first name"
          value={name}
          onChange={e => setName(e.target.value)}
          onKeyDown={handleKeyDown}
          autoFocus
        />
        <button onClick={lookup} disabled={loading || !name.trim()}>
          {loading ? 'Looking up…' : 'Continue'}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {history !== null && (
        <div className="history-panel">
          {isReturning ? (
            <>
              <p>Welcome back, <strong>{name.trim()}</strong>!</p>
              <p className="history-sub">
                Sessions completed: {completedSessions.length} &nbsp;|&nbsp;
                Last score: {completedSessions[completedSessions.length - 1]?.total_questions ?? '—'}
              </p>
              {resumable && (
                <div className="resume-notice">
                  <p>You have an unfinished session. Would you like to resume it?</p>
                  <div className="btn-row">
                    <button className="btn-primary" onClick={() => onStart(name.trim())}>
                      Resume Session {resumable.iteration}
                    </button>
                    <button className="btn-secondary" onClick={() => onStart(name.trim())}>
                      Start New Test
                    </button>
                  </div>
                </div>
              )}
              {!resumable && (
                <button className="btn-primary" onClick={() => onStart(name.trim())}>
                  Take Next Test
                </button>
              )}
            </>
          ) : (
            <>
              <p>Hi <strong>{name.trim()}</strong>, let's get started!</p>
              <button className="btn-primary" onClick={() => onStart(name.trim())}>
                Begin Test
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
