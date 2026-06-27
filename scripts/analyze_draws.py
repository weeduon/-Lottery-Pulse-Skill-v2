#!/usr/bin/env python3
"""Generate simple markdown analysis report from normalized CSV.

This script deliberately avoids pandas.DataFrame.to_markdown(), because that
method requires the optional tabulate package. Fewer optional dependency traps,
fewer tiny software landmines for humans to step on.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd


def parse_nums(s: str) -> list[int]:
    return [int(x) for x in str(s).split() if str(x).strip()]


def freq_table(series: pd.Series, universe: range) -> pd.DataFrame:
    c = Counter()
    for s in series.dropna():
        c.update(parse_nums(s))
    return pd.DataFrame({"number": list(universe), "count": [c[i] for i in universe]}).sort_values(["count", "number"], ascending=[False, True])


def omission(series: pd.Series, universe: range) -> pd.DataFrame:
    last_seen = {i: None for i in universe}
    vals = list(series.dropna())
    for idx, s in enumerate(vals):
        for n in parse_nums(s):
            last_seen[n] = idx
    total = len(vals)
    rows = []
    for n in universe:
        rows.append({"number": n, "omission": total if last_seen[n] is None else total - 1 - last_seen[n]})
    return pd.DataFrame(rows).sort_values(["omission", "number"], ascending=[False, True])


def md_table(df: pd.DataFrame, n: int = 10) -> str:
    """Render a tiny GitHub-flavored Markdown table without optional deps."""
    head = df.head(n).copy()
    cols = list(head.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |"]
    lines.append("| " + " | ".join("---" for _ in cols) + " |")
    for _, row in head.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--game", choices=["kl8", "dlt"], required=True)
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    df = pd.read_csv(args.input)
    lines = [f"# {args.game.upper()} 历史数据分析报告", "", f"样本期数：{len(df)}", ""]

    if args.game == "kl8":
        freq = freq_table(df["numbers"], range(1, 81))
        omit = omission(df["numbers"], range(1, 81))
        lines += ["## 出现频率 Top 10", md_table(freq), "", "## 当前遗漏 Top 10", md_table(omit), ""]
        sums = df["numbers"].apply(lambda s: sum(parse_nums(s)))
        lines += ["## 和值", f"平均和值：{sums.mean():.2f}", f"最小/最大和值：{sums.min()} / {sums.max()}", ""]
    else:
        ff = freq_table(df["front_numbers"], range(1, 36))
        fb = freq_table(df["back_numbers"], range(1, 13))
        of = omission(df["front_numbers"], range(1, 36))
        ob = omission(df["back_numbers"], range(1, 13))
        lines += ["## 前区频率 Top 10", md_table(ff), "", "## 后区频率 Top 10", md_table(fb), ""]
        lines += ["## 前区遗漏 Top 10", md_table(of), "", "## 后区遗漏 Top 10", md_table(ob), ""]
        sums = df["front_numbers"].apply(lambda s: sum(parse_nums(s)))
        lines += ["## 前区和值", f"平均和值：{sums.mean():.2f}", f"最小/最大和值：{sums.min()} / {sums.max()}", ""]

    lines += ["## 风险提示", "以上只是历史统计，不代表下一期开奖结果。随机数不欠你一个解释。", ""]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"saved report -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
