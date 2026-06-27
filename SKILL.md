# 玄彩引擎：快乐8 + 大乐透数据分析 Skill

## 目标
面向中国福利彩票「快乐8」与中国体育彩票「超级大乐透」建立一个可复盘的数据分析 Skill。它用于：

1. 收集近 1000 期开奖数据。
2. 标准化开奖、销量、奖池、奖级信息。
3. 计算概率、频率、遗漏、分区、和值、奇偶、大小、连号、重号等指标。
4. 生成候选号码并做历史回测。
5. 每日生成若干组模拟号码，并说明结构理由与理论概率。
6. 明确标注：彩票是随机开奖，本 Skill 不承诺预测未来，不输出“稳赚”“必中”“内部号”等结论。

## 强制工作流
每次分析时按以下顺序执行：

1. **数据拉取**
   - 首选中彩网 / 中国体彩网 / 中国福彩网等官方或半官方页面。
   - 若页面为动态渲染，使用 `scripts/fetch_zhcw_playwright.py`。
   - 若本地环境有 API key，可使用 `scripts/fetch_jisu_history.py` 作为补充源。

2. **数据校验**
   - 快乐8：每期必须 20 个号码，范围 1-80，不重复。
   - 大乐透：前区 5 个号码，范围 1-35；后区 2 个号码，范围 1-12；区内不重复。
   - 期号、日期、号码缺失时不得进入分析。
   - 多源冲突时，以彩票中心官方网站公布为准。

3. **分析输出**
   - 基础统计：频率、遗漏、和值、奇偶、大小、分区。
   - 结构统计：连号、重号、间隔、尾数、AC 值。
   - 风险统计：单注理论概率、回测收益、最大回撤、连亏期数。
   - 候选号码只允许标记为“模拟组合”或“娱乐研究组合”。

4. **每日选号**
   - 使用 `scripts/daily_picks.py` 输出每日 Markdown 组合表。
   - 每组必须包含：号码、选择理由、理论概率、风险提示。
   - 大乐透默认输出一等奖概率：`1 / 21,425,712`。
   - 快乐8默认按“选10”输出全中概率，也支持 `--choose-k 1-10`。
   - 理由只能解释组合结构，例如分区、奇偶、和值、高频、遗漏；不得说成“预测原因”。

5. **回测优先**
   - 任何策略必须先回测最近 N 期。
   - 不允许只凭“热号”“冷号”“玄学感”直接推荐，除非用户明确要求娱乐玩法。

## 输出风格
- 用中文。
- 直接给结论、表格、依据和风险。
- 避免“高概率中奖”“稳胆”“必中”等误导性表达。
- 可以提供多个策略桶：保守低注、覆盖型、随机基准、模型型。

## 支持的彩种代码
- `kl8`: 中国福利彩票快乐8
- `dlt`: 中国体育彩票超级大乐透

## 标准字段
详见 `schemas/draw_schema.md`。

## 常用命令
```bash
pip install -r requirements.txt

# 使用 JisuAPI 拉取快乐8 近1000期，需设置环境变量 JISU_APPKEY
python scripts/fetch_jisu_history.py --game kl8 --limit 1000 --out data/kl8_raw.json

# 使用 JisuAPI 拉取大乐透近1000期
python scripts/fetch_jisu_history.py --game dlt --limit 1000 --out data/dlt_raw.json

# 标准化
python scripts/normalize_draws.py --game kl8 --input data/kl8_raw.json --out data/kl8_1000.csv
python scripts/normalize_draws.py --game dlt --input data/dlt_raw.json --out data/dlt_1000.csv

# 分析
python scripts/analyze_draws.py --game kl8 --input data/kl8_1000.csv --out outputs/kl8_report.md
python scripts/analyze_draws.py --game dlt --input data/dlt_1000.csv --out outputs/dlt_report.md

# 回测
python scripts/backtest.py --game dlt --input data/dlt_1000.csv --strategy random --trials 1000

# 每日生成模拟号码，含选择理由和理论概率
python scripts/daily_picks.py --game dlt --input data/dlt_1000.csv --groups 5 --out outputs/dlt_daily.md
python scripts/daily_picks.py --game kl8 --input data/kl8_1000.csv --choose-k 10 --groups 5 --out outputs/kl8_daily.md
```

## 每日选号输出要求

每日选号报告必须包含：

| 字段 | 要求 |
|---|---|
| 组别 | 从 1 开始编号 |
| 号码 | 快乐8显示所选 k 个号；大乐透分前区/后区 |
| 选择理由 | 只描述结构和历史统计，不使用“必中”“稳胆” |
| 理论概率 | 明确显示单注理论概率，例如 `1 / 21,425,712` |
| 风险提示 | 提醒用户这是娱乐研究，不构成投注建议 |

详见 `rules/probability_notes.md`。

## 禁止事项
- 不声称能破解开奖算法。
- 不生成“内部消息”“杀号必中”等欺诈话术。
- 不建议超预算投注。
- 不把短期命中包装成长期稳定优势。
