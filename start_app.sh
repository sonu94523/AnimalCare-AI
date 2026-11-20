#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ADMIN_TOKEN="${ADMIN_TOKEN:-local-dev-admin}"
export VITE_ADMIN_TOKEN="${VITE_ADMIN_TOKEN:-$ADMIN_TOKEN}"

echo "Starting AnimalCare AI Backend on http://127.0.0.1:5000 ..."
(cd "$ROOT_DIR" && backend/venv/bin/python -m backend.app) &
BACKEND_PID=$!

cleanup() {
  echo "Stopping servers..."
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting AnimalCare AI Frontend on http://localhost:5173 ..."
cd "$ROOT_DIR/frontend"
npm run dev
