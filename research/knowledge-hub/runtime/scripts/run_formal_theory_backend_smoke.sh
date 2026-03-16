#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KERNEL_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${KERNEL_ROOT}/../.." && pwd)"
AITP_BIN="${AITP_BIN:-aitp}"
TODAY="${TODAY:-$(date +%F)}"
TOPIC="${TOPIC:-AITP formal-theory backend smoke test ${TODAY}}"
TOPIC_SLUG="${TOPIC_SLUG:-aitp-formal-theory-backend-smoke-${TODAY}}"
UPDATED_BY="${UPDATED_BY:-formal-theory-backend-smoke}"
SMOKE_ROOT="${SMOKE_ROOT:-/tmp/aitp-formal-theory-backend-smoke-${TOPIC_SLUG}}"
BACKEND_ROOT="${BACKEND_ROOT:-${SMOKE_ROOT}/external-formal-theory-backend}"
NOTE_PATH="${NOTE_PATH:-${BACKEND_ROOT}/notes/modular-flow-derivation-outline.md}"
REALIZED_CARD="${REALIZED_CARD:-${SMOKE_ROOT}/formal-theory-note-library.realized.json}"
REGISTRY_ROW_PATH="${REGISTRY_ROW_PATH:-${SMOKE_ROOT}/backend_index.row.jsonl}"
EXAMPLE_CARD="${KERNEL_ROOT}/canonical/backends/examples/formal-theory-note-library.example.json"
SCHEMA_PATH="${KERNEL_ROOT}/schemas/l2-backend.schema.json"

export AITP_KERNEL_ROOT="${AITP_KERNEL_ROOT:-${KERNEL_ROOT}}"
export AITP_REPO_ROOT="${AITP_REPO_ROOT:-${REPO_ROOT}}"

mkdir -p "$(dirname "${NOTE_PATH}")"
mkdir -p "${SMOKE_ROOT}"

if [[ ! -f "${NOTE_PATH}" ]]; then
  cat > "${NOTE_PATH}" <<'EOF'
# Modular Flow Derivation Outline

This temporary note simulates one external formal-theory backend artifact.

- Topic: modular flow
- Role: derivation-focused formal note
- Claim: modular flow should be treated as source-bound material until AITP writes an explicit reusable concept or derivation object.
- Reminder: backend folder names are not canonical ontology.
EOF
fi

"${AITP_BIN}" doctor >/dev/null

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

"${AITP_BIN}" bootstrap \
  --topic "${TOPIC}" \
  --topic-slug "${TOPIC_SLUG}" \
  --statement "Only validate the external formal-theory backend bridge and operator-visible runtime artifacts." \
  --human-request "Do one bounded formal-theory backend smoke step without scientific conclusions." \
  --updated-by "${UPDATED_BY}" \
  --json >/dev/null

python3 "${KERNEL_ROOT}/source-layer/scripts/register_local_note_source.py" \
  --topic-slug "${TOPIC_SLUG}" \
  --path "${NOTE_PATH}" \
  --registered-by "${UPDATED_BY}" >/dev/null

"${AITP_BIN}" loop \
  --topic-slug "${TOPIC_SLUG}" \
  --human-request "Use the registered formal-theory backend note as a bounded L2 bridge, keep provenance explicit, and avoid folder-level canonicalization." \
  --updated-by "${UPDATED_BY}" \
  --max-auto-steps 1 \
  --json >/dev/null

"${AITP_BIN}" audit --topic-slug "${TOPIC_SLUG}" --phase exit >/dev/null

echo "status: success"
echo "topic_slug: ${TOPIC_SLUG}"
echo "backend_card: ${REALIZED_CARD}"
echo "backend_index_row: ${REGISTRY_ROW_PATH}"
echo "registered_note: ${NOTE_PATH}"
echo "runtime_root: ${KERNEL_ROOT}/runtime/topics/${TOPIC_SLUG}"
