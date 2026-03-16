#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KERNEL_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${KERNEL_ROOT}/../.." && pwd)"
AITP_BIN="${AITP_BIN:-}"
AITP_PYTHON_BIN="${AITP_PYTHON_BIN:-python3}"
TODAY="${TODAY:-$(date +%F)}"
TOPIC="${TOPIC:-AITP toy-model numeric backend smoke test ${TODAY}}"
TOPIC_SLUG="${TOPIC_SLUG:-aitp-toy-model-numeric-backend-smoke-${TODAY}}"
UPDATED_BY="${UPDATED_BY:-toy-model-numeric-backend-smoke}"
SMOKE_ROOT="${SMOKE_ROOT:-/tmp/aitp-toy-model-numeric-backend-smoke-${TOPIC_SLUG}}"
BACKEND_ROOT="${BACKEND_ROOT:-${SMOKE_ROOT}/external-toy-model-backend}"
CONFIG_PATH="${CONFIG_PATH:-${BACKEND_ROOT}/configs/tfim-gap-config.json}"
RESULT_PATH="${RESULT_PATH:-${BACKEND_ROOT}/results/tfim-gap-result.json}"
NOTE_PATH="${NOTE_PATH:-${BACKEND_ROOT}/notes/tfim-gap-benchmark.md}"
REALIZED_CARD="${REALIZED_CARD:-${SMOKE_ROOT}/toy-model-numeric-workspace.realized.json}"
REGISTRY_ROW_PATH="${REGISTRY_ROW_PATH:-${SMOKE_ROOT}/backend_index.row.jsonl}"
EXAMPLE_CARD="${KERNEL_ROOT}/canonical/backends/examples/toy-model-numeric-workspace.example.json"
CONFIG_TEMPLATE="${KERNEL_ROOT}/validation/templates/toy-model-numeric/tfim-gap.config.template.json"
SCHEMA_PATH="${KERNEL_ROOT}/schemas/l2-backend.schema.json"
TOOL_PATH="${KERNEL_ROOT}/validation/tools/tfim_exact_diagonalization.py"

export AITP_KERNEL_ROOT="${AITP_KERNEL_ROOT:-${KERNEL_ROOT}}"
export AITP_REPO_ROOT="${AITP_REPO_ROOT:-${REPO_ROOT}}"
export PYTHONPATH="${KERNEL_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

run_aitp() {
  if [[ -n "${AITP_BIN}" ]]; then
    "${AITP_BIN}" "$@"
    return
  fi
  "${AITP_PYTHON_BIN}" -m knowledge_hub.aitp_cli \
    --kernel-root "${KERNEL_ROOT}" \
    --repo-root "${REPO_ROOT}" \
    "$@"
}

mkdir -p "$(dirname "${CONFIG_PATH}")" "$(dirname "${RESULT_PATH}")" "$(dirname "${NOTE_PATH}")" "${SMOKE_ROOT}"
cp "${CONFIG_TEMPLATE}" "${CONFIG_PATH}"

run_aitp doctor >/dev/null

python3 "${TOOL_PATH}" \
  --config "${CONFIG_PATH}" \
  --output "${RESULT_PATH}" \
  --summary-note "${NOTE_PATH}"

python3 - "${EXAMPLE_CARD}" "${SCHEMA_PATH}" "${REALIZED_CARD}" "${REGISTRY_ROW_PATH}" "${BACKEND_ROOT}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

example_path = Path(sys.argv[1])
schema_path = Path(sys.argv[2])
realized_path = Path(sys.argv[3])
registry_path = Path(sys.argv[4])
backend_root = Path(sys.argv[5]).resolve()

payload = json.loads(example_path.read_text(encoding="utf-8"))
payload["status"] = "active"
payload["root_paths"] = [str(backend_root)]

schema = json.loads(schema_path.read_text(encoding="utf-8"))
Draft202012Validator(schema).validate(payload)

realized_path.parent.mkdir(parents=True, exist_ok=True)
realized_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

registry_row = {
    "backend_id": payload["backend_id"],
    "title": payload["title"],
    "backend_type": payload["backend_type"],
    "status": payload["status"],
    "card_path": str(realized_path),
    "canonical_targets": payload["canonical_targets"],
}
registry_path.write_text(json.dumps(registry_row, ensure_ascii=True) + "\n", encoding="utf-8")
PY

python3 - "${RESULT_PATH}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert "spectral_gap" in (payload.get("metrics") or {}), "Missing spectral_gap metric"
PY

run_aitp bootstrap \
  --topic "${TOPIC}" \
  --topic-slug "${TOPIC_SLUG}" \
  --statement "Only validate the external toy-model numeric backend bridge and operator-visible runtime artifacts." \
  --human-request "Do one bounded toy-model numeric backend smoke step without scientific conclusions." \
  --updated-by "${UPDATED_BY}" \
  --json >/dev/null

python3 "${KERNEL_ROOT}/source-layer/scripts/register_local_note_source.py" \
  --topic-slug "${TOPIC_SLUG}" \
  --path "${NOTE_PATH}" \
  --registered-by "${UPDATED_BY}" \
  --backend-id "backend:toy-model-numeric-workspace" \
  --backend-root "${BACKEND_ROOT}" \
  --backend-artifact-kind "toy_model_numeric_run_note" \
  --backend-relative-path "notes/tfim-gap-benchmark.md" \
  --backend-card-path "${REALIZED_CARD}" >/dev/null

run_aitp loop \
  --topic-slug "${TOPIC_SLUG}" \
  --human-request "Use the registered toy-model numeric backend note as a bounded L2 bridge, keep provenance explicit, keep the model definition visible, and avoid scientific conclusions." \
  --updated-by "${UPDATED_BY}" \
  --max-auto-steps 1 \
  --json >/dev/null

run_aitp audit --topic-slug "${TOPIC_SLUG}" --phase exit >/dev/null

grep -q 'backend:toy-model-numeric-workspace' "${KERNEL_ROOT}/runtime/topics/${TOPIC_SLUG}/agent_brief.md"
grep -q 'source-layer/scripts/register_local_note_source.py' "${KERNEL_ROOT}/runtime/topics/${TOPIC_SLUG}/agent_brief.md"
grep -q 'backend:toy-model-numeric-workspace' "${KERNEL_ROOT}/runtime/topics/${TOPIC_SLUG}/runtime_protocol.generated.md"
grep -q 'source-layer/scripts/register_local_note_source.py' "${KERNEL_ROOT}/runtime/topics/${TOPIC_SLUG}/runtime_protocol.generated.md"

echo "status: success"
echo "topic_slug: ${TOPIC_SLUG}"
echo "backend_card: ${REALIZED_CARD}"
echo "backend_index_row: ${REGISTRY_ROW_PATH}"
echo "config_path: ${CONFIG_PATH}"
echo "result_path: ${RESULT_PATH}"
echo "registered_note: ${NOTE_PATH}"
echo "runtime_root: ${KERNEL_ROOT}/runtime/topics/${TOPIC_SLUG}"
