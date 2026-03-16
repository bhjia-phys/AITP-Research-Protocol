#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOPIC_SLUG="haldane-shastry-chaos-transition"
UPDATED_BY="${UPDATED_BY:-openclaw-control-path-test}"

STEP_NOTES=(
  "../../../knowledge-hub/runtime/topics/${TOPIC_SLUG}/control-notes/2026-03-16_openclaw-codex-control-path_step1-select-route.md"
  "../../../knowledge-hub/runtime/topics/${TOPIC_SLUG}/control-notes/2026-03-16_openclaw-codex-control-path_step2-materialize-task.md"
  "../../../knowledge-hub/runtime/topics/${TOPIC_SLUG}/control-notes/2026-03-16_openclaw-codex-control-path_step3-dispatch-task.md"
  "../../../knowledge-hub/runtime/topics/${TOPIC_SLUG}/control-notes/2026-03-16_openclaw-codex-control-path_step4-ingest-result.md"
)

for note_rel in "${STEP_NOTES[@]}"; do
  note_path="$(cd "${SCRIPT_DIR}" && realpath "${note_rel}")"
  if [[ ! -f "${note_path}" ]]; then
    echo "Missing control note: ${note_path}" >&2
    exit 1
  fi
  echo "==> heartbeat with $(basename "${note_path}")"
  python3 "${SCRIPT_DIR}/heartbeat_bridge.py" \
    --topic-slug "${TOPIC_SLUG}" \
    --control-note "${note_path}" \
    --updated-by "${UPDATED_BY}" \
    --max-steps 1
done

echo "==> key artifacts"
echo "runtime/topics/${TOPIC_SLUG}/next_action_decision.json"
echo "validation/topics/${TOPIC_SLUG}/runs/2026-03-12-otoc-krylov-extension/returned_execution_result.json"
echo "validation/topics/${TOPIC_SLUG}/runs/2026-03-12-otoc-krylov-extension/results/result_manifest.json"
