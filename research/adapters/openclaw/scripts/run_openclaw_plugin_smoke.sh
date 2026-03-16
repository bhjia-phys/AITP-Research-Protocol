#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
KERNEL_ROOT="${REPO_ROOT}/research/knowledge-hub"
TODAY="${TODAY:-$(date +%F)}"
TOPIC="${TOPIC:-AITP OpenClaw plugin smoke test ${TODAY}}"
TOPIC_SLUG="${TOPIC_SLUG:-aitp-openclaw-plugin-smoke-${TODAY}}"
UPDATED_BY="${UPDATED_BY:-openclaw-plugin-smoke}"
AITP_BIN="${AITP_BIN:-aitp}"

export AITP_KERNEL_ROOT="${AITP_KERNEL_ROOT:-${KERNEL_ROOT}}"
export AITP_REPO_ROOT="${AITP_REPO_ROOT:-${REPO_ROOT}}"

"${AITP_BIN}" doctor >/dev/null
"${AITP_BIN}" bootstrap \
  --topic "${TOPIC}" \
  --topic-slug "${TOPIC_SLUG}" \
  --statement "Only verify the OpenClaw plugin path and runtime artifact materialization." \
  --human-request "Do one bounded plugin smoke step without scientific conclusions." \
  --updated-by "${UPDATED_BY}" \
  --json >/dev/null
"${AITP_BIN}" loop \
  --topic-slug "${TOPIC_SLUG}" \
  --human-request "Run one bounded OpenClaw plugin smoke step and leave human-readable artifacts." \
  --updated-by "${UPDATED_BY}" \
  --max-auto-steps 1 \
  --json >/dev/null

echo "topic_slug: ${TOPIC_SLUG}"
echo "runtime_root: ${KERNEL_ROOT}/runtime/topics/${TOPIC_SLUG}"
echo "path: ${KERNEL_ROOT}/runtime/topics/${TOPIC_SLUG}/agent_brief.md"
echo "path: ${KERNEL_ROOT}/runtime/topics/${TOPIC_SLUG}/operator_console.md"
echo "path: ${KERNEL_ROOT}/runtime/topics/${TOPIC_SLUG}/conformance_report.md"
