#!/usr/bin/env python3
"""Probability helpers for KL8 and DLT."""
from __future__ import annotations

from math import comb


def kl8_match_prob(k: int, r: int) -> float:
    """P(exactly r hits when choosing k numbers, draw has 20 from 80)."""
    if r < 0 or r > k:
        return 0.0
    return comb(20, r) * comb(60, k - r) / comb(80, k)


def dlt_total_combinations() -> int:
    return comb(35, 5) * comb(12, 2)


def dlt_at_least_one_jackpot_prob(groups: int) -> float:
    """Probability that at least one of N unique DLT tickets wins first prize."""
    p = 1 / dlt_total_combinations()
    return 1 - (1 - p) ** groups


def kl8_exact_hit_probability(k: int, r: int) -> float:
    """P(exactly r hits when choosing k numbers, draw has 20 from 80)."""
    if r < 0 or r > k or 20 - r < 0 or 20 - r > 80 - k:
        return 0.0
    return comb(k, r) * comb(80 - k, 20 - r) / comb(80, 20)


def dlt_match_prob(front_hits: int, back_hits: int) -> float:
    """P(exact front/back hits for one DLT ticket."""
    return (
        comb(5, front_hits) * comb(30, 5 - front_hits) / comb(35, 5)
        * comb(2, back_hits) * comb(10, 2 - back_hits) / comb(12, 2)
    )


def main() -> None:
    print("大乐透总组合数:", dlt_total_combinations())
    print("大乐透一等奖概率: 1 /", dlt_total_combinations())
    print("大乐透5组至少一组一等奖概率:", dlt_at_least_one_jackpot_prob(5))
    for k in range(1, 11):
        print("快乐8 选%d:" % k, {r: round(kl8_match_prob(k, r), 8) for r in range(k + 1)})


if __name__ == "__main__":
    main()
