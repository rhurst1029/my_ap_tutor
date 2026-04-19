import { useState, useRef, useEffect, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import type { OnMount, OnChange } from '@monaco-editor/react';
import type { editor } from 'monaco-editor';
import type { FRQPart } from '../../types/test';
import type { FRQPartResponse, FRQRunAttempt } from '../../types/session';

interface Props {
  questionId: string;
  parts: FRQPart[];
  onComplete: (responses: FRQPartResponse[]) => void;
}

interface PartState {
  code: string;
  runAttempts: FRQRunAttempt[];
  compileErrorsSeen: Set<string>;
  lineTimeMap: Record<string, number>;
  lineEditCounts: Record<string, number>;
  startTime: number;
  firstKeystrokeTime: number | null;
  running: boolean;
  currentOutput: string;
  currentError: string;
  lastPassed: boolean;
  done: boolean;
}

function initPartState(starterCode: string): PartState {
  return {
    code: starterCode,
    runAttempts: [],
    compileErrorsSeen: new Set(),
    lineTimeMap: {},
    lineEditCounts: {},
    startTime: Date.now(),
    firstKeystrokeTime: null,
    running: false,
    currentOutput: '',
    currentError: '',
    lastPassed: false,
    done: false,
  };
}

export default function FRQCard({ parts, onComplete }: Props) {
  const [partIndex, setPartIndex] = useState(0);
  const [states, setStates] = useState<PartState[]>(() => parts.map(p => initPartState(p.starter_code)));
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const cursorLineRef = useRef<number>(1);
  const lineTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const completedParts = useRef<FRQPartResponse[]>([]);

  const part = parts[partIndex];
  const state = states[partIndex];

  // ── Line-time tracking ──────────────────────────────────────────────────────
  const startLineTimer = useCallback(() => {
    if (lineTimerRef.current) clearInterval(lineTimerRef.current);
    lineTimerRef.current = setInterval(() => {
      const line = String(cursorLineRef.current);
      setStates(prev => {
        const next = [...prev];
        const s = { ...next[partIndex] };
        s.lineTimeMap = { ...s.lineTimeMap, [line]: (s.lineTimeMap[line] ?? 0) + 1 };
        next[partIndex] = s;
        return next;
      });
    }, 1000);
  }, [partIndex]);

  useEffect(() => {
    startLineTimer();
    return () => { if (lineTimerRef.current) clearInterval(lineTimerRef.current); };
  }, [partIndex, startLineTimer]);

  const handleEditorMount: OnMount = (editorInstance) => {
    editorRef.current = editorInstance;

    editorInstance.onDidChangeCursorPosition(e => {
      cursorLineRef.current = e.position.lineNumber;
    });
  };

  const handleCodeChange: OnChange = (value) => {
    const line = String(cursorLineRef.current);
    setStates(prev => {
      const next = [...prev];
      const s = { ...next[partIndex] };
      s.code = value ?? s.code;
      s.lineEditCounts = { ...s.lineEditCounts, [line]: (s.lineEditCounts[line] ?? 0) + 1 };
      if (s.firstKeystrokeTime === null) s.firstKeystrokeTime = Date.now();
      next[partIndex] = s;
      return next;
    });
  };

  // ── Run code ────────────────────────────────────────────────────────────────
  const handleRun = async () => {
    setStates(prev => {
      const next = [...prev];
      next[partIndex] = { ...next[partIndex], running: true };
      return next;
    });

    const timestamp = new Date().toISOString();
    const currentCode = states[partIndex].code;

    try {
      const res = await fetch('http://localhost:8000/api/execute/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_code: currentCode }),
      });
      const data = await res.json();

      const attemptNumber = states[partIndex].runAttempts.length + 1;
      const passed = data.passed && data.stdout.trim() !== '';

      const attempt: FRQRunAttempt = {
        attempt_number: attemptNumber,
        code_snapshot: currentCode,
        stdout: data.stdout,
        stderr: data.stderr,
        compile_errors: data.compile_errors,
        passed,
        timestamp,
      };

      setStates(prev => {
        const next = [...prev];
        const s = { ...next[partIndex] };
        s.running = false;
        s.currentOutput = data.stdout;
        s.currentError = data.stderr || data.compile_errors.join('\n');
        s.lastPassed = passed;
        s.runAttempts = [...s.runAttempts, attempt];
        s.compileErrorsSeen = new Set([...s.compileErrorsSeen, ...data.compile_errors]);
        next[partIndex] = s;
        return next;
      });
    } catch {
      setStates(prev => {
        const next = [...prev];
        next[partIndex] = {
          ...next[partIndex],
          running: false,
          currentError: 'Could not reach execution server.',
        };
        return next;
      });
    }
  };

  // ── Submit part ─────────────────────────────────────────────────────────────
  const handleSubmitPart = () => {
    if (lineTimerRef.current) clearInterval(lineTimerRef.current);
    const s = state;
    const totalTime = Math.round((Date.now() - s.startTime) / 1000);
    const ttfk = s.firstKeystrokeTime
      ? Math.round((s.firstKeystrokeTime - s.startTime) / 1000)
      : totalTime;

    // Flag lines with above-average time or high edit count
    const timeValues = Object.values(s.lineTimeMap);
    const avgTime = timeValues.length ? timeValues.reduce((a, b) => a + b, 0) / timeValues.length : 0;
    const struggled = Object.entries(s.lineTimeMap)
      .filter(([, t]) => t > avgTime * 1.5)
      .map(([l]) => parseInt(l));

    const response: FRQPartResponse = {
      part: part.part,
      final_code: s.code,
      passed: s.lastPassed,
      total_runs: s.runAttempts.length,
      total_time_seconds: totalTime,
      time_to_first_keystroke_seconds: ttfk,
      run_attempts: s.runAttempts,
      compile_errors_encountered: [...s.compileErrorsSeen],
      line_time_map: s.lineTimeMap,
      line_edit_counts: s.lineEditCounts,
      struggled_lines: struggled,
    };

    completedParts.current = [...completedParts.current, response];

    if (partIndex < parts.length - 1) {
      setPartIndex(i => i + 1);
    } else {
      onComplete(completedParts.current);
    }
  };

  const expectedOutput = part.test_cases[0]?.expected_output ?? '';

  return (
    <div className="frq-card">
      {parts.length > 1 && (
        <div className="frq-parts-nav">
          {parts.map((p, i) => (
            <span key={p.part} className={`frq-part-tab ${i === partIndex ? 'active' : ''} ${i < partIndex ? 'done' : ''}`}>
              Part {p.part.toUpperCase()}
            </span>
          ))}
        </div>
      )}

      <div className="frq-part-header">
        <span className="frq-points">{part.points} points</span>
        <p className="frq-description">{part.description}</p>
      </div>

      <div className="frq-editor">
        <Editor
          height="calc(100vh - 280px)"
          defaultLanguage="java"
          value={state.code}
          theme="vs-dark"
          onMount={handleEditorMount}
          onChange={handleCodeChange}
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            lineNumbers: 'on',
            renderLineHighlight: 'line',
            wordWrap: 'on',
          }}
        />
      </div>

      <div className="frq-controls">
        <button className="btn-run" onClick={handleRun} disabled={state.running}>
          {state.running ? 'Running…' : '▶ Run'}
        </button>
        <button
          className="btn-primary"
          onClick={handleSubmitPart}
          disabled={state.runAttempts.length === 0}
        >
          {partIndex < parts.length - 1 ? `Submit Part ${part.part.toUpperCase()} →` : 'Submit FRQ'}
        </button>
      </div>

      {(state.currentOutput || state.currentError) && (
        <div className="frq-output">
          <div className="frq-output-header">
            <span>Output</span>
            {expectedOutput && (
              <span className={`frq-verdict ${state.lastPassed ? 'passed' : 'failed'}`}>
                {state.lastPassed ? '✓ Matches expected' : '✗ Does not match expected'}
              </span>
            )}
          </div>
          {state.currentOutput && (
            <pre className={`frq-stdout ${state.lastPassed ? 'correct' : ''}`}>{state.currentOutput}</pre>
          )}
          {state.currentError && (
            <pre className="frq-stderr">{state.currentError}</pre>
          )}
          {expectedOutput && !state.lastPassed && (
            <div className="frq-expected">
              <span>Expected:</span>
              <pre>{expectedOutput}</pre>
            </div>
          )}
        </div>
      )}

      <p className="frq-run-hint">
        {state.runAttempts.length === 0
          ? 'Run your code at least once before submitting.'
          : `${state.runAttempts.length} run${state.runAttempts.length > 1 ? 's' : ''} so far`}
      </p>
    </div>
  );
}
