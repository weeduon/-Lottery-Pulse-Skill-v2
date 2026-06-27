#!/usr/bin/env python3
"""Daily simulated number generator for KL8 and DLT.

This script generates entertainment/research number sets with transparent
reasoning and theoretical probabilities. It does NOT predict lottery results.
Randomness is seeded by game + date + strategy so the same date produces a
stable daily report.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import random
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Iterable, Sequence


def parse_nums(value: str | None) -> list[int]:
    if not value:
        return []
    return [int(x) for x in str(value).replace(",", " ").split() if x.strip()]


def fmt_nums(nums: Sequence[int], width: int = 2) -> str:
    return " ".join(f"{n:0{width}d}" for n in nums)


def stable_rng(seed_text: str) -> random.Random:
    digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def comb(n: int, k: int) -> int:
    return math.comb(n, k)


def pct(prob: float) -> str:
    return f"{prob * 100:.10f}%"


def one_in(prob: float) -> str:
    if prob <= 0:
        return "∞"
    return f"1 / {round(1 / prob):,}"


def weighted_sample_without_replacement(
    rng: random.Random,
    items: Sequence[int],
    weights: dict[int, float],
    k: int,
) -> list[int]:
    pool = list(items)
    selected: list[int] = []
    for _ in range(k):
        total = sum(max(weights.get(x, 1.0), 0.001) for x in pool)
        r = rng.random() * total
        acc = 0.0
        chosen = pool[-1]
        for item in pool:
            acc += max(weights.get(item, 1.0), 0.001)
            if acc >= r:
                chosen = item
                break
        selected.append(chosen)
        pool.remove(chosen)
    return selected


@dataclass
class HistoryStats:
    freq: Counter[int]
    omission: dict[int, int]
    draws: int


def build_stats(rows: list[dict[str, str]], field: str, universe: Iterable[int]) -> HistoryStats:
    freq: Counter[int] = Counter()
    last_seen = {n: None for n in universe}
    usable_rows = []
    for row in rows:
        nums = parse_nums(row.get(field))
        if nums:
            usable_rows.append(nums)
    for idx, nums in enumerate(usable_rows):
        freq.update(nums)
        for n in nums:
            last_seen[n] = idx
    total = len(usable_rows)
    omission = {
        n: total if last_seen[n] is None else total - 1 - int(last_seen[n])
        for n in universe
    }
    return HistoryStats(freq=freq, omission=omission, draws=total)


def load_history(path: str | None) -> list[dict[str, str]]:
    if not path:
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def make_weights(stats: HistoryStats, universe: Sequence[int]) -> dict[int, float]:
    if stats.draws <= 0:
        return {n: 1.0 for n in universe}
    max_freq = max([stats.freq.get(n, 0) for n in universe] + [1])
    max_omit = max([stats.omission.get(n, 0) for n in universe] + [1])
    weights = {}
    for n in universe:
        hot = stats.freq.get(n, 0) / max_freq
        cold = stats.omission.get(n, 0) / max_omit
        # A deliberately mild blend: enough to explain the choice, not enough to
        # pretend the next draw remembers the past. Randomness, tragically, has no CRM.
        weights[n] = 1.0 + 0.55 * hot + 0.35 * cold
    return weights


def zone_counts(nums: Sequence[int], zones: Sequence[range]) -> list[int]:
    return [sum(1 for n in nums if n in z) for z in zones]


def odd_even(nums: Sequence[int]) -> tuple[int, int]:
    odd = sum(1 for n in nums if n % 2)
    return odd, len(nums) - odd


def top_items(counter: Counter[int], nums: Sequence[int], n: int = 3) -> list[int]:
    return sorted(nums, key=lambda x: (-counter.get(x, 0), x))[:n]


def top_omissions(omission: dict[int, int], nums: Sequence[int], n: int = 3) -> list[int]:
    return sorted(nums, key=lambda x: (-omission.get(x, 0), x))[:n]


def dlt_jackpot_probability() -> float:
    return 1 / (comb(35, 5) * comb(12, 2))


def kl8_exact_hit_probability(k: int, r: int) -> float:
    """Probability of exactly r hits when choosing k, draw selects 20 from 80."""
    if r < 0 or r > k or 20 - r < 0 or 20 - r > 80 - k:
        return 0.0
    return comb(k, r) * comb(80 - k, 20 - r) / comb(80, 20)


def dlt_valid_front(front: Sequence[int]) -> bool:
    s = sum(front)
    odd, even = odd_even(front)
    zones = zone_counts(front, [range(1, 13), range(13, 25), range(25, 36)])
    return 65 <= s <= 125 and odd in {2, 3} and max(zones) <= 3 and min(zones) >= 1


def generate_dlt(rows: list[dict[str, str]], groups: int, target_date: str, strategy: str) -> str:
    rng = stable_rng(f"dlt|{target_date}|{strategy}")
    front_universe = list(range(1, 36))
    back_universe = list(range(1, 13))
    front_stats = build_stats(rows, "front_numbers", front_universe)
    back_stats = build_stats(rows, "back_numbers", back_universe)
    front_weights = make_weights(front_stats, front_universe)
    back_weights = make_weights(back_stats, back_universe)
    seen: set[tuple[tuple[int, ...], tuple[int, ...]]] = set()
    out = [
        f"# 大乐透每日模拟组合：{target_date}",
        "",
        "> 用途：娱乐研究 + 复盘。不是预测，不是投注承诺，更不是随机数突然开始给人类递纸条。",
        "",
        f"样本期数：{front_stats.draws if front_stats.draws else '未提供历史数据，使用结构化随机'}",
        f"单注一等奖理论概率：{one_in(dlt_jackpot_probability())}，约 {pct(dlt_jackpot_probability())}。",
        "",
        "| 组别 | 前区 | 后区 | 选择理由 | 理论概率 |",
        "|---:|---|---|---|---|",
    ]
    attempts = 0
    while len(seen) < groups and attempts < groups * 1000:
        attempts += 1
        front = sorted(weighted_sample_without_replacement(rng, front_universe, front_weights, 5))
        back = sorted(weighted_sample_without_replacement(rng, back_universe, back_weights, 2))
        if not dlt_valid_front(front):
            continue
        key = (tuple(front), tuple(back))
        if key in seen:
            continue
        seen.add(key)
        f_zones = zone_counts(front, [range(1, 13), range(13, 25), range(25, 36)])
        f_odd, f_even = odd_even(front)
        b_odd, b_even = odd_even(back)
        hot_f = top_items(front_stats.freq, front)
        cold_f = top_omissions(front_stats.omission, front)
        hot_b = top_items(back_stats.freq, back, 1)
        reason_bits = [
            f"前区三区分布 {f_zones[0]}-{f_zones[1]}-{f_zones[2]}",
            f"前区奇偶 {f_odd}:{f_even}",
            f"前区和值 {sum(front)}",
            f"后区奇偶 {b_odd}:{b_even}",
        ]
        if front_stats.draws:
            reason_bits.append(f"兼顾高频前区 {fmt_nums(hot_f)} 与遗漏前区 {fmt_nums(cold_f)}")
        if back_stats.draws:
            reason_bits.append(f"后区参考高频/权重号 {fmt_nums(hot_b)}")
        reason = "；".join(reason_bits)
        out.append(
            f"| {len(seen)} | {fmt_nums(front)} | {fmt_nums(back)} | {reason} | 一等奖 {one_in(dlt_jackpot_probability())}，{pct(dlt_jackpot_probability())} |"
        )
    out += [
        "",
        "## 复盘建议",
        "- 每期把生成组合与开奖号码比对，记录前区命中、后区命中和投入产出。",
        "- 不要因为某组‘看起来顺眼’就加注。顺眼不是统计量，只是人脑在随机噪声里贴墙纸。",
        "- 若连续回测表现差，应降低组数或停止策略，而不是加倍追。",
        "",
    ]
    return "\n".join(out)


def kl8_valid(nums: Sequence[int], k: int) -> bool:
    zones = zone_counts(nums, [range(1, 21), range(21, 41), range(41, 61), range(61, 81)])
    odd, even = odd_even(nums)
    # Avoid extreme concentration. For small k, only require at least two zones.
    if k >= 8 and max(zones) > math.ceil(k / 2):
        return False
    if k >= 6 and not (abs(odd - even) <= 4):
        return False
    if k >= 4 and sum(1 for z in zones if z > 0) < 2:
        return False
    return True


def generate_kl8(rows: list[dict[str, str]], groups: int, target_date: str, strategy: str, choose_k: int) -> str:
    rng = stable_rng(f"kl8|{target_date}|{strategy}|{choose_k}")
    universe = list(range(1, 81))
    stats = build_stats(rows, "numbers", universe)
    weights = make_weights(stats, universe)
    seen: set[tuple[int, ...]] = set()
    top_prob = kl8_exact_hit_probability(choose_k, choose_k)
    out = [
        f"# 快乐8每日模拟组合：{target_date}",
        "",
        f"> 默认按“选{choose_k}”生成。用途：娱乐研究 + 复盘，不是预测。快乐8一次开 20 个号，别把它想成会看你脸色的老虎机。",
        "",
        f"样本期数：{stats.draws if stats.draws else '未提供历史数据，使用结构化随机'}",
        f"选{choose_k}全中理论概率：{one_in(top_prob)}，约 {pct(top_prob)}。",
        "",
        "| 组别 | 号码 | 选择理由 | 理论概率 |",
        "|---:|---|---|---|",
    ]
    attempts = 0
    while len(seen) < groups and attempts < groups * 1000:
        attempts += 1
        nums = sorted(weighted_sample_without_replacement(rng, universe, weights, choose_k))
        if not kl8_valid(nums, choose_k):
            continue
        key = tuple(nums)
        if key in seen:
            continue
        seen.add(key)
        zones = zone_counts(nums, [range(1, 21), range(21, 41), range(41, 61), range(61, 81)])
        odd, even = odd_even(nums)
        hot = top_items(stats.freq, nums, min(4, choose_k))
        cold = top_omissions(stats.omission, nums, min(4, choose_k))
        reason_bits = [
            f"四区分布 {zones[0]}-{zones[1]}-{zones[2]}-{zones[3]}",
            f"奇偶 {odd}:{even}",
            f"和值 {sum(nums)}",
        ]
        if stats.draws:
            reason_bits.append(f"兼顾高频号 {fmt_nums(hot)} 与当前遗漏号 {fmt_nums(cold)}")
        reason = "；".join(reason_bits)
        out.append(
            f"| {len(seen)} | {fmt_nums(nums)} | {reason} | 选{choose_k}全中 {one_in(top_prob)}，{pct(top_prob)} |"
        )
    out += [
        "",
        "## 命中数概率参考",
        "| 命中数 | 理论概率 | 约等于 |",
        "|---:|---:|---:|",
    ]
    for r in range(choose_k, max(-1, choose_k - 6), -1):
        p = kl8_exact_hit_probability(choose_k, r)
        out.append(f"| {r} | {pct(p)} | {one_in(p)} |")
    out += [
        "",
        "## 复盘建议",
        "- 只记录命中数、投入、返奖，不要用一两期结果证明策略‘觉醒’。彩票没有主角光环，只有概率。",
        "- 若做多组覆盖，应先设定每日预算上限，再生成组合。顺序别反了。",
        "",
    ]
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate daily simulated lottery picks with reasons and probabilities.")
    parser.add_argument("--game", choices=["kl8", "dlt"], required=True)
    parser.add_argument("--input", help="Optional normalized CSV history file.")
    parser.add_argument("--groups", type=int, default=5, help="Number of groups to generate.")
    default_date = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    parser.add_argument("--date", default=default_date, help="Target date, YYYY-MM-DD. Default uses Asia/Shanghai date. Same date generates stable picks.")
    parser.add_argument("--strategy", default="balanced", choices=["balanced", "random", "hot_omission"], help="Strategy label used in deterministic seed and weighting.")
    parser.add_argument("--choose-k", type=int, default=10, help="KL8 choose type, 1-10. Default: 10.")
    parser.add_argument("--out", required=True, help="Markdown report output path.")
    args = parser.parse_args()

    if args.groups < 1 or args.groups > 20:
        raise SystemExit("--groups must be between 1 and 20")
    if args.choose_k < 1 or args.choose_k > 10:
        raise SystemExit("--choose-k must be between 1 and 10")
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit("--date must use YYYY-MM-DD") from exc

    rows = load_history(args.input)
    if args.game == "dlt":
        report = generate_dlt(rows, args.groups, args.date, args.strategy)
    else:
        report = generate_kl8(rows, args.groups, args.date, args.strategy, args.choose_k)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"saved daily picks -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
