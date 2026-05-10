import { useState, useEffect } from 'react';
import NameEntry from './components/NameEntry';
import TestRunner from './components/TestRunner/TestRunner';
import CompletionScreen from './components/CompletionScreen';
import TakeHomeRunner from './components/TakeHome/TakeHomeRunner';
import { fetchTest, fetchNextTest } from './api';
import type { Test } from './types/test';
import type { QuestionResponse } from './types/session';
import './App.css';

type Screen = 'name-entry' | 'loading' | 'test' | 'complete' | 'takehome';

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

export default function App() {
  const [screen, setScreen] = useState<Screen>('name-entry');
  const [studentName, setStudentName] = useState('');
  const [test, setTest] = useState<Test | null>(null);
  const [result, setResult] = useState<CompletionResult | null>(null);
  const [loadError, setLoadError] = useState('');
  const [sessionType, setSessionType] = useState<'assessment' | 'quiz'>('assessment');
  const [takeHomePath, setTakeHomePath] = useState('');
  const [forcedTestId, setForcedTestId] = useState<string | null>(null);

  // URL params:
  //   ?takehome=bella_data/take_home_session_6   → opens the take-home IDE
  //   ?test=bella_data_practice_exam_1           → after name entry, loads this exact test
  //                                                instead of the next adaptive iteration
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const th = params.get('takehome');
    if (th) {
      setTakeHomePath(th);
      setScreen('takehome');
      return;
    }
    const t = params.get('test');
    if (t) setForcedTestId(t);
  }, []);

  const handleStart = async (name: string) => {
    setStudentName(name);
    setScreen('loading');
    setLoadError('');
    try {
      let test_id: string;
      let session_type: 'assessment' | 'quiz';
      if (forcedTestId) {
        test_id = forcedTestId;
        session_type = 'quiz';
      } else {
        const next = await fetchNextTest(name);
        test_id = next.test_id;
        session_type = next.session_type;
      }
      setSessionType(session_type);
      const t = await fetchTest(test_id);
      setTest(t);
      setScreen('test');
    } catch {
      setLoadError('Could not load test. Make sure the backend is running.');
      setScreen('name-entry');
    }
  };

  const handleComplete = (r: CompletionResult) => {
    setResult(r);
    setScreen('complete');
  };

  const handleRetake = () => {
    setResult(null);
    setTest(null);
    setScreen('name-entry');
  };

  return (
    <div className="app">
      {screen === 'name-entry' && (
        <>
          <NameEntry onStart={handleStart} />
          {loadError && <p className="error" style={{ textAlign: 'center', marginTop: '1rem' }}>{loadError}</p>}
        </>
      )}
      {screen === 'loading' && (
        <div className="loading-screen">
          <p>Loading test…</p>
        </div>
      )}
      {screen === 'test' && test && (
        <TestRunner
          test={test}
          studentName={studentName}
          sessionType={sessionType}
          onComplete={handleComplete}
        />
      )}
      {screen === 'takehome' && takeHomePath && (
        <TakeHomeRunner
          manifestPath={`${takeHomePath}/manifest.json`}
          basePath={takeHomePath}
        />
      )}
      {screen === 'complete' && result && (
        <CompletionScreen
          score={result.score}
          rawCorrect={result.rawCorrect}
          total={result.total}
          responses={result.responses}
          test={result.test}
          studentName={result.studentName}
          sessionInfo={result.sessionInfo}
          onRetake={handleRetake}
        />
      )}
    </div>
  );
}
