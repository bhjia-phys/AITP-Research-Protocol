"""AI Physicist Check — brain-level physicist reasoning patterns.

These functions verify that the AI has performed physics reasoning
(correspondence checks, anomaly detection, L2 lookup) and RECORDED it.
They do NOT check whether the physics is "correct" — that is the human's call.
"""

from __future__ import annotations

from typing import Any


# -- Physicist check functions --

# --- AI Physicist Check Pattern ---
# The AI IS a physicist — it reasons about physics, checks against known limits,
# compares with L2 knowledge, and flags anomalies for human discussion.
# These functions verify that such checks were RECORDED, not whether they're correct.

def _check_physicist_l2_lookup(body: str, stage: str) -> list[str]:
    """Verify the AI queried L2 at this stage and recorded findings.

    Each stage must reference L2 knowledge in its artifacts. Two valid patterns:
    1. References one or more concrete L2 entry IDs (claim-xxx, system-xxx, ...)
    2. States that L2 was queried and no relevant entries were found, with
       evidence of the query (mentions the tool used or the query parameters).

    A bare heading with "No prior knowledge found" is NOT valid — it doesn't
    prove that L2 was actually queried.

    Returns list of missing items (empty = valid).
    """
    import re
    issues = []
    heading_map = {
        "L0": "## Prior L2 Knowledge",
        "L1": "## L2 Cross-Reference",
        "L3": "## L2 Consistency Check",
        "L4": "## Benchmark Comparison",
    }
    heading = heading_map.get(stage)
    if heading and heading not in body:
        issues.append(f"Missing {heading} — must record what L2 already knows about this")
        return issues

    # Extract content between this heading and the next
    idx = body.find(heading)
    content_start = body.find("\n", idx) + 1
    remaining = body[content_start:]
    next_section = remaining.find("\n## ")
    section = remaining[:next_section] if next_section != -1 else remaining

    # Check for L2 entry ID references (found relevant entries)
    entry_refs = re.findall(
        r'(?:claim|system|method|pitfall|question)-[a-z][a-z0-9-]+',
        section
    )
    if entry_refs:
        return []  # Found explicit entry references → valid

    # No entry references. Check if the AI at least queried L2.
    # Accept evidence of querying: mentioning tool names or explicit "nothing found"
    queried_signals = [
        "aitp_query_l2", "aitp_query_entries", "aitp_query_l2_index",
        "aitp_query_l2_graph", "queried L2", "searched L2",
        "no relevant entries", "L2 returned no", "L2 has no relevant",
        "nothing relevant in L2", "no L2 entries matched",
        "L2 is empty for", "zero results", "0 results",
    ]
    has_query_evidence = any(signal.lower() in section.lower() for signal in queried_signals)
    if has_query_evidence:
        return []  # AI queried but found nothing → valid

    # Neither entry refs nor query evidence
    issues.append(
        f"{heading} must reference at least one L2 entry ID "
        "(e.g. claim-headwing-formula, system-si-bulk), "
        "or state that L2 was queried and no relevant entries were found. "
        "Run aitp_query_l2 or aitp_query_entries before filling this section, "
        "and mention what you searched for."
    )

    return issues


def _check_physicist_correspondence(body: str, lane: str) -> list[str]:
    """Verify correspondence check names at least one concrete physical limit.

    The check must:
    1. Name a specific limit (e.g. "T→0", "q→0", "weak coupling")
    2. State expected behavior in that limit
    3. State whether the result matches (and if not, discuss)
    """
    idx = body.find("## Correspondence Check")
    if idx == -1:
        idx = body.find("## Limiting Case Check")
    if idx == -1:
        idx = body.find("## Physicist Check")
    if idx == -1:
        return ["Missing correspondence/limiting case check"]

    content_start = body.find("\n", idx) + 1
    remaining = body[content_start:]
    next_section = remaining.find("\n## ")
    section = remaining[:next_section] if next_section != -1 else remaining

    issues = []
    # Must name at least one specific limit
    limit_keywords = ["T→0", "T → 0", "q→0", "q → 0", "weak coupling",
                      "strong coupling", "large N", "classical limit", "hbar→0",
                      "non-relativistic", "static limit", "long wavelength",
                      "low energy", "high temperature", "zero temperature",
                      "perturbative", "free field", "non-interacting"]
    has_limit = any(kw.lower() in section.lower() for kw in limit_keywords)
    if not has_limit:
        issues.append("Correspondence check must name at least one concrete physical limit")

    # For code_method/toy_numeric: must state whether computed value agrees
    if lane in ("code_method", "toy_numeric"):
        agreement_words = ["agrees", "deviates", "matches", "consistent",
                          "disagrees", "within", "error", "discrepancy"]
        has_agreement = any(w in section.lower() for w in agreement_words)
        if not has_agreement:
            issues.append("Correspondence check must state whether result agrees with limit/benchmark")

    return issues


def _check_physicist_anomalies(body: str) -> list[str]:
    """Verify that anomalies (unexpected results, deviations, surprises) are flagged for discussion.

    At minimum, the artifact must explicitly state either:
    - No anomalies were found (and why that's expected), OR
    - Specific anomalies were found and documented
    """
    has_anomaly_section = (
        "## Anomalies" in body
        or "## Surprises" in body
        or "## Unexpected Results" in body
        or "## Deviations" in body
        or "no anomalies" in body.lower()
        or "no unexpected" in body.lower()
        or "as expected" in body.lower()
    )
    if not has_anomaly_section:
        return ["Must flag anomalies for discussion — either document specific anomalies or explicitly state none were found"]
    return []


# -- Physicist reasoning patterns (protocol-level, not gate checks) --

PHYSICIST_CHECKPOINTS = ["L0→L1", "L1→L3", "candidate_submit", "L4_review"]

PHYSICIST_FOUR_QUESTIONS = {
    "l2_lookup": "What does L2 already know about this claim/result? Query aitp_query_l2_graph.",
    "correspondence": "Name a concrete physical limit. State expected vs actual behavior.",
    "anomalies": "Any surprises? Deviations from expectation? Unexpected behavior?",
    "human_verify": "What is the single most important claim the human should scrutinize?",
}

CORRESPONDENCE_LIMIT_KEYWORDS = [
    "T→0", "T → 0", "q→0", "q → 0", "weak coupling", "strong coupling",
    "large N", "classical limit", "hbar→0", "non-relativistic", "static limit",
    "long wavelength", "low energy", "high temperature", "zero temperature",
    "perturbative", "free field", "non-interacting", "thermodynamic limit",
    "continuum limit", "infinite volume", "mean field",
]
