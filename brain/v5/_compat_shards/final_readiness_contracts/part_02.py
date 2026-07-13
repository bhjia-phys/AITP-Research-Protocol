# Compatibility shard 2 for final_readiness_contracts.
from __future__ import annotations

def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}

def _validate_host_production_loop(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("runtime", "readiness_cli", "lifecycle_cli", "batch_lifecycle_smoke_cli"):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("session_start_smoke_supported"), bool):
        result.add(f"{path}.session_start_smoke_supported", "must be a bool")
    if payload.get("batch_lifecycle_smoke_supported") is not True:
        result.add(f"{path}.batch_lifecycle_smoke_supported", "must be true")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
