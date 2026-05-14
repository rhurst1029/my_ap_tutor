import { useState, useEffect } from 'react';
import TestRunner from '../TestRunner/TestRunner';
import { fetchTest } from '../../api';
import type { Test } from '../../types/test';
import { GUIDED_PLAN } from './guidedPlan';
import type { GuidedStage } from './guidedPlan';

interface Props {
  studentName: string;
  onExit: () => void;
}

const FRQ_STAGE_INDEX = GUIDED_PLAN.findIndex(s => s.kind === 'frq');

function fmt(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export default function GuidedPractice({ studentName, onExit }: Props) {
  const [stageIndex, setStageIndex] = useState(0);
  const [secondsLeft, setSecondsLeft] = useState(GUIDED_PLAN[0].durationMin * 60);
  const [timerRunning, setTimerRunning] = useState(true);

  // Per-stage checklist + writing state, keyed so they persist across nav.
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [writing, setWriting] = useState<Record<string, string>>({});

  // The embedded FRQ runner is mounted once visited and then kept alive
  // (display-toggled) so navigating away and back doesn't restart its session.
  const [frqVisited, setFrqVisited] = useState(false);
  const [frqTest, setFrqTest] = useState<Test | null>(null);
  const [frqError, setFrqError] = useState('');
  const [frqDone, setFrqDone] = useState(false);

  const stage: GuidedStage = GUIDED_PLAN[stageIndex];
  const isFirst = stageIndex === 0;
  const isLast = stageIndex === GUIDED_PLAN.length - 1;

  // Reset the countdown whenever the stage changes; auto-start it.
  useEffect(() => {
    setSecondsLeft(GUIDED_PLAN[stageIndex].durationMin * 60);
    setTimerRunning(true);
    if (stageIndex === FRQ_STAGE_INDEX) setFrqVisited(true);
  }, [stageIndex]);

  // Countdown tick — clamps at 0, never auto-advances (tutor controls pace).
  useEffect(() => {
    if (!timerRunning) return;
    const id = setInterval(() => {
      setSecondsLeft(s => (s <= 0 ? 0 : s - 1));
    }, 1000);
    return () => clearInterval(id);
  }, [timerRunning, stageIndex]);

  // Lazy-load the FRQ drill the first time the FRQ stage is reached.
  useEffect(() => {
    if (!frqVisited || frqTest) return;
    const testId = GUIDED_PLAN[FRQ_STAGE_INDEX].testId;
    if (!testId) return;
    fetchTest(testId)
      .then(setFrqTest)
      .catch(() => setFrqError('Could not load the FRQ drill. Make sure the backend is running.'));
  }, [frqVisited, frqTest]);

  const toggleCheck = (key: string) =>
    setChecked(c => ({ ...c, [key]: !c[key] }));

  const timeUp = secondsLeft === 0;
  const elapsedStages = stageIndex; // stages fully behind us
  const progressPct = (elapsedStages / GUIDED_PLAN.length) * 100;

  return (
    <div className="guided">
      {/* ── Header ──────────────────────────────────────────────── */}
      <div className="guided-header">
        <div className="guided-header-top">
          <span className="guided-kicker">
            Guided Practice · {studentName} · Stage {stageIndex + 1} of {GUIDED_PLAN.length}
          </span>
          <button className="guided-exit" onClick={onExit}>Exit</button>
        </div>
        <div className="guided-progress">
          <div className="guided-progress-fill" style={{ width: `${progressPct}%` }} />
        </div>
        <div className="guided-header-main">
          <div>
            <h2 className="guided-title">{stage.title}</h2>
            <span className="guided-timelabel">{stage.timeLabel}</span>
          </div>
          <div className={`guided-timer ${timeUp ? 'guided-timer-up' : ''}`}>
            <span className="guided-clock">{timeUp ? "Time's up" : fmt(secondsLeft)}</span>
            <div className="guided-timer-controls">
              <button onClick={() => setTimerRunning(r => !r)}>
                {timerRunning ? 'Pause' : 'Resume'}
              </button>
              <button onClick={() => { setSecondsLeft(stage.durationMin * 60); setTimerRunning(true); }}>
                Reset
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Stage body ──────────────────────────────────────────── */}
      <div className="guided-body">
        <p className="guided-purpose">{stage.purpose}</p>

        <ul className="guided-instructions">
          {stage.body.map((line, i) => <li key={i}>{line}</li>)}
        </ul>

        {stage.kind === 'writing' && (
          <div className="guided-writing">
            <label className="guided-writing-prompt">{stage.writingPrompt}</label>
            <textarea
              className="guided-writing-area"
              rows={8}
              placeholder="Start writing here…"
              value={writing[stage.id] ?? ''}
              onChange={e => setWriting(w => ({ ...w, [stage.id]: e.target.value }))}
            />
          </div>
        )}

        {stage.checklist && (
          <div className="guided-checklist">
            <span className="guided-checklist-label">Checklist</span>
            {stage.checklist.map((item, i) => {
              const key = `${stage.id}:${i}`;
              return (
                <label key={key} className={`guided-check ${checked[key] ? 'done' : ''}`}>
                  <input
                    type="checkbox"
                    checked={!!checked[key]}
                    onChange={() => toggleCheck(key)}
                  />
                  <span>{item}</span>
                </label>
              );
            })}
          </div>
        )}

        {stage.kind === 'break' && (
          <div className="guided-break-note">Take the full break. Come back refreshed.</div>
        )}
      </div>

      {/* ── Persistent embedded FRQ runner ──────────────────────── */}
      {frqVisited && (
        <div
          className="guided-frq-embed"
          style={{ display: stageIndex === FRQ_STAGE_INDEX ? 'block' : 'none' }}
        >
          {frqError && <div className="error">{frqError}</div>}
          {!frqError && !frqTest && <div className="guided-frq-loading">Loading FRQ drill…</div>}
          {frqTest && (
            <>
              {frqDone && (
                <div className="guided-frq-done">
                  ✓ FRQ drill complete — continue to the next stage when ready.
                </div>
              )}
              <TestRunner
                test={frqTest}
                studentName={studentName}
                sessionType="quiz"
                onComplete={() => setFrqDone(true)}
              />
            </>
          )}
        </div>
      )}

      {/* ── Nav ─────────────────────────────────────────────────── */}
      <div className="guided-nav">
        <button
          className="guided-nav-btn"
          disabled={isFirst}
          onClick={() => setStageIndex(i => Math.max(0, i - 1))}
        >
          ← Previous
        </button>
        <span className="guided-nav-dots">
          {GUIDED_PLAN.map((s, i) => (
            <span
              key={s.id}
              className={`guided-dot ${i === stageIndex ? 'active' : ''} ${i < stageIndex ? 'past' : ''}`}
            />
          ))}
        </span>
        {isLast ? (
          <button className="guided-nav-btn guided-nav-finish" onClick={onExit}>
            Finish ✓
          </button>
        ) : (
          <button
            className="guided-nav-btn guided-nav-next"
            onClick={() => setStageIndex(i => Math.min(GUIDED_PLAN.length - 1, i + 1))}
          >
            Next →
          </button>
        )}
      </div>
    </div>
  );
}
