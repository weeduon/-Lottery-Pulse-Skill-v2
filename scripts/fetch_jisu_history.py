#!/usr/bin/env python3
"""Fetch lottery history from JisuAPI.

Requires env var: JISU_APPKEY
Examples:
  python scripts/fetch_jisu_history.py --game kl8 --limit 1000 --out data/kl8_raw.json
  python scripts/fetch_jisu_history.py --game dlt --limit 1000 --out data/dlt_raw.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

GAME_IDS = {
    "dlt": 14,  # 大乐透
    "kl8": 89,  # 快乐8
}


def fetch_page(appkey: str, caipiaoid: int, start: int, num: int) -> dict[str, Any]:
    url = "https://api.jisuapi.com/caipiao/history"
    params = {
        "appkey": appkey,
        "caipiaoid": caipiaoid,
        "start": start,
        "num": num,
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    if str(data.get("status")) not in {"0", "200"}:
        raise RuntimeError(f"JisuAPI error: {data}")
    return data


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--game", choices=GAME_IDS.keys(), required=True)
    p.add_argument("--limit", type=int, default=1000)
    p.add_argument("--out", required=True)
    p.add_argument("--sleep", type=float, default=0.2)
    args = p.parse_args()

    appkey = os.getenv("JISU_APPKEY")
    if not appkey:
        print("Missing env var JISU_APPKEY", file=sys.stderr)
        return 2

    caipiaoid = GAME_IDS[args.game]
    all_rows: list[dict[str, Any]] = []
    start = 0
    page_size = 20  # JisuAPI docs say max 20.

    while len(all_rows) < args.limit:
        num = min(page_size, args.limit - len(all_rows))
        payload = fetch_page(appkey, caipiaoid, start, num)
        result = payload.get("result") or {}
        rows = result.get("list") or []
        if not rows:
            break
        all_rows.extend(rows)
        start += len(rows)
        time.sleep(args.sleep)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"game": args.game, "source": "jisuapi", "rows": all_rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {len(all_rows)} rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
