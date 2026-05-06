"""Section hash tracking for incremental notebook rebuild."""
import hashlib
import json
from pathlib import Path


def _hash_files(topic_root: Path, patterns: list[str]) -> str:
    h = hashlib.sha256()
    for pat in patterns:
        if "*" in pat:
            for f in sorted(topic_root.glob(pat)):
                h.update(f.read_bytes())
        else:
            f = topic_root / pat
            if f.exists():
                h.update(f.read_bytes())
    return h.hexdigest()


def _hash_state_path(topic_root: Path) -> Path:
    return topic_root / "runtime" / ".notebook_section_hashes.json"


def _load_hash_state(topic_root: Path) -> dict[str, str]:
    p = _hash_state_path(topic_root)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_hash_state(topic_root: Path, hashes: dict[str, str]) -> None:
    p = _hash_state_path(topic_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(hashes, indent=2), encoding="utf-8")


def compute_section_hash(section_name: str, rendered_content: str) -> str:
    return hashlib.sha256(rendered_content.encode('utf-8')).hexdigest()
