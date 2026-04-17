"""Topic truth-root support — path helpers for the unified topic folder layout.

ARCHITECTURE CONSTRAINT (single-topic truth root):
    All topic data MUST live under ``topics/<slug>/``.
    The legacy split-root layout (runtime/topics/, source-layer/topics/,
    intake/topics/, feedback/topics/, validation/topics/, consultation/topics/)
    has been fully migrated away.  No new code should reference legacy paths.

    Valid layer sub-directories inside ``topics/<slug>/``:
        L0/  L1/  L2/  L3/  L4/  runtime/  consultation/  logs/

    Global reusable knowledge (canonical L2) lives in ``canonical/``,
    NOT inside topic folders.  Topic-local L2/ is only a staging placeholder.

See: docs/AITP_TOPIC_FOLDER_ARCHITECTURE.md (in the AITP repo root)
"""
from __future__ import annotations

import warnings
from datetime import datetime
from pathlib import Path

# Legacy mappings kept only for backward-compatible inference during
# the transition period.  Do NOT use these to construct new paths.
LEGACY_LAYER_PREFIXES: dict[str, tuple[str, ...]] = {
    "runtime": ("runtime", "topics"),
    "L0": ("source-layer", "topics"),
    "L1": ("intake", "topics"),
    "L3": ("feedback", "topics"),
    "L4": ("validation", "topics"),
    "consultation": ("consultation", "topics"),
}
LEGACY_PREFIX_TO_LAYER = {
    prefix[0]: layer_name for layer_name, prefix in LEGACY_LAYER_PREFIXES.items()
}


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _path_from_parts(parts: tuple[str, ...]) -> Path:
    if not parts:
        return Path()
    return Path(parts[0]).joinpath(*parts[1:])


def topic_root(kernel_root: Path, topic_slug: str) -> Path:
    return kernel_root / "topics" / topic_slug


def runtime_root(kernel_root: Path, topic_slug: str) -> Path:
    return topic_root(kernel_root, topic_slug) / "runtime"


def layer_root(kernel_root: Path, topic_slug: str, layer_name: str) -> Path:
    return topic_root(kernel_root, topic_slug) / layer_name


def consultation_root(kernel_root: Path, topic_slug: str) -> Path:
    return topic_root(kernel_root, topic_slug) / "consultation"


def logs_root(kernel_root: Path, topic_slug: str) -> Path:
    return topic_root(kernel_root, topic_slug) / "logs"


def infer_kernel_root_from_topic_path(path: Path) -> Path | None:
    resolved = path.expanduser().resolve()
    parts = resolved.parts
    # Unified layout: topics/<slug>/...
    if "topics" in parts:
        index = parts.index("topics")
        if index + 2 < len(parts):
            return _path_from_parts(parts[:index])
    # Legacy layout fallback (deprecated, emits warning)
    for prefix in LEGACY_PREFIX_TO_LAYER:
        if prefix not in parts:
            continue
        index = parts.index(prefix)
        if index + 2 < len(parts) and parts[index + 1] == "topics":
            warnings.warn(
                f"Legacy path detected: '{prefix}/topics/...' is deprecated. "
                "All topic data must live under 'topics/<slug>/'.",
                DeprecationWarning,
                stacklevel=2,
            )
            return _path_from_parts(parts[:index])
    return None


def compatibility_projection_path(path: Path, *, kernel_root: Path | None = None) -> Path | None:
    """DEPRECATED: Legacy-to-unified path translation. Will be removed after migration."""
    warnings.warn(
        "compatibility_projection_path() is deprecated — "
        "legacy split-root layout has been fully migrated away.",
        DeprecationWarning,
        stacklevel=2,
    )
    resolved = path.expanduser().resolve()
    effective_kernel_root = (kernel_root or infer_kernel_root_from_topic_path(resolved))
    if effective_kernel_root is None:
        return None
    try:
        relative = resolved.relative_to(effective_kernel_root.resolve())
    except ValueError:
        return None
    parts = relative.parts
    if len(parts) >= 4 and parts[0] == "topics":
        topic_slug = parts[1]
        surface = parts[2]
        remainder = parts[3:]
        legacy_prefix = LEGACY_LAYER_PREFIXES.get(surface)
        if legacy_prefix is None:
            return None
        return effective_kernel_root.joinpath(*legacy_prefix, topic_slug, *remainder)
    if len(parts) >= 4 and parts[1] == "topics":
        legacy_prefix = parts[0]
        surface = LEGACY_PREFIX_TO_LAYER.get(legacy_prefix)
        if surface is None:
            return None
        topic_slug = parts[2]
        remainder = parts[3:]
        return effective_kernel_root / "topics" / topic_slug / surface / Path(*remainder)
    return None


def write_topic_manifest(
    kernel_root: Path,
    topic_slug: str,
    *,
    updated_by: str = "aitp",
) -> Path:
    root = topic_root(kernel_root, topic_slug)
    manifest_path = root / "topic_manifest.md"
    lines = [
        "---",
        f"topic_slug: {topic_slug}",
        "artifact_kind: topic_manifest",
        f"updated_at: {_now_iso()}",
        f"updated_by: {updated_by}",
        "---",
        "",
        "# Topic Manifest",
        "",
        "## Root Summary",
        "",
        f"- Topic root: `topics/{topic_slug}`",
        f"- Runtime root: `topics/{topic_slug}/runtime`",
        f"- L0 root: `topics/{topic_slug}/L0`",
        f"- L1 root: `topics/{topic_slug}/L1`",
        f"- L2 root: `topics/{topic_slug}/L2`",
        f"- L3 root: `topics/{topic_slug}/L3`",
        f"- L4 root: `topics/{topic_slug}/L4`",
        f"- Consultation root: `topics/{topic_slug}/consultation`",
        f"- Logs root: `topics/{topic_slug}/logs`",
        "",
        "## Contract",
        "",
        "This topic folder is the single topic-owned truth root. Human-readable Markdown surfaces belong here even when compatibility JSON projections still exist elsewhere during migration.",
        "",
    ]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(lines), encoding="utf-8")
    return manifest_path


def ensure_topic_truth_root(
    kernel_root: Path,
    topic_slug: str,
    *,
    updated_by: str = "aitp",
) -> dict[str, Path]:
    root = topic_root(kernel_root, topic_slug)
    paths = {
        "topic_root": root,
        "runtime_root": runtime_root(kernel_root, topic_slug),
        "L0": layer_root(kernel_root, topic_slug, "L0"),
        "L1": layer_root(kernel_root, topic_slug, "L1"),
        "L2": layer_root(kernel_root, topic_slug, "L2"),
        "L3": layer_root(kernel_root, topic_slug, "L3"),
        "L4": layer_root(kernel_root, topic_slug, "L4"),
        "consultation": consultation_root(kernel_root, topic_slug),
        "logs": logs_root(kernel_root, topic_slug),
    }
    for key in ("runtime_root", "L0", "L1", "L2", "consultation", "logs"):
        paths[key].mkdir(parents=True, exist_ok=True)
    (paths["L3"] / "runs").mkdir(parents=True, exist_ok=True)
    (paths["L4"] / "runs").mkdir(parents=True, exist_ok=True)
    paths["manifest"] = write_topic_manifest(kernel_root, topic_slug, updated_by=updated_by)
    return paths
