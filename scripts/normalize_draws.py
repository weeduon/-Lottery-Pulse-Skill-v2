#!/usr/bin/env python3
"""Normalize raw lottery JSON/CSV into a standard CSV schema."""
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

STANDARD_FIELDS = [
    "game", "issue", "draw_date", "numbers", "front_numbers", "back_numbers",
    "sale_amount", "pool_amount", "source", "fetched_at"
]


def clean_num_string(s: str) -> str:
    nums = re.findall(r"\d{1,2}", s or "")
    return " ".join(f"{int(x):02d}" for x in nums)


def normalize_jisu(game: str, payload: dict[str, Any]) -> list[dict[str, str]]:
    rows = payload.get("rows") or payload.get("result", {}).get("list") or []
    out = []
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    for r in rows:
        issue = str(r.get("issueno") or r.get("qihao") or "").strip()
        draw_date = str(r.get("opendate") or r.get("time") or "").split("(")[0].strip()
        number = str(r.get("number") or "")
        refer = str(r.get("refernumber") or "")
        row = {
            "game": game,
            "issue": issue,
            "draw_date": draw_date,
            "numbers": "",
            "front_numbers": "",
            "back_numbers": "",
            "sale_amount": str(r.get("saleamount") or r.get("xiaoshou") or ""),
            "pool_amount": str(r.get("totalmoney") or r.get("jiangchi") or ""),
            "source": payload.get("source", "jisuapi"),
            "fetched_at": now,
        }
        if game == "kl8":
            row["numbers"] = clean_num_string(number)
        elif game == "dlt":
            row["front_numbers"] = clean_num_string(number)
            row["back_numbers"] = clean_num_string(refer)
            # Some APIs put all 7 numbers in number and empty refernumber.
            nums = row["front_numbers"].split()
            if len(nums) == 7 and not row["back_numbers"]:
                row["front_numbers"] = " ".join(nums[:5])
                row["back_numbers"] = " ".join(nums[5:])
        out.append(row)
    return out


def validate_row(row: dict[str, str]) -> list[str]:
    errors = []
    game = row["game"]
    if game == "kl8":
        nums = [int(x) for x in row["numbers"].split()]
        if len(nums) != 20:
            errors.append(f"KL8 expected 20 numbers, got {len(nums)}")
        if any(x < 1 or x > 80 for x in nums):
            errors.append("KL8 number out of range")
        if len(nums) != len(set(nums)):
            errors.append("KL8 duplicate number")
    elif game == "dlt":
        front = [int(x) for x in row["front_numbers"].split()]
        back = [int(x) for x in row["back_numbers"].split()]
        if len(front) != 5:
            errors.append(f"DLT expected 5 front numbers, got {len(front)}")
        if len(back) != 2:
            errors.append(f"DLT expected 2 back numbers, got {len(back)}")
        if any(x < 1 or x > 35 for x in front):
            errors.append("DLT front number out of range")
        if any(x < 1 or x > 12 for x in back):
            errors.append("DLT back number out of range")
        if len(front) != len(set(front)) or len(back) != len(set(back)):
            errors.append("DLT duplicate number")
    return errors


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--game", choices=["kl8", "dlt"], required=True)
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--strict", action="store_true")
    args = p.parse_args()

    inp = Path(args.input)
    if inp.suffix.lower() == ".json":
        payload = json.loads(inp.read_text(encoding="utf-8"))
        rows = normalize_jisu(args.game, payload)
    else:
        raise SystemExit("Currently normalizer supports JSON from fetch_jisu_history.py. For ZHCW raw CSV, add a site-specific parser after inspecting raw_text.")

    valid_rows = []
    for row in rows:
        errors = validate_row(row)
        if errors:
            msg = f"{row.get('issue')}: {'; '.join(errors)}"
            if args.strict:
                raise ValueError(msg)
            print("skip", msg)
            continue
        valid_rows.append(row)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=STANDARD_FIELDS)
        writer.writeheader()
        writer.writerows(valid_rows)
    print(f"saved {len(valid_rows)} normalized rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
