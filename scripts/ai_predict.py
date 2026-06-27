#!/usr/bin/env python3
"""AI-style lottery analysis and simulated picks.

Inspired by public product patterns such as moving-average analysis, omission
analysis, trend analysis and AI scoring. This is statistical tooling, not a
promise to predict random lottery draws.
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
from pathlib import Path
from statistics import mean
from typing import Iterable, Sequence


@dataclass
class NumberStats:
    freq: Counter[int]
    recent_freq: Counter[int]
    omission: dict[int, int]
    ma5: dict[int, float]
    ma10: dict[int, float]
    ma20: dict[int, float]
    draws: int


def parse_nums(value: str | None) -> list[int]:
    if not value:
        return []
    return [int(x) for x in str(value).replace(',', ' ').split() if x.strip()]


def fmt_nums(nums: Sequence[int]) -> str:
    return ' '.join(f'{n:02d}' for n in nums)


def stable_rng(seed_text: str) -> random.Random:
    digest = hashlib.sha256(seed_text.encode('utf-8')).hexdigest()
    return random.Random(int(digest[:16], 16))


def load_rows(path: str) -> list[dict[str, str]]:
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def moving_rate(draws: list[list[int]], universe: Sequence[int], window: int) -> dict[int, float]:
    sample = draws[:window]
    if not sample:
        return {n: 0.0 for n in universe}
    c = Counter()
    for nums in sample:
        c.update(nums)
    return {n: c[n] / len(sample) for n in universe}


def build_stats(rows: list[dict[str, str]], field: str, universe: Iterable[int]) -> NumberStats:
    u = list(universe)
    draws = [parse_nums(row.get(field)) for row in rows if parse_nums(row.get(field))]
    freq: Counter[int] = Counter()
    recent_freq: Counter[int] = Counter()
    last_seen = {n: None for n in u}
    for idx, nums in enumerate(draws):
        freq.update(nums)
        for n in nums:
            last_seen[n] = idx
    for weight_idx, nums in enumerate(draws[:20]):
        weight = max(1, 20 - weight_idx)
        for n in nums:
            recent_freq[n] += weight
    total = len(draws)
    omission = {n: total if last_seen[n] is None else total - 1 - int(last_seen[n]) for n in u}
    return NumberStats(
        freq=freq,
        recent_freq=recent_freq,
        omission=omission,
        ma5=moving_rate(draws, u, 5),
        ma10=moving_rate(draws, u, 10),
        ma20=moving_rate(draws, u, 20),
        draws=total,
    )


def norm(value: float, max_value: float) -> float:
    return 0.0 if max_value <= 0 else value / max_value


def score_numbers(stats: NumberStats, universe: Sequence[int], rng: random.Random) -> dict[int, float]:
    max_freq = max([stats.freq.get(n, 0) for n in universe] + [1])
    max_recent = max([stats.recent_freq.get(n, 0) for n in universe] + [1])
    max_omit = max([stats.omission.get(n, 0) for n in universe] + [1])
    scores = {}
    for n in universe:
        hot_score = norm(stats.freq.get(n, 0), max_freq)
        miss_score = norm(stats.omission.get(n, 0), max_omit)
        trend_score = norm(stats.recent_freq.get(n, 0), max_recent)
        ma_signal = 0.45 * stats.ma5.get(n, 0) + 0.35 * stats.ma10.get(n, 0) + 0.20 * stats.ma20.get(n, 0)
        noise = rng.random() * 0.03
        scores[n] = 0.30 * hot_score + 0.25 * miss_score + 0.25 * trend_score + 0.17 * ma_signal + noise
    return scores


def weighted_sample(rng: random.Random, universe: Sequence[int], scores: dict[int, float], k: int) -> list[int]:
    pool = list(universe)
    chosen: list[int] = []
    for _ in range(k):
        total = sum(max(scores.get(n, 0.001), 0.001) for n in pool)
        mark = rng.random() * total
        acc = 0.0
        pick = pool[-1]
        for n in pool:
            acc += max(scores.get(n, 0.001), 0.001)
            if acc >= mark:
                pick = n
                break
        chosen.append(pick)
        pool.remove(pick)
    return sorted(chosen)


def zone_counts(nums: Sequence[int], zones: Sequence[range]) -> list[int]:
    return [sum(1 for n in nums if n in z) for z in zones]


def odd_even(nums: Sequence[int]) -> tuple[int, int]:
    odd = sum(1 for n in nums if n % 2)
    return odd, len(nums) - odd


def confidence(score: float) -> str:
    if score >= 80:
        return '高'
    if score >= 65:
        return '中'
    return '低'


def one_in(prob: float) -> str:
    return '∞' if prob <= 0 else f'1 / {round(1 / prob):,}'


def pct(prob: float) -> str:
    return f'{prob * 100:.10f}%'


def dlt_jackpot_prob() -> float:
    return 1 / (math.comb(35, 5) * math.comb(12, 2))


def kl8_full_hit_prob(k: int) -> float:
    return math.comb(80 - k, 20 - k) / math.comb(80, 20)


def combo_score(nums: Sequence[int], scores: dict[int, float], bonus: float, penalty: float = 0.0) -> float:
    raw = mean(scores[n] for n in nums) if nums else 0.0
    return max(0.0, min(100.0, raw * 100 + bonus - penalty))


def dlt_structure(front: Sequence[int], back: Sequence[int]) -> tuple[float, list[str], bool]:
    zones = zone_counts(front, [range(1, 13), range(13, 25), range(25, 36)])
    odd, even = odd_even(front)
    b_odd, b_even = odd_even(back)
    front_sum = sum(front)
    bonus = 0.0
    ok = True
    reasons = [f'三区 {zones[0]}-{zones[1]}-{zones[2]}', f'前区奇偶 {odd}:{even}', f'前区和值 {front_sum}', f'后区奇偶 {b_odd}:{b_even}']
    if min(zones) >= 1 and max(zones) <= 3:
        bonus += 12
    else:
        ok = False
    if odd in {2, 3}:
        bonus += 8
    if 65 <= front_sum <= 125:
        bonus += 8
    else:
        ok = False
    if b_odd in {1, 2}:
        bonus += 4
    return bonus, reasons, ok


def kl8_structure(nums: Sequence[int], k: int) -> tuple[float, list[str], bool]:
    zones = zone_counts(nums, [range(1, 21), range(21, 41), range(41, 61), range(61, 81)])
    odd, even = odd_even(nums)
    bonus = 0.0
    ok = True
    reasons = [f'四区 {zones[0]}-{zones[1]}-{zones[2]}-{zones[3]}', f'奇偶 {odd}:{even}', f'和值 {sum(nums)}']
    if sum(1 for z in zones if z > 0) >= min(4, max(2, k // 3)):
        bonus += 10
    else:
        ok = False
    if k < 6 or abs(odd - even) <= 4:
        bonus += 8
    if k >= 8 and max(zones) <= math.ceil(k / 2):
        bonus += 8
    return bonus, reasons, ok


def top_by(data: dict[int, float] | Counter[int], nums: Sequence[int], n: int = 3) -> list[int]:
    return sorted(nums, key=lambda x: (-float(data.get(x, 0)), x))[:n]


def make_dlt_report(rows: list[dict[str, str]], groups: int, target_date: str) -> str:
    rng = stable_rng(f'ai-dlt|{target_date}|{groups}')
    front_u = list(range(1, 36))
    back_u = list(range(1, 13))
    front_stats = build_stats(rows, 'front_numbers', front_u)
    back_stats = build_stats(rows, 'back_numbers', back_u)
    front_scores = score_numbers(front_stats, front_u, rng)
    back_scores = score_numbers(back_stats, back_u, rng)
    seen: set[tuple[tuple[int, ...], tuple[int, ...]]] = set()
    lines = [
        f'# 大乐透 AI模拟预测：{target_date}', '',
        '> 参考均线分析、遗漏宝、趋势宝的产品形态：看指标，不装神。AI评分不改变理论中奖概率。', '',
        f'样本期数：{front_stats.draws}',
        f'单注一等奖理论概率：{one_in(dlt_jackpot_prob())}，约 {pct(dlt_jackpot_prob())}。', '',
        '| 组别 | 前区 | 后区 | AI评分 | 结构置信度 | 选择理由 | 理论概率 |',
        '|---:|---|---|---:|---|---|---|',
    ]
    attempts = 0
    while len(seen) < groups and attempts < groups * 1500:
        attempts += 1
        front = weighted_sample(rng, front_u, front_scores, 5)
        back = weighted_sample(rng, back_u, back_scores, 2)
        key = (tuple(front), tuple(back))
        if key in seen:
            continue
        bonus, reasons, ok = dlt_structure(front, back)
        if not ok:
            continue
        score = combo_score(front + back, {**front_scores, **back_scores}, bonus)
        hot = fmt_nums(top_by(front_stats.freq, front, 3))
        miss = fmt_nums(top_by(front_stats.omission, front, 3))
        trend = fmt_nums(top_by(front_stats.recent_freq, front, 3))
        reason = '；'.join(reasons + [f'热号 {hot}', f'遗漏关注 {miss}', f'近期趋势 {trend}'])
        seen.add(key)
        lines.append(f'| {len(seen)} | {fmt_nums(front)} | {fmt_nums(back)} | {score:.1f} | {confidence(score)} | {reason} | 一等奖 {one_in(dlt_jackpot_prob())} |')
    lines += ['', '## 风险提示', 'AI评分只表示组合结构与历史统计特征，不表示中奖概率提升。彩票开奖结果具有随机性，请控制预算，勿追投。']
    return '\n'.join(lines)


def make_kl8_report(rows: list[dict[str, str]], groups: int, target_date: str, k: int) -> str:
    rng = stable_rng(f'ai-kl8|{target_date}|{groups}|{k}')
    universe = list(range(1, 81))
    stats = build_stats(rows, 'numbers', universe)
    scores = score_numbers(stats, universe, rng)
    seen: set[tuple[int, ...]] = set()
    prob = kl8_full_hit_prob(k)
    lines = [
        f'# 快乐8 AI模拟预测：{target_date}', '',
        f'> 参考均线、遗漏、趋势三类指标生成。默认选{k}，AI评分不是中奖率。', '',
        f'样本期数：{stats.draws}',
        f'选{k}全中理论概率：{one_in(prob)}，约 {pct(prob)}。', '',
        '| 组别 | 号码 | AI评分 | 结构置信度 | 选择理由 | 理论概率 |',
        '|---:|---|---:|---|---|---|',
    ]
    attempts = 0
    while len(seen) < groups and attempts < groups * 1500:
        attempts += 1
        nums = weighted_sample(rng, universe, scores, k)
        key = tuple(nums)
        if key in seen:
            continue
        bonus, reasons, ok = kl8_structure(nums, k)
        if not ok:
            continue
        score = combo_score(nums, scores, bonus)
        hot = fmt_nums(top_by(stats.freq, nums, min(4, k)))
        miss = fmt_nums(top_by(stats.omission, nums, min(4, k)))
        trend = fmt_nums(top_by(stats.recent_freq, nums, min(4, k)))
        reason = '；'.join(reasons + [f'热号 {hot}', f'遗漏关注 {miss}', f'近期趋势 {trend}'])
        seen.add(key)
        lines.append(f'| {len(seen)} | {fmt_nums(nums)} | {score:.1f} | {confidence(score)} | {reason} | 全中 {one_in(prob)} |')
    lines += ['', '## 风险提示', 'AI评分只表示组合结构与历史统计特征，不表示中奖概率提升。彩票开奖结果具有随机性，请控制预算，勿追投。']
    return '\n'.join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description='AI-style lottery scoring and simulated picks')
    p.add_argument('--game', choices=['dlt', 'kl8'], required=True)
    p.add_argument('--input', required=True)
    p.add_argument('--groups', type=int, default=5)
    p.add_argument('--choose-k', type=int, default=10)
    p.add_argument('--date', default=datetime.now().date().isoformat())
    p.add_argument('--out', required=True)
    args = p.parse_args()
    if not 1 <= args.groups <= 20:
        raise SystemExit('--groups must be between 1 and 20')
    if not 1 <= args.choose_k <= 10:
        raise SystemExit('--choose-k must be between 1 and 10')
    rows = load_rows(args.input)
    report = make_dlt_report(rows, args.groups, args.date) if args.game == 'dlt' else make_kl8_report(rows, args.groups, args.date, args.choose_k)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding='utf-8')
    print(f'saved AI prediction report -> {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
