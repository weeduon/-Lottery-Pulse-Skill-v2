# 玄彩引擎 Lottery Pulse Skill

这是一个面向「快乐8」与「超级大乐透」的数据收集、统计分析、模拟选号、AI评分、回测复盘 Skill 包。适合安装到 Codex、Marvis、OpenClaw 或作为本地 Python 工程使用。名字取了个玄乎的，主要是为了让随机数感到一点压力，虽然它大概率毫无感觉。

## 功能

- 收集近 1000 期历史开奖数据。
- 标准化为 CSV。
- 计算频率、遗漏、和值、奇偶、大小、分区、连号、重号等指标。
- 增加类彩虹多多产品形态的均线分析、遗漏分析、趋势分析和 AI组合评分。
- 支持快乐8与大乐透的理论概率计算。
- 支持模拟策略回测。
- 支持每日生成若干组模拟号码，并说明选择理由与理论概率。
- 生成可复盘报告，不输出“必中”玄学废话。

## 数据来源建议

1. 中彩网快乐8往期页：支持按期数查询，页面提示最多 1000 期。
2. 中彩网大乐透往期页：支持按期数查询，页面提示最多 1000 期。
3. 中国体彩网超级大乐透历史开奖号码页。
4. 第三方 API 备选：JisuAPI、接口盒子等，适合自动化，但需 key 或有频次限制。

## 安装

```bash
cd lottery-pulse-skill
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 使用 JisuAPI 拉取数据

```bash
export JISU_APPKEY="你的key"
python scripts/fetch_jisu_history.py --game kl8 --limit 1000 --out data/kl8_raw.json
python scripts/fetch_jisu_history.py --game dlt --limit 1000 --out data/dlt_raw.json
```

JisuAPI 文档里历史开奖接口单次 `num` 最大 20，所以脚本会自动分页到 1000 期。

## 使用中彩网页面拉取

中彩网页面是动态渲染。如果普通 requests 拿不到真实表格，就用 Playwright：

```bash
pip install playwright
playwright install chromium
python scripts/fetch_zhcw_playwright.py --game kl8 --limit 1000 --out data/kl8_zhcw.csv
python scripts/fetch_zhcw_playwright.py --game dlt --limit 1000 --out data/dlt_zhcw.csv
```

## 标准化与分析

```bash
python scripts/normalize_draws.py --game kl8 --input data/kl8_raw.json --out data/kl8_1000.csv
python scripts/analyze_draws.py --game kl8 --input data/kl8_1000.csv --out outputs/kl8_report.md
```

## 类彩虹多多 AI预测/评分报告

公开产品页中常见的工具形态包括均线分析、遗漏宝、趋势宝。本项目参考这种“工具化分析”形式，但不抓取其数据、不复刻其内容，只实现自己的统计评分报告。

大乐透 AI评分 5 组：

```bash
python scripts/ai_predict.py --game dlt --input data/dlt_1000.csv --groups 5 --out outputs/dlt_ai_predict.md
```

快乐8 AI评分 5 组，按选10：

```bash
python scripts/ai_predict.py --game kl8 --input data/kl8_1000.csv --choose-k 10 --groups 5 --out outputs/kl8_ai_predict.md
```

AI报告会输出：

| 内容 | 说明 |
|---|---|
| AI评分 | 由热度、遗漏、近期趋势、5/10/20期均线和结构平衡综合计算 |
| 结构置信度 | 只表示组合结构是否均衡，不表示中奖概率 |
| 选择理由 | 热号、遗漏关注、趋势信号、分区、奇偶、和值 |
| 理论概率 | 使用组合数学计算，不随 AI评分改变 |

## 每日生成几组号码

大乐透每日 5 组：

```bash
python scripts/daily_picks.py --game dlt --input data/dlt_1000.csv --groups 5 --out outputs/dlt_daily.md
```

快乐8每日 5 组，默认按“选10”：

```bash
python scripts/daily_picks.py --game kl8 --input data/kl8_1000.csv --choose-k 10 --groups 5 --out outputs/kl8_daily.md
```

不传历史数据也可以生成结构化随机组合：

```bash
python scripts/daily_picks.py --game dlt --groups 5 --out outputs/dlt_daily.md
python scripts/daily_picks.py --game kl8 --choose-k 10 --groups 5 --out outputs/kl8_daily.md
```

每日报告会输出：

| 内容 | 说明 |
|---|---|
| 号码组合 | 大乐透分前区/后区；快乐8按选几展示 |
| 选择理由 | 分区、奇偶、和值、高频、遗漏等结构依据 |
| 理论概率 | 大乐透一等奖概率、快乐8对应选法全中概率 |
| 复盘建议 | 用于记录命中，不用于神化策略 |

概率说明见 `rules/probability_notes.md`。

## 风险声明

彩票开奖结果具有强随机性。统计分析、机器学习候选、历史回测只能用于学习和复盘，不构成投注建议。别让 2 元钱彩票长出 200 万元的幻觉，人类已经够辛苦了。
