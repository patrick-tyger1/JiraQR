#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_DIR="${JIRAQR_RESULTS_DIR:-${REPO_DIR}/sample_data}"
PASS_DURATION_MS="${JIRAQR_PASS_DURATION_MS:-1000}"

cd "${REPO_DIR}"
exec python3 app.py --results-dir "${RESULTS_DIR}" --pass-duration-ms "${PASS_DURATION_MS}"
