"""Composite trapezoidal rule for the synthetic integral of exp(-x*x)."""

import argparse
import math


def evaluate(n):
    if n < 1:
        raise ValueError("N must be positive")
    interior = math.fsum(math.exp(-((k / n) ** 2)) for k in range(1, n))
    value = (0.5 * (1.0 + math.exp(-1.0)) + interior) / n
    bound = 1.0 / (6.0 * n * n)
    return value, bound


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("N", type=int)
    args = parser.parse_args()
    value, bound = evaluate(args.N)
    print("N,T_N,error_bound,lower,upper")
    print(f"{args.N},{value:.15f},{bound:.15f},{value-bound:.15f},{value+bound:.15f}")
