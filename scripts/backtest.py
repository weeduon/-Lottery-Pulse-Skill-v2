#!/usr/bin/env python3
"""Tiny backtest framework for lottery candidate strategies.

The default random strategy is a baseline. Any fancy strategy must beat this baseline
on long windows before it earns a chair at the adult table.
"""
from __future__ import annotations

import argparse
import random

import pandas as pd


def parse_nums(s: str) -> set[int]:
    return {int(x) for x in str(s).split() if str(x).strip()}


def random_ticket(game: str) -> tuple[set[int], set[int]]:
    if game == "kl8":
        return set(random.sample(range(1, 81), 10)), set()
    if game == "dlt":
        return set(random.sample(range(1, 36), 5)), set(random.sample(range(1, 13), 2))
    raise ValueError(game)


def dlt_prize(front_hit: int, back_hit: int) -> str | None:
    if front_hit == 5 and back_hit == 2:
        return "一等奖"
    if front_hit == 5 and back_hit == 1:
        return "二等奖"
    if (front_hit == 5 and back_hit == 0) or (front_hit == 4 and back_hit == 2):
        return "三等奖"
    if front_hit == 4 and back_hit == 1:
        return "四等奖"
    if (front_hit == 4 and back_hit == 0) or (front_hit == 3 and back_hit == 2):
        return "五等奖"
    if (front_hit == 3 and back_hit == 1) or (front_hit == 2 and back_hit == 2):
        return "六等奖"
    if (front_hit == 3 and back_hit == 0) or (front_hit == 2 and back_hit == 1) or (front_hit == 1 and back_hit == 2) or (front_hit == 0 and back_hit == 2):
        return "七等奖"
    return None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--game", choices=["kl8", "dlt"], required=True)
    p.add_argument("--input", required=True)
    p.add_argument("--strategy", default="random")
    p.add_argument("--trials", type=int, default=1000)
    args = p.parse_args()

    df = pd.read_csv(args.input)
    hit_counter = {}
    for _, row in df.iterrows():
        for _ in range(args.trials):
            a, b = random_ticket(args.game)
            if args.game == "kl8":
                draw = parse_nums(row["numbers"])
                hits = len(a & draw)
                hit_counter[hits] = hit_counter.get(hits, 0) + 1
            else:
                front = parse_nums(row["front_numbers"])
                back = parse_nums(row["back_numbers"])
                prize = dlt_prize(len(a & front), len(b & back)) or "未中"
                hit_counter[prize] = hit_counter.get(prize, 0) + 1

    print("Backtest baseline:", args.game, args.strategy)
    total = sum(hit_counter.values())
    for k, v in sorted(hit_counter.items(), key=lambda kv: str(kv[0])):
        print(k, v, f"{v / total:.6%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
