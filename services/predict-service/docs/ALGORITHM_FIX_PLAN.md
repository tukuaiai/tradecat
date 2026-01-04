# Polymarket 信号检测修复计划报告

文档时间：2025-12-23

## 目标与范围
本报告聚焦以下模块的真实代码修复计划：套利（arbitrage）、订单簿失衡（orderbook）、扫尾盘（closing）。

## 修复清单（是什么 / 为什么 / 怎么做）

### 1) 套利净利润计算修复
- 是什么  
  当前净利润公式仅扣一次固定费率，且为绝对值扣减。
- 为什么  
  对不同价位的市场会产生系统性偏差，导致阈值判断失真。
- 怎么做  
  按成交额比例扣费与滑点：  
  `net = 1 - sum - feeRate*sum - slippageRate*sum`

### 2) 套利深度检查（可成交性）
- 是什么  
  套利检测仅用 best ask，不校验盘口深度。
- 为什么  
  极薄盘口会产生假阳性。
- 怎么做  
  从 agg_orderbook 收集前 N 档 ask 深度（美元面值），要求 YES/NO 双边深度满足门槛。

### 3) 订单簿 minPriceImpact 配置生效
- 是什么  
  价格冲击阈值硬编码为 1%，配置项未使用。
- 为什么  
  配置无效，调参失控。
- 怎么做  
  引入 `MIN_PRICE_IMPACT` 并替换硬编码判断。

### 4) 扫尾盘排序规则一致性
- 是什么  
  注释说“按得分优先”，代码却先按剩余时间排序。
- 为什么  
  预期与实际不一致，影响解释性。
- 怎么做  
  二选一：  
  A) 改排序逻辑为“先 score 再 timeRemaining”；  
  B) 改注释为“先 timeRemaining 再 score”。

### 5) 文档/阈值一致性（建议）
- 是什么  
  文档阈值与用户阈值判断存在偏差。
- 为什么  
  用户侧理解与实际触发不一致。
- 怎么做  
  同步 userManager 阈值与算法说明文档。

## 影响的数据与字段（详细）

### 套利模块
数据源：
- clob_market.price_change -> pc[].ba
- clob_market.agg_orderbook -> asks[].price / asks[].size
- activity.trades -> price（降级）

建议新增缓存字段（priceCache）：
- askDepthUsd: 前 N 档 ask 深度之和
- askLevels: 前 N 档明细（可选）
- source: price_change / orderbook / trade
- updatedAt: 时间戳（用于过期判断）

### 订单簿模块
关键字段：
- buyDepth, sellDepth, imbalance, priceImpact, spread

### 扫尾盘模块
关键字段：
- hoursLeft, volume, liquidity, yesPrice, noPrice, score

## 涉及函数与文件（到函数级）

套利检测：
- services/polymarket/signals/arbitrage/detector.js
  - processOrderbook()
  - updateCache()
  - detect()

订单簿失衡：
- services/polymarket/signals/orderbook/detector.js
  - constructor()
  - detect()

扫尾盘：
- services/polymarket/signals/closing/detector.js
  - compareMarkets()

配置：
- services/polymarket/config/settings.js
  - arbitrage
  - orderbook

阈值与文档：
- services/polymarket/utils/userManager.js
  - checkArbitrageThreshold()
  - getThresholdSummary()
- services/polymarket/ALGORITHM_SPEC.md

## 执行步骤（详细）
1) 修改套利净利润公式，支持 fee/slippage 按成交额扣减  
2) 在套利缓存中写入 ask 深度与更新时间  
3) 在套利 detect 阶段增加深度门槛 + 过期判断  
4) 订单簿检测启用 `minPriceImpact` 配置  
5) 扫尾盘排序逻辑与注释对齐  
6) 同步用户阈值与文档（可选但强烈建议）

## 验证用例（最小可行）

### 套利
输入：
- YES=0.49, NO=0.49, fee=0.2%, slippage=0.5%
期望：
- net < 0，信号不触发

### 套利深度
输入：
- YES 深度=5, NO 深度=50, minDepth=20
期望：
- 不触发

### 订单簿
输入：
- priceImpact=0.8, minPriceImpact=1.0
期望：
- 不触发

### 扫尾盘排序
输入：
- A: score 高, timeRemaining 长
- B: score 低, timeRemaining 短
期望：
- 排序与选定规则一致
