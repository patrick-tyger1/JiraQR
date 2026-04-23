#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_DESKTOP="${REPO_DIR}/desktop/jiraqr.desktop"
TARGET_DESKTOP="${HOME}/Desktop/jiraqr.desktop"
TARGET_APPS="${HOME}/.local/share/applications/jiraqr.desktop"

mkdir -p "${HOME}/Desktop" "${HOME}/.local/share/applications"

# Replace development path with current repo path
sed "s|/workspace/JiraQR|${REPO_DIR}|g" "${SOURCE_DESKTOP}" > "${TARGET_DESKTOP}"
cp "${TARGET_DESKTOP}" "${TARGET_APPS}"
chmod +x "${TARGET_DESKTOP}" "${TARGET_APPS}"

echo "Installed desktop launchers:"
echo "- ${TARGET_DESKTOP}"
echo "- ${TARGET_APPS}"
echo
echo "If your desktop requires trusting launchers, right-click jiraqr.desktop and choose 'Allow Launching'."
