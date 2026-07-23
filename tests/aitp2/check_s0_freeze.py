#!/usr/bin/env python3
"""S0 freeze validator — decisions-only mode.

Validates committed S0_DECISIONS.json for Oracle Gate B evidence.
Stdlib only. No third-party imports, no aitp, no external .aitp access.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# ── frozen error codes (from active spec §7.3) ──────────────────────────
FROZEN_ERROR_CODES = frozenset({
    "validation_failed",
    "not_available_in_stage",
    "profile_mismatch",
})

ERROR_PRIORITY = {
    "profile_mismatch": 6,
    "validation_failed": 8,
    "not_available_in_stage": 17,
}

_EXPECTED_IDS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "U1"]
_VALID_STATUSES = frozenset({"frozen", "user-decision-required", "explicitly-deferred"})
_FORBIDDEN_STATUS_TOKENS = frozenset({"TBD", "pending", "discuss", "blank"})

# D2 identity regex — human:<slug> only for decided_by contexts
_ID_RE = re.compile(r"^human:([a-z0-9]+(?:[._-][a-z0-9]+)*)$")
_SLUG_MAX_LEN = 64

# Git object-id hex check (lowercase/uppercase hex only)
_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")


def _repo_root_from_script() -> Path:
    """Derive repo root from this script's location (tests/aitp2/)."""
    return Path(__file__).resolve().parent.parent.parent


def _default_decisions_path(repo_root: Path) -> Path:
    return repo_root / "tests" / "fixtures" / "aitp2" / "S0_DECISIONS.json"


def _git_cat_file(repo_root: Path, commit: str, path: str) -> bool:
    """Return True if commit:path exists in local Git repo.
    commit must be pre-validated hex — reject non-hex defensively.
    """
    if not _HEX_RE.match(commit):
        return False
    try:
        subprocess.run(
            ["git", "cat-file", "-e", f"{commit}:{path}"],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            timeout=15,
        )
        return True
    except Exception:
        return False


def _err(code: str, detail: str) -> dict:
    """Create a frozen error dict. Guards against non-frozen codes."""
    if code not in FROZEN_ERROR_CODES:
        raise ValueError(f"Frozen error code {code!r} not in FROZEN_ERROR_CODES")
    return {"code": code, "detail": detail}


def _validate_path(ref_path: str) -> str | None:
    """Validate a relative POSIX authority path.  Returns error detail or None.
    Rejects empty/dot/dotdot components, absolute, drive, backslash, controls.
    Allows benign double-dot in filenames (e.g. foo..bar).
    """
    if not isinstance(ref_path, str):
        return "path is not a string"
    if not ref_path:
        return "path is empty"
    if ref_path.startswith("/") or re.search(r"^[A-Za-z]:", ref_path):
        return f"absolute or drive-qualified path: {ref_path!r}"
    if re.search(r"[\x00-\x1f\x7f\\]", ref_path):
        return f"unsafe path (control/backslash): {ref_path!r}"
    parts = ref_path.split("/")
    for part in parts:
        if not part or part == "." or part == "..":
            return f"invalid path component {part!r}: {ref_path!r}"
    return None


def _validate_commit_id(commit: str, repo_root: Path) -> str | None:
    """Verify authority_commit is a full local Git object-id.
    Returns error detail or None.
    """
    if not isinstance(commit, str) or not _HEX_RE.match(commit):
        return f"authority_commit is not a valid hex object-id: {commit!r}"
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return f"authority_commit not a valid local commit: {commit!r}"
        resolved = result.stdout.strip().lower()
        if resolved != commit.lower():
            return f"authority_commit does not resolve to same full id: {commit!r}"
    except Exception as exc:
        return f"authority_commit git verify failed: {exc}"
    return None


def _check_identity(value: str, label: str) -> str | None:
    """Validate human:<slug> with slug 1–64 chars.  Returns error detail or None."""
    if not isinstance(value, str):
        return f"{label}: not a string"
    m = _ID_RE.match(value)
    if not m:
        return f"{label} {value!r} does not match human:<slug> (D2)"
    slug = m.group(1)
    if len(slug) < 1 or len(slug) > _SLUG_MAX_LEN:
        return f"{label} slug length {len(slug)} must be 1-{_SLUG_MAX_LEN} (D2)"
    return None


def _sort_errors(errors: list[dict]) -> list[dict]:
    """Sort errors by frozen priority (stable within same priority)."""
    return sorted(errors, key=lambda e: ERROR_PRIORITY.get(e["code"], 999))


def _primary_error(errors: list[dict]) -> str | None:
    """Derive primary error code from minimum priority among errors."""
    if not errors:
        return None
    priorities = [ERROR_PRIORITY.get(e["code"], 999) for e in errors]
    min_idx = priorities.index(min(priorities))
    return errors[min_idx]["code"]


def validate_decisions(data: dict, repo_root: Path) -> tuple[bool, list[dict], dict]:
    """Validate decisions JSON. Returns (ok, errors, summary)."""
    errors: list[dict] = []

    # ── top-level shape ──────────────────────────────────────────────
    if not isinstance(data, dict):
        errors.append(_err("validation_failed", "top-level is not a JSON object"))
        return False, errors, {}

    for key in ("protocol", "artifact", "stage", "state", "decisions"):
        if key not in data:
            errors.append(_err("validation_failed", f"missing top-level key: {key}"))

    # Exact-value checks
    if data.get("protocol") != "aitp/2.0":
        errors.append(_err("profile_mismatch",
            f"protocol must be aitp/2.0, got {data.get('protocol')!r}"))
    if data.get("artifact") != "S0/T1a":
        errors.append(_err("profile_mismatch",
            f"artifact must be S0/T1a, got {data.get('artifact')!r}"))
    if data.get("stage") != "S0_DECISIONS":
        errors.append(_err("not_available_in_stage",
            f"stage must be S0_DECISIONS, got {data.get('stage')!r}"))
    if data.get("state") != "ready_for_gate_b_review":
        errors.append(_err("validation_failed",
            f"state must be ready_for_gate_b_review, got {data.get('state')!r}"))

    # ── required sections existence and type ─────────────────────────
    for section in ("meta", "t0_metadata", "approval_evidence"):
        if section not in data:
            errors.append(_err("validation_failed", f"missing top-level key: {section}"))
        elif not isinstance(data[section], dict):
            errors.append(_err("validation_failed", f"{section} is not an object"))
    if isinstance(data.get("t0_metadata"), dict):
        t0_checks = data["t0_metadata"].get("t0_checks")
        if not isinstance(t0_checks, dict):
            errors.append(_err("validation_failed",
                "t0_metadata.t0_checks missing or not an object"))

    decisions = data.get("decisions")
    if not isinstance(decisions, list):
        errors.append(_err("validation_failed", "decisions is not a list"))
        return False, errors, {}

    # ── decision IDs ─────────────────────────────────────────────────
    actual_ids = []
    seen = set()
    for i, d in enumerate(decisions):
        if not isinstance(d, dict):
            errors.append(_err("validation_failed", f"decisions[{i}] is not an object"))
            continue
        did = d.get("id")
        if not did or not isinstance(did, str):
            errors.append(_err("validation_failed", f"decisions[{i}] missing or invalid id"))
            continue
        if did in seen:
            errors.append(_err("validation_failed", f"duplicate decision id: {did}"))
        seen.add(did)
        actual_ids.append(did)

    expected_ids = list(_EXPECTED_IDS)
    if actual_ids != expected_ids:
        errors.append(_err("validation_failed",
            f"decision IDs mismatch: expected {expected_ids}, got {actual_ids}"))

    if len(decisions) != 10:
        errors.append(_err("validation_failed",
            f"expected 10 decisions, got {len(decisions)}"))

    # ── authority commit validation ──────────────────────────────────
    auth_commit = None
    if isinstance(data.get("t0_metadata"), dict):
        auth_commit = data["t0_metadata"].get("authority_commit")
    if not auth_commit or not isinstance(auth_commit, str):
        errors.append(_err("validation_failed",
            "missing or invalid t0_metadata.authority_commit"))
    else:
        ace = _validate_commit_id(auth_commit, repo_root)
        if ace:
            errors.append(_err("validation_failed", ace))

    # ── per-decision checks ──────────────────────────────────────────
    frozen_count = 0
    udr_count = 0
    deferred_count = 0
    for i, d in enumerate(decisions):
        # Guard: malformed list items produce structured errors, never traceback
        if not isinstance(d, dict):
            errors.append(_err("validation_failed",
                f"decisions[{i}] is not an object"))
            continue
        did = d.get("id", f"[{i}]")
        if not isinstance(did, str):
            did = f"[{i}]"
        status = d.get("status")
        if not status or not isinstance(status, str):
            errors.append(_err("validation_failed", f"{did}: missing or invalid status"))
            continue

        # Forbidden tokens and unrecognized status
        if status in _FORBIDDEN_STATUS_TOKENS:
            errors.append(_err("validation_failed",
                f"{did}: forbidden status token: {status}"))
        if status not in _VALID_STATUSES:
            errors.append(_err("validation_failed",
                f"{did}: unrecognized status: {status}"))

        if status == "frozen":
            frozen_count += 1
            # Summary required
            summary = d.get("summary", "")
            if not summary or not isinstance(summary, str):
                errors.append(_err("validation_failed",
                    f"{did}: frozen entry missing nonempty summary"))

            # Authority refs
            refs = d.get("authority_refs", [])
            if not refs or not isinstance(refs, list):
                errors.append(_err("validation_failed",
                    f"{did}: frozen entry missing authority_refs list"))
            else:
                for ri, ref in enumerate(refs):
                    if not isinstance(ref, dict):
                        errors.append(_err("validation_failed",
                            f"{did}: authority_refs[{ri}] is not an object"))
                        continue
                    rpath = ref.get("path", "")
                    rsection = ref.get("section", "")
                    rcommit = ref.get("commit", "")

                    # Type-safe path validation
                    if not isinstance(rpath, str):
                        errors.append(_err("validation_failed",
                            f"{did}: authority_refs[{ri}] path is not a string"))
                    else:
                        pe = _validate_path(rpath)
                        if pe:
                            errors.append(_err("validation_failed",
                                f"{did}: authority_refs[{ri}] path error: {pe}"))

                    if not rsection or not isinstance(rsection, str):
                        errors.append(_err("validation_failed",
                            f"{did}: authority_refs[{ri}] missing nonempty section"))
                    if not rcommit or not isinstance(rcommit, str):
                        errors.append(_err("validation_failed",
                            f"{did}: authority_refs[{ri}] missing nonempty commit"))
                    elif auth_commit and rcommit != auth_commit:
                        errors.append(_err("validation_failed",
                            f"{did}: authority_refs[{ri}] commit {rcommit!r} != "
                            f"top-level authority_commit {auth_commit!r}"))
                    elif (auth_commit and isinstance(rcommit, str)
                          and isinstance(rpath, str) and rcommit and rpath
                          and _HEX_RE.match(rcommit)):
                        # Git existence check only with validated hex commit
                        if not _git_cat_file(repo_root, rcommit, rpath):
                            errors.append(_err("validation_failed",
                                f"{did}: authority_refs[{ri}] commit:path not "
                                f"in local repo: {rcommit}:{rpath}"))

            # decided_by: human:<slug> required (D2), slug 1–64
            db = d.get("decided_by", "")
            id_err = _check_identity(db, f"{did} decided_by")
            if id_err:
                errors.append(_err("validation_failed", id_err))

            # decided_at required
            da = d.get("decided_at", "")
            if not da or not isinstance(da, str):
                errors.append(_err("validation_failed",
                    f"{did}: frozen entry missing decided_at"))

        elif status == "user-decision-required":
            udr_count += 1
            errors.append(_err("validation_failed",
                f"{did}: status user-decision-required — decisions-only mode "
                f"requires zero unresolved entries"))

        elif status == "explicitly-deferred":
            deferred_count += 1
            for field in ("named_slice", "rationale", "acceptance_criteria"):
                val = d.get(field, "")
                if not val or not isinstance(val, str):
                    errors.append(_err("validation_failed",
                        f"{did}: explicitly-deferred entry missing nonempty {field}"))

    # ── D7 and U1 must be frozen (type-safe lookup) ──────────────────
    for did in ("D7", "U1"):
        entry = next((d for d in decisions
                      if isinstance(d, dict) and d.get("id") == did), None)
        if entry and entry.get("status") != "frozen":
            errors.append(_err("validation_failed", f"{did}: must be frozen"))

    # ── approval evidence ────────────────────────────────────────────
    ae = data.get("approval_evidence", {})
    if isinstance(ae, dict):
        ae_db = ae.get("decided_by", "")
        id_err = _check_identity(ae_db, "approval_evidence.decided_by")
        if id_err:
            errors.append(_err("validation_failed", id_err))
        ae_da = ae.get("decided_at", "")
        if not ae_da or not isinstance(ae_da, str):
            errors.append(_err("validation_failed",
                "approval_evidence missing decided_at"))
        ae_method = ae.get("method", "")
        if not ae_method or not isinstance(ae_method, str):
            errors.append(_err("validation_failed",
                "approval_evidence.method missing or empty"))

    # ── meta counts ──────────────────────────────────────────────────
    meta = data.get("meta", {})
    if isinstance(meta, dict):
        if meta.get("total_decisions") != len(decisions):
            errors.append(_err("validation_failed",
                f"meta.total_decisions {meta.get('total_decisions')} "
                f"!= actual {len(decisions)}"))
        if meta.get("frozen_count") != frozen_count:
            errors.append(_err("validation_failed",
                f"meta.frozen_count {meta.get('frozen_count')} "
                f"!= actual {frozen_count}"))
        if meta.get("user_decision_required_count") != udr_count:
            errors.append(_err("validation_failed",
                f"meta.user_decision_required_count "
                f"{meta.get('user_decision_required_count')} "
                f"!= actual {udr_count}"))
        if meta.get("explicitly_deferred_count") != deferred_count:
            errors.append(_err("validation_failed",
                f"meta.explicitly_deferred_count "
                f"{meta.get('explicitly_deferred_count')} "
                f"!= actual {deferred_count}"))
        actual_id_set = meta.get("decision_ids_exact_set")
        expected_id_set = list(_EXPECTED_IDS)
        if actual_id_set != expected_id_set:
            errors.append(_err("validation_failed",
                f"meta.decision_ids_exact_set {actual_id_set} "
                f"!= expected {expected_id_set}"))
        absent = meta.get("forbidden_statuses_absent", [])
        absent_ok = True
        if not isinstance(absent, list):
            absent_ok = False
        else:
            for elem in absent:
                if not isinstance(elem, str):
                    absent_ok = False
                    break
        if not absent_ok or set(absent) != _FORBIDDEN_STATUS_TOKENS:
            errors.append(_err("validation_failed",
                "meta.forbidden_statuses_absent missing expected tokens"))
    else:
        errors.append(_err("validation_failed", "meta is not an object"))

    # ── T0 metadata ──────────────────────────────────────────────────
    t0 = data.get("t0_metadata", {})
    if isinstance(t0, dict):
        for field in ("head", "origin_main", "cutover_ancestor", "phase1_ancestor",
                       "authority_commit", "branch", "t0_verified_at"):
            if not t0.get(field):
                errors.append(_err("validation_failed",
                    f"t0_metadata.{field} missing or empty"))
        t0_checks = t0.get("t0_checks", {})
        if isinstance(t0_checks, dict):
            for ck in ("ancestor_389b3149", "ancestor_7de57f34",
                        "local_equals_remote", "tree_clean",
                        "authority_guard_pass", "origin_main_baseline_match"):
                if t0_checks.get(ck) is not True:
                    errors.append(_err("validation_failed",
                        f"t0_checks.{ck} is not true"))
        else:
            errors.append(_err("validation_failed",
                "t0_checks missing or not an object"))
    else:
        errors.append(_err("validation_failed", "t0_metadata is not an object"))

    ok = len(errors) == 0
    summary = {
        "total_decisions": len(decisions),
        "frozen_count": frozen_count,
        "user_decision_required_count": udr_count,
        "explicitly_deferred_count": deferred_count,
        "expected_ids": list(_EXPECTED_IDS),
        "actual_ids": actual_ids,
        "errors": [e["detail"] for e in errors],
    }
    return ok, errors, summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="S0 freeze validator — decisions-only mode",
    )
    parser.add_argument(
        "--decisions-only",
        action="store_true",
        help="Validate committed S0_DECISIONS.json (decisions-only mode)",
    )
    parser.add_argument(
        "--decisions-path",
        type=Path,
        default=None,
        help="Path to S0_DECISIONS.json (default: committed artifact)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: auto-detect from script location)",
    )
    args = parser.parse_args()

    mode = None
    if args.decisions_only:
        mode = "decisions-only"

    repo_root = args.repo_root or _repo_root_from_script()
    if not repo_root.is_dir():
        result = {
            "status": "error",
            "mode": mode,
            "primary_error": "validation_failed",
            "errors": [_err("validation_failed", f"repo-root not found: {repo_root}")],
        }
        print(json.dumps(result, sort_keys=True, indent=2))
        return 1

    if mode == "decisions-only":
        decisions_path = args.decisions_path or _default_decisions_path(repo_root)
        if not decisions_path.is_file():
            err = _err("validation_failed",
                       f"decisions file not found: {decisions_path}")
            result = {
                "status": "error",
                "mode": mode,
                "primary_error": "validation_failed",
                "errors": [err],
            }
            print(json.dumps(result, sort_keys=True, indent=2))
            return 1

        try:
            raw = decisions_path.read_text(encoding="utf-8")
        except Exception as exc:
            err = _err("validation_failed",
                       f"cannot read {decisions_path}: {exc}")
            result = {
                "status": "error",
                "mode": mode,
                "primary_error": "validation_failed",
                "errors": [err],
            }
            print(json.dumps(result, sort_keys=True, indent=2))
            return 1

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            err = _err("validation_failed",
                       f"JSON parse error at line {exc.lineno} "
                       f"col {exc.colno}: {exc.msg}")
            result = {
                "status": "error",
                "mode": mode,
                "primary_error": "validation_failed",
                "errors": [err],
            }
            print(json.dumps(result, sort_keys=True, indent=2))
            return 1

        ok, errs, summary = validate_decisions(data, repo_root)
        sorted_errs = _sort_errors(errs)
        primary_error = _primary_error(sorted_errs)

        result = {
            "status": "ok" if ok else "error",
            "mode": mode,
            "decisions_path": str(decisions_path),
            "total_decisions": summary.get("total_decisions", 0),
            "frozen_count": summary.get("frozen_count", 0),
            "user_decision_required_count": summary.get(
                "user_decision_required_count", 0),
            "explicitly_deferred_count": summary.get(
                "explicitly_deferred_count", 0),
            "primary_error": primary_error,
            "errors": sorted_errs,
        }
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0 if ok else 1

    # No supported mode selected
    result = {
        "status": "error",
        "mode": mode,
        "primary_error": "not_available_in_stage",
        "errors": [_err("not_available_in_stage",
            "no supported mode selected — use --decisions-only")],
    }
    print(json.dumps(result, sort_keys=True, indent=2))
    return 1


if __name__ == "__main__":
    sys.exit(main())
