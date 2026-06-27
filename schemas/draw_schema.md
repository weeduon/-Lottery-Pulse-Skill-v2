# 标准化开奖数据 Schema

## 通用字段

| 字段 | 类型 | 说明 |
|---|---|---|
| game | string | `kl8` 或 `dlt` |
| issue | string | 期号 |
| draw_date | date | 开奖日期，YYYY-MM-DD |
| numbers | string | 快乐8用 20 个号码；大乐透可为空 |
| front_numbers | string | 大乐透前区号码，空格分隔 |
| back_numbers | string | 大乐透后区号码，空格分隔 |
| sale_amount | decimal | 当期销售额，可为空 |
| pool_amount | decimal | 奖池金额，可为空 |
| source | string | 数据来源 |
| fetched_at | datetime | 拉取时间 |

## 快乐8校验

- `numbers` 必须有 20 个号码。
- 每个号码范围 1-80。
- 不允许重复。

## 大乐透校验

- `front_numbers` 必须 5 个，范围 1-35。
- `back_numbers` 必须 2 个，范围 1-12。
- 区内不允许重复。
