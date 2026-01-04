# Polymarket 信号检测算法规格说明

## 一、市场背景

### 1.1 什么是 Polymarket

Polymarket 是基于 Polygon 区块链的去中心化预测市场平台，2020年创立，总部纽约。

**核心机制：**
- 用户对真实世界事件结果进行交易（政治、体育、加密货币等）
- 每个市场有两种份额：**YES** 和 **NO**
- 份额价格在 **$0.01 ~ $0.99** 之间浮动
- 价格反映市场对该结果发生概率的共识（$0.65 = 65% 概率）

### 1.2 结算规则

| 事件结果 | YES 份额 | NO 份额 |
|---------|---------|---------|
| 事件发生 | 结算为 $1 | 结算为 $0 |
| 事件未发生 | 结算为 $0 | 结算为 $1 |

**关键约束：YES价格 + NO价格 ≈ $1.00**

---

## 二、信号检测算法

### 2.1 套利检测 (Arbitrage)

**原理：** 当 YES + NO < 1.0 时，同时买入两边可无风险获利。

**数据来源（优先级）：**
1. `clob_market.price_change` 的 `ba` (best_ask)
2. `clob_market.agg_orderbook` 的 `asks[0].price` + 深度
3. `activity.trades` 的 `price` (降级)

**算法：**
```
sum = YES_ask + NO_ask
if sum >= 1.0: 无套利

grossProfit = 1.0 - sum
totalFee = sum * 0.2% * 2      // 双边手续费
totalSlippage = sum * 0.5% * 2 // 双边滑点
netProfit = grossProfit - totalFee - totalSlippage

if netProfit >= 0.3% 
   AND YES深度 >= $100 
   AND NO深度 >= $100
   AND 价格数据 < 60秒
   AND YES/NO时间差 < 30秒:
   触发信号
```

**配置：**
- MIN_PROFIT=0.3%
- TRADING_FEE=0.2% (双边)
- SLIPPAGE=0.5% (双边)
- MIN_DEPTH=$100
- MAX_PRICE_AGE=60秒
- MAX_PRICE_TIME_DIFF=30秒
- COOLDOWN=3秒

---

### 2.2 订单簿失衡 (Orderbook Imbalance)

**原理：** 买卖深度严重失衡预示价格将向深度大的方向移动。

**数据来源：** `clob_market.agg_orderbook`

**算法：**
```
buyDepth = Σ(前3档 bid.size)
sellDepth = Σ(前3档 ask.size)

if buyDepth > sellDepth: direction = BULLISH, imbalance = buyDepth/sellDepth
if sellDepth > buyDepth: direction = BEARISH, imbalance = sellDepth/buyDepth

if imbalance >= 1.1x 
   AND max(buyDepth, sellDepth) >= $10
   AND priceImpact >= 1.0%:
   触发信号
```

**配置：**
- MIN_IMBALANCE=1.1x
- MIN_DEPTH=$10
- MIN_PRICE_IMPACT=1.0%
- COOLDOWN=0.5秒

---

### 2.3 扫尾盘 (Closing Scanner)

**原理：** 即将结束且概率极端(≥95%)的市场，结果几乎确定。

**数据来源：** Gamma API

**算法：**
```
过滤: 168小时内结束 + YES≥95% 或 NO≥95%
评分（得分优先排序）:
  - 剩余时间 ≤2h: +40分 (HIGH)
  - 剩余时间 ≤12h: +25分 (MEDIUM)
  - 成交量 >$200K: +25分
  - 流动性 >$100K: +20分
  - 概率 ≥95%: +30分
```

**配置：** TIME_WINDOW=168小时, SCAN_INTERVAL=5分钟

---

## 三、用户档位

| 档位 | 套利 | 订单簿 | 扫尾盘 |
|-----|-----|-------|-------|
| 1 宽松 | ≥2.0% | ≥3x + $20K | 任意 |
| 2 中等 | ≥4.0% | ≥6x + $100K | 中等置信度 |
| 3 严格 | ≥8.0% | ≥12x + $200K | 高置信度 |

**注意：** 算法检测阈值(0.3%)低于用户档位1阈值(2.0%)，这是设计如此，允许记录更多机会但只推送符合用户设置的信号。

---

## 四、数据流

```
WebSocket → 消息分发 → 检测器 → 信号聚合 → 用户阈值过滤 → Telegram推送
```

---

## 五、修复记录 (2025-12-23)

1. **套利手续费计算** - 改为双边按成交额比例扣减
2. **套利滑点计算** - 新增双边滑点扣减
3. **套利深度检查** - 新增YES/NO双边深度校验
4. **套利价格过期** - 新增价格数据有效期和时间差检查
5. **订单簿minPriceImpact** - 从配置读取，不再硬编码
6. **扫尾盘排序** - 改为得分优先（与注释一致）

*文档时间: 2025-12-23*
