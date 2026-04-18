import { useState, useEffect, useRef, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import type { OnMount } from '@monaco-editor/react';
import type { editor } from 'monaco-editor';
import './TakeHome.css';

// ── Types ────────────────────────────────────────────────────────────────────

interface TestCase {
  id: string;
  description: string;
  method_call: string;
  expected_output: string;
  what_it_tests: string;
  wrong_means: string;
}

interface VariantSummary {
  what_this_tests: string;
  why: string;
  concept_background: string;
}

interface Variant {
  id: string;
  parent_question: string;
  mutation_description: string;
  concept_tested: string;
  difficulty: string;
  topic_tags: string[];
  starter_modification: string;
  test_cases: TestCase[];
  summary: VariantSummary;
  metadata: {
    started_at: string | null;
    completed_at: string | null;
    total_time_ms: number | null;
    run_attempts: unknown[];
    test_results: unknown[];
  };
}

interface QuestionMeta {
  id: string;
  title: string;
  topic_tags: string[];
  priority: string;
  difficulty: string;
  variants: string[];
  directory: string;
}

interface Manifest {
  student: string;
  session: number;
  generated_at: string;
  total_questions: number;
  questions: QuestionMeta[];
}

interface TestResult {
  tc_id: string;
  passed: boolean;
  actual: string;
  expected: string;
  time_ms: number;
}

// ── Constants ────────────────────────────────────────────────────────────────

const API_BASE = 'http://localhost:8000/api';
const TAKEHOME_API = `${API_BASE}/takehome`;
const VISUALIZER_BASE = 'https://cscircles.cemc.uwaterloo.ca/java_visualize/';

// ── Component ────────────────────────────────────────────────────────────────

interface Props {
  manifestPath: string;
  basePath: string;
}

export default function TakeHomeRunner({ manifestPath, basePath }: Props) {
  // State
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [variantIndex, setVariantIndex] = useState(0);
  const [code, setCode] = useState('');
  const [variant, setVariant] = useState<Variant | null>(null);
  const [javaTemplate, setJavaTemplate] = useState('');
  const [running, setRunning] = useState(false);
  const [stdout, setStdout] = useState('');
  const [stderr, setStderr] = useState('');
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [showVisualizer, setShowVisualizer] = useState(false);
  const [activePanel, setActivePanel] = useState<'tests' | 'visualizer' | 'info'>('tests');
  const [startTime, setStartTime] = useState<number>(Date.now());

  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

  // ── Load manifest ─────────────────────────────────────────────────────────
  useEffect(() => {
    fetch(`${TAKEHOME_API}/${manifestPath}`)
      .then(r => r.json())
      .then(setManifest)
      .catch(e => console.error('Failed to load manifest:', e));
  }, [manifestPath]);

  // ── Load question + variant ───────────────────────────────────────────────
  const loadQuestion = useCallback(async (qIdx: number, vIdx: number) => {
    if (!manifest) return;
    const q = manifest.questions[qIdx];

    // Load Java template
    const javaRes = await fetch(`${TAKEHOME_API}/${basePath}/${q.directory}/${q.id}.java`);
    const javaText = await javaRes.text();
    setJavaTemplate(javaText);
    setCode(javaText);

    // Load variant
    const variantId = q.variants[vIdx];
    const varRes = await fetch(`${TAKEHOME_API}/${basePath}/${q.directory}/${variantId}.json`);
    const varData: Variant = await varRes.json();
    setVariant(varData);

    // Reset state
    setStdout('');
    setStderr('');
    setTestResults([]);
    setStartTime(Date.now());
    setShowVisualizer(false);
    setActivePanel('tests');
  }, [manifest, basePath]);

  useEffect(() => {
    if (manifest) loadQuestion(questionIndex, variantIndex);
  }, [manifest, questionIndex, variantIndex, loadQuestion]);

  // ── Run code ──────────────────────────────────────────────────────────────
  const handleRun = async () => {
    setRunning(true);
    setStdout('');
    setStderr('');
    try {
      const res = await fetch(`${API_BASE}/execute/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_code: code }),
      });
      const data = await res.json();
      setStdout(data.stdout || '');
      setStderr(data.stderr || data.compile_errors?.join('\n') || '');
    } catch {
      setStderr('Could not reach execution server. Is the backend running?');
    }
    setRunning(false);
  };

  // ── Run test cases ────────────────────────────────────────────────────────
  const handleRunTests = async () => {
    if (!variant) return;
    setRunning(true);
    setActivePanel('tests');
    const results: TestResult[] = [];

    for (const tc of variant.test_cases) {
      // Build the main() body for this test case.
      // Rules:
      //   1. If method_call already ends with `;`, use as-is (full statement).
      //   2. If it starts with System.out.print(...), just append `;`.
      //   3. If the method is declared `void` in the code, call bare + `;`.
      //   4. Otherwise wrap in System.out.println(...) to capture the return value.
      const startsWithPrint = /^\s*System\.out\.(print|println)/.test(tc.method_call);
      const callAlreadyStatement = /;\s*$/.test(tc.method_call);
      const methodNameMatch = tc.method_call.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(/);
      const methodName = methodNameMatch?.[1];
      const voidRegex = methodName
        ? new RegExp(`\\bstatic\\s+void\\s+${methodName}\\b`)
        : null;
      const isVoid = voidRegex ? voidRegex.test(code) : false;

      const mainBody = callAlreadyStatement
        ? tc.method_call
        : startsWithPrint
          ? `${tc.method_call};`
          : isVoid
            ? `${tc.method_call};`
            : `System.out.println(${tc.method_call});`;

      const testCode = code.replace(
        /public static void main\(String\[\] args\)\s*\{[\s\S]*?\n\s*\}/,
        `public static void main(String[] args) {\n        ${mainBody}\n    }`
      );

      const start = Date.now();
      try {
        const res = await fetch(`${API_BASE}/execute/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source_code: testCode }),
        });
        const data = await res.json();
        const actual = (data.stdout || '').trim();
        results.push({
          tc_id: tc.id,
          passed: actual === tc.expected_output.trim(),
          actual: data.stderr ? `ERROR: ${data.stderr}` : actual,
          expected: tc.expected_output,
          time_ms: Date.now() - start,
        });
      } catch {
        results.push({
          tc_id: tc.id,
          passed: false,
          actual: 'Execution failed',
          expected: tc.expected_output,
          time_ms: Date.now() - start,
        });
      }
    }

    setTestResults(results);
    setRunning(false);
  };

  // ── Visualizer ────────────────────────────────────────────────────────────
  const visualizerUrl = () => {
    const encoded = encodeURIComponent(code);
    return `${VISUALIZER_BASE}#code=${encoded}&mode=display&cumulative=false&heapPrimitives=false&drawRef=false&textReferences=false&showOnlyOutputs=false&py=3`;
  };

  // ── Editor mount ──────────────────────────────────────────────────────────
  const handleEditorMount: OnMount = (editorInstance) => {
    editorRef.current = editorInstance;
  };

  // ── Navigation ────────────────────────────────────────────────────────────
  const goToQuestion = (qIdx: number) => {
    setQuestionIndex(qIdx);
    setVariantIndex(0);
  };

  const goToVariant = (vIdx: number) => {
    setVariantIndex(vIdx);
  };

  // ── Derived ───────────────────────────────────────────────────────────────
  if (!manifest || !variant) {
    return <div className="takehome-loading">Loading assignment...</div>;
  }

  const currentQ = manifest.questions[questionIndex];
  const passedAll = testResults.length > 0 && testResults.every(r => r.passed);
  const elapsedSec = Math.round((Date.now() - startTime) / 1000);

  return (
    <div className="takehome">
      {/* ── Sidebar: Question List ─────────────────────────────────────────── */}
      <aside className="takehome-sidebar">
        <div className="takehome-sidebar-header">
          <h2>Session 6 Take-Home</h2>
          <span className="takehome-student">{manifest.student}</span>
        </div>
        <nav className="takehome-nav">
          {manifest.questions.map((q, i) => (
            <button
              key={q.id}
              className={`takehome-nav-item ${i === questionIndex ? 'active' : ''}`}
              onClick={() => goToQuestion(i)}
            >
              <span className="nav-id">{q.id}</span>
              <span className="nav-title">{q.title}</span>
              <span className={`nav-priority priority-${q.priority.toLowerCase()}`}>
                {q.priority}
              </span>
            </button>
          ))}
        </nav>
      </aside>

      {/* ── Main Area ──────────────────────────────────────────────────────── */}
      <main className="takehome-main">
        {/* Question header */}
        <header className="takehome-header">
          <div className="takehome-header-left">
            <h3>{currentQ.id}: {currentQ.title}</h3>
            <div className="takehome-tags">
              {currentQ.topic_tags.map(t => (
                <span key={t} className="tag">{t}</span>
              ))}
              <span className={`tag tag-difficulty tag-${currentQ.difficulty}`}>
                {currentQ.difficulty}
              </span>
            </div>
          </div>
          <div className="takehome-variants">
            {currentQ.variants.map((v, i) => (
              <button
                key={v}
                className={`variant-tab ${i === variantIndex ? 'active' : ''}`}
                onClick={() => goToVariant(i)}
              >
                {v}
              </button>
            ))}
          </div>
        </header>

        {/* Mutation description */}
        <div className="takehome-mutation">
          <span className="mutation-label">Task:</span>
          <p>{variant.mutation_description}</p>
          <p className="mutation-hint">{variant.starter_modification}</p>
        </div>

        {/* Editor + Panels layout */}
        <div className="takehome-workspace">
          {/* Code editor */}
          <div className="takehome-editor-container">
            <div className="editor-toolbar">
              <button className="btn-run-code" onClick={handleRun} disabled={running}>
                {running ? 'Running…' : '▶ Run Code'}
              </button>
              <button
                className={`btn-panel ${activePanel === 'tests' ? 'active' : ''}`}
                onClick={handleRunTests}
                disabled={running}
              >
                {running ? 'Testing…' : '🧪 Tests'}
              </button>
              <button
                className={`btn-panel btn-visualize ${activePanel === 'visualizer' ? 'active' : ''}`}
                onClick={() => { setShowVisualizer(true); setActivePanel('visualizer'); }}
              >
                🔬 Visualize
              </button>
              <button
                className={`btn-panel ${activePanel === 'info' ? 'active' : ''}`}
                onClick={() => setActivePanel('info')}
              >
                📖 Info
              </button>
              <button className="btn-reset" onClick={() => setCode(javaTemplate)}>
                ↺ Reset
              </button>
            </div>
            <Editor
              height="calc(100vh - 320px)"
              defaultLanguage="java"
              value={code}
              theme="vs-dark"
              onMount={handleEditorMount}
              onChange={(v) => setCode(v ?? '')}
              options={{
                fontSize: 14,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                lineNumbers: 'on',
                renderLineHighlight: 'line',
                wordWrap: 'on',
                glyphMargin: true,
              }}
            />
            {/* Terminal output */}
            {(stdout || stderr) && (
              <div className="takehome-terminal">
                <div className="terminal-header">
                  <span>Terminal Output</span>
                </div>
                {stdout && <pre className="terminal-stdout">{stdout}</pre>}
                {stderr && <pre className="terminal-stderr">{stderr}</pre>}
              </div>
            )}
          </div>

          {/* Right panel */}
          <div className="takehome-panel">
            <div className="panel-title-bar">
              {activePanel === 'tests' && <span>🧪 Test Cases</span>}
              {activePanel === 'visualizer' && <span>🔬 Environment Diagram</span>}
              {activePanel === 'info' && <span>📖 Concept Info</span>}
            </div>

            {/* Tests panel */}
            {activePanel === 'tests' && (
              <div className="panel-content panel-tests">
                <h4>Test Cases ({variant.test_cases.length})</h4>
                {variant.test_cases.map((tc, i) => {
                  const result = testResults.find(r => r.tc_id === tc.id);
                  return (
                    <div key={tc.id} className={`test-case ${result ? (result.passed ? 'passed' : 'failed') : ''}`}>
                      <div className="tc-header">
                        <span className="tc-num">Test {i + 1}</span>
                        {result && (
                          <span className={`tc-badge ${result.passed ? 'pass' : 'fail'}`}>
                            {result.passed ? '✓ PASS' : '✗ FAIL'}
                          </span>
                        )}
                      </div>
                      <p className="tc-desc">{tc.description}</p>
                      <div className="tc-code">
                        <code>{tc.method_call}</code>
                      </div>
                      <div className="tc-expected">
                        <span>Expected:</span> <code>{tc.expected_output}</code>
                      </div>
                      {result && !result.passed && (
                        <div className="tc-actual">
                          <span>Got:</span> <code>{result.actual}</code>
                        </div>
                      )}
                      {result && !result.passed && (
                        <div className="tc-hint">
                          <span>💡</span> {tc.wrong_means}
                        </div>
                      )}
                      <p className="tc-tests-for">{tc.what_it_tests}</p>
                    </div>
                  );
                })}
                {passedAll && (
                  <div className="all-passed-banner">
                    ✅ All tests passed! Try the next variant or question.
                  </div>
                )}
              </div>
            )}

            {/* Visualizer panel */}
            {activePanel === 'visualizer' && (
              <div className="panel-content panel-visualizer">
                <div className="visualizer-controls">
                  <button
                    className="btn-load-viz"
                    onClick={() => setShowVisualizer(true)}
                  >
                    Load current code into visualizer
                  </button>
                  <a
                    href={visualizerUrl()}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-open-external"
                  >
                    Open in new tab ↗
                  </a>
                </div>
                {showVisualizer && (
                  <iframe
                    className="visualizer-frame"
                    src={visualizerUrl()}
                    title="Java Visualizer"
                    sandbox="allow-scripts allow-same-origin allow-popups"
                  />
                )}
              </div>
            )}

            {/* Info panel */}
            {activePanel === 'info' && (
              <div className="panel-content panel-info">
                <h4>What This Tests</h4>
                <p>{variant.summary.what_this_tests}</p>

                <h4>Why This Matters</h4>
                <p>{variant.summary.why}</p>

                <h4>Concept Background</h4>
                <p className="info-background">{variant.summary.concept_background}</p>

                <h4>Concept Tested</h4>
                <p>{variant.concept_tested}</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
