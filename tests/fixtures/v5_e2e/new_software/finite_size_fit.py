"""Small disposable research CLI used by the AITP onboarding vertical."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def fit_inverse_size(sizes: list[float], values: list[float]) -> dict[str, float | int]:
    if len(sizes) != len(values) or len(sizes) < 3:
        raise ValueError("sizes and values must have the same length of at least three")
    if any(size <= 0 for size in sizes):
        raise ValueError("sizes must be positive")
    x = [1.0 / size for size in sizes]
    x_mean = sum(x) / len(x)
    y_mean = sum(values) / len(values)
    denominator = sum((item - x_mean) ** 2 for item in x)
    if denominator == 0:
        raise ValueError("sizes must contain distinct values")
    slope = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values)) / denominator
    intercept = y_mean - slope * x_mean
    residuals = [yi - (intercept + slope * xi) for xi, yi in zip(x, values)]
    rmse = math.sqrt(sum(item * item for item in residuals) / len(residuals))
    return {
        "sample_count": len(sizes),
        "intercept": intercept,
        "slope": slope,
        "rmse": rmse,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = fit_inverse_size(payload["sizes"], payload["values"])
    args.output.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
