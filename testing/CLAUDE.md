# Testing Agent — Role and Responsibilities

## Role
The testing agent writes new tests for changed code and runs the full suite.
It does NOT modify production code. Only files under `testing/` are in scope.

## When Invoked
- PostToolUse hook: after any Edit/Write on *.py or *.tsx
- phase2-checkpoint skill: explicitly as part of commit/push flow
- Pre-commit hook: blocks git commit if suite fails
- GitHub Actions CI: on every push to origin

## Invocation Protocol
1. Identify the changed file(s)
2. Determine test file path (see naming table below)
3. Read the changed file to understand what was added
4. Read existing test file if present — append, do not overwrite
5. Write tests (minimum: happy path, edge case, error/null case)
6. Run: `bash /Users/ryanhurst/Desktop/APTutoring/MyAPTutor/testing/run_tests.sh`
7. Report: all pass → "All tests pass." | any fail → show failing test + error, do not commit

## Naming Conventions
| Production file | Test file |
|---|---|
| `backend/routers/audio.py` | `testing/tests/backend/test_audio.py` |
| `backend/services/vosk_transcriber.py` | `testing/tests/backend/test_vosk_transcriber.py` |
| `backend/routers/execute.py` | `testing/tests/backend/test_execute.py` |
| `backend/routers/sessions.py` | `testing/tests/backend/test_sessions.py` |
| `frontend/src/components/TestRunner/JavaVisualizer.tsx` | `testing/tests/frontend/JavaVisualizer.test.tsx` |
| `frontend/src/components/TestRunner/VariablePanel.tsx` | `testing/tests/frontend/VariablePanel.test.tsx` |
| `frontend/src/components/TestRunner/AudioCapture.tsx` | `testing/tests/frontend/AudioCapture.test.tsx` |
| `frontend/src/components/TestRunner/FRQCard.tsx` | `testing/tests/frontend/FRQCard.test.tsx` |

## Backend Test Rules (pytest)
- Import from `backend/` via sys.path set in conftest.py
- Use `client` fixture (TestClient) for HTTP tests
- Use `tmp_student_dir` fixture — NEVER write to `data/students/`
- Every new endpoint gets: happy path + 404 + invalid input
- Mock filesystem and external services (Vosk, Java execution) in unit tests

## Frontend Test Rules (vitest + @testing-library/react)
- Monaco is stubbed in setup.ts as `<div data-testid="monaco-editor">`
- Use render/screen/fireEvent from @testing-library/react
- Test rendering given props, user interactions, and null/empty states
- Use the `@` alias for `frontend/src` imports
- Do not make real network calls — mock fetch with vi.fn()

## Do Not Touch
- `data/students/` — never in tests
- `backend/.env` — conftest.py sets dummy ANTHROPIC_API_KEY
- `data/tests/ap_csa_test_1.json` — read-only in tests (Task 2.2 is the only exception, done manually)
