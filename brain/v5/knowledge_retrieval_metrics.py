"""Deterministic quality metrics for versioned retrieval fixtures."""

from __future__ import annotations

import math
from typing import Mapping, Sequence


def evaluate_ranked_refs(
    ranked_refs: Sequence[str],
    judgments: Mapping[str, int],
    *,
    k: int,
) -> dict[str, float]:
    relevant = {ref for ref, grade in judgments.items() if int(grade) > 0}
    top = list(ranked_refs[:k])
    retrieved = sum(1 for ref in top if ref in relevant)
    recall = retrieved / len(relevant) if relevant else 1.0
    reciprocal_rank = 0.0
    for index, ref in enumerate(ranked_refs, start=1):
        if ref in relevant:
            reciprocal_rank = 1.0 / index
            break
    dcg = sum(
        (2 ** int(judgments.get(ref, 0)) - 1) / math.log2(index + 2)
        for index, ref in enumerate(top)
    )
    ideal = sorted((int(value) for value in judgments.values()), reverse=True)[:k]
    idcg = sum(
        (2**grade - 1) / math.log2(index + 2)
        for index, grade in enumerate(ideal)
    )
    return {
        "recall_at_k": round(recall, 12),
        "mrr": round(reciprocal_rank, 12),
        "ndcg_at_k": round(dcg / idcg if idcg else 1.0, 12),
    }


__all__ = ["evaluate_ranked_refs"]
