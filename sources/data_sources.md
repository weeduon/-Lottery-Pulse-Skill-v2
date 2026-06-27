# 数据源清单

## 首选源

### 中彩网快乐8往期页
- URL: https://www.zhcw.com/kjxx/kl8/
- 特点：支持近 30 / 50 / 100 期与自定义查询，页面提示最多 1000 期。
- 字段：期号、开奖日期、开奖号码、总销售额、详情。

### 中彩网大乐透往期页
- URL: https://www.zhcw.com/kjxx/dlt/
- 特点：支持近 30 / 50 / 100 期与自定义查询，页面提示最多 1000 期。
- 字段：期号、开奖日期、前区、后区、销售额、一二等奖、奖池等。

### 中国体彩网超级大乐透历史页
- URL: https://www.lottery.gov.cn/zst/dlt/
- 特点：官方体彩历史数据页。

## 备选 API

### JisuAPI 彩票开奖接口
- 历史开奖接口：`https://api.jisuapi.com/caipiao/history`
- 参数：`appkey`, `caipiaoid`, `start`, `num`
- 文档显示：`num` 最大 20，需要分页。
- 彩种 ID：大乐透 `14`，快乐8 `89`。

### 接口盒子 快乐8
- URL: https://cn.apihz.cn/api/caipiao/kuaile8.php
- 适合查询快乐8最新或指定期号。
- 需要开发者 ID 与 KEY。

## 数据可信原则

1. 多源冲突时，以彩票中心官方数据为准。
2. 第三方 API 只作为自动化备份源。
3. 所有数据进入分析前必须校验号码数量、范围和重复情况。
