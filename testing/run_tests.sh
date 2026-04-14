#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TESTING_DIR="$PROJECT_ROOT/testing"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_FAIL=0
FRONTEND_FAIL=0

echo "════════════════════════════════════════"
echo "  MyAPTutor Test Suite"
echo "════════════════════════════════════════"

echo ""
echo "── Backend (pytest) ─────────────────────"
cd "$PROJECT_ROOT"
source backend/venv/bin/activate
python -m pytest "$TESTING_DIR/tests/backend/" -v --tb=short || BACKEND_FAIL=1
deactivate

echo ""
echo "── Frontend (vitest) ────────────────────"
cd "$FRONTEND_DIR"
NODE_PATH="$FRONTEND_DIR/node_modules" npx vitest run --config "$TESTING_DIR/tests/frontend/vitest.config.ts" || FRONTEND_FAIL=1

echo ""
echo "════════════════════════════════════════"
if [ "$BACKEND_FAIL" -eq 0 ] && [ "$FRONTEND_FAIL" -eq 0 ]; then
  echo "  ALL TESTS PASS. Ready to commit."
  echo "════════════════════════════════════════"
  exit 0
else
  echo "  TESTS FAILED. Do not commit until fixed."
  echo "════════════════════════════════════════"
  exit 1
fi
