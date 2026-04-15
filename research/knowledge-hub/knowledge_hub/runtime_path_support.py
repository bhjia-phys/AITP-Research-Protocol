from __future__ import annotations

from pathlib import Path


def resolve_runtime_reference_path(
    value: str | Path | None,
    *,
    kernel_root: Path,
    repo_root: Path,
) -> Path | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    normalized = raw.replace("\\", "/")
    if normalized.startswith("topics/"):
        return (kernel_root / Path(normalized)).resolve()
    if normalized.startswith("runtime/"):
        return (kernel_root / Path(normalized)).resolve()
    kernel_candidate = (kernel_root / candidate).resolve()
    if kernel_candidate.exists():
        return kernel_candidate
    return (repo_root / candidate).resolve()
