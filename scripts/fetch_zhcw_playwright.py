#!/usr/bin/env python3
"""Fetch history rows from ZHCW dynamic pages using Playwright.

This script is intentionally defensive because public pages change selectors whenever
someone sneezes near the front-end team.

Examples:
  python scripts/fetch_zhcw_playwright.py --game kl8 --limit 1000 --out data/kl8_zhcw.csv
  python scripts/fetch_zhcw_playwright.py --game dlt --limit 1000 --out data/dlt_zhcw.csv
"""
from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path

GAME_URLS = {
    "kl8": "https://www.zhcw.com/kjxx/kl8/",
    "dlt": "https://www.zhcw.com/kjxx/dlt/",
}


def parse_numbers(text: str) -> list[str]:
    return re.findall(r"\b\d{1,2}\b", text)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--game", choices=GAME_URLS.keys(), required=True)
    p.add_argument("--limit", type=int, default=1000)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    from playwright.sync_api import sync_playwright

    url = GAME_URLS[args.game]
    rows_out: list[dict[str, str]] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1200})
        page.goto(url, wait_until="networkidle", timeout=60000)

        # Try to click/query the "按期数" input and fill limit.
        # This may need small adjustment if the site changes its front-end.
        text_inputs = page.locator("input").all()
        for inp in text_inputs:
            try:
                if inp.is_visible():
                    inp.fill(str(args.limit))
                    break
            except Exception:
                pass

        # Click a likely query button.
        for label in ["开始查询", "查询", "我要查最近"]:
            try:
                btn = page.get_by_text(label).first
                if btn.is_visible():
                    btn.click()
                    page.wait_for_timeout(3000)
                    break
            except Exception:
                pass

        # Extract table-like rows.
        trs = page.locator("table tr").all()
        for tr in trs:
            text = " ".join(tr.inner_text().split())
            if not text or "期号" in text:
                continue
            # Expected rough pattern: issue date numbers ...
            m_issue = re.search(r"\b(20\d{5}|\d{5})\b", text)
            if not m_issue:
                continue
            rows_out.append({
                "game": args.game,
                "raw_text": text,
                "source": "zhcw_playwright",
                "fetched_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            })
            if len(rows_out) >= args.limit:
                break

        browser.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["game", "raw_text", "source", "fetched_at"])
        writer.writeheader()
        writer.writerows(rows_out)
    print(f"saved {len(rows_out)} raw rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
