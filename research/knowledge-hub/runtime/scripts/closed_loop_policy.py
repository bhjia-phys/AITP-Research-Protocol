#!/usr/bin/env python3
"""Declarative policy loader for AITP closed-loop route selection and result ingest."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

POLICY_PATH = Path(__file__).resolve().parents[1] / "closed_loop_policies.json"


@lru_cache(maxsize=1)
def load_closed_loop_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def closed_loop_policy_path_ref() -> str:
    return "runtime/closed_loop_policies.json"


def route_selection_policy() -> dict:
    return dict((load_closed_loop_policy().get("route_selection") or {}))


def result_ingest_policy() -> dict:
    return dict((load_closed_loop_policy().get("result_ingest") or {}))
