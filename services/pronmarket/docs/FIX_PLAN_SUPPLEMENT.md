# Polymarket 信号检测修复落地文档（补充版）

文档时间：2025-12-23
状态：待执行

---

## 一、问题确认清单

### 🔴 P0 - 必须修复（影响信号准确性）

| # | 问题 | 当前代码 | 正确逻辑 | 文件位置 |
|---|------|---------|---------|---------|
| 1 | 套利手续费计算错误 | `netProfit = grossProfit - 0.002` | `netProfit = grossProfit - sum * fee * 2` | arbitrage/detector.js:289-290 |
| 2 | 套利滑点配置未使用 | 配置有 `slippage: 0.005`，代码未读取 | 计算时扣除滑点 | arbitrage/detector.js + bot.js |

### 🟡 P1 - 应该修复（防止假阳性/配置失效）

| # | 问题 | 当前代码 | 正确逻辑 | 文件位置 |
|---|------|---------|---------|---------|
| 3 | 套利缺深度检查 | 只检查价格 | 检查 YES/NO 双边深度 ≥ 阈值 | arbitrage/detector.js |
| 4 | minPriceImpact 未传递 | bot.js 漏传，detector 硬编码 `1` | 从配置读取 | bot.js:136 + orderbook/detector.js:304 |

### 🟢 P2 - 建议修复（提升质量）

| # | 问题 | 当前代码 | 正确逻辑 | 文件位置 |
|---|------|---------|---------|---------|
| 5 | 套利价格缓存无过期检查 | 只存 timestamp 不检查 | 检查 YES/NO 时间差 ≤ 阈值 | arbitrage/detector.js:269-275 |
| 6 | 扫尾盘排序注释错误 | 注释说"得分优先"，代码"时间优先" | 二选一对齐 | closing/detector.js:100-107 |

### ⚪ P3 - 可选修复

| # | 问题 | 说明 |
|---|------|------|
| 7 | 订单簿 Cooldown 0.5s | 可能噪声多，建议改 2-3s |
| 8 | 扫尾盘无最低流动性 | 默认 0，可能推送枯竭市场 |
| 9 | 用户阈值与文档不一致 | 算法 0.3%，档位1 要 2% |

---

## 二、修复方案详细设计

### 修复 #1：套利手续费计算

**当前代码：**
```javascript
// arbitrage/detector.js:289-290
const grossProfit = 1.0 - sum;
const netProfit = grossProfit - this.TRADING_FEE;
```

**修复后：**
```javascript
// arbitrage/detector.js:289-291
const grossProfit = 1.0 - sum;
const totalFee = sum * this.TRADING_FEE * 2;  // 双边手续费
const netProfit = grossProfit - totalFee;
```

**验证用例：**
```
输入: YES=0.49, NO=0.49, fee=0.2%
sum = 0.98
grossProfit = 0.02 (2%)
totalFee = 0.98 * 0.002 * 2 = 0.00392 (0.4%)
netProfit = 0.02 - 0.00392 = 0.01608 (1.6%)

当前错误结果: 0.02 - 0.002 = 0.018 (1.8%) ❌
修复后正确结果: 0.01608 (1.6%) ✅
```

---

### 修复 #2：套利滑点计算

**当前代码：**
```javascript
// bot.js:125-131 - 未传递 slippage
this.modules.arbitrage = new ArbitrageDetector({
    minProfit: config.arbitrage.minProfit,
    tradingFee: config.arbitrage.tradingFee,
    // slippage 未传递
});

// arbitrage/detector.js - 未定义 SLIPPAGE
```

**修复后：**

Step 1 - bot.js 传递配置：
```javascript
this.modules.arbitrage = new ArbitrageDetector({
    minProfit: config.arbitrage.minProfit,
    tradingFee: config.arbitrage.tradingFee,
    slippage: config.arbitrage.slippage,  // 新增
    cooldown: config.arbitrage.cooldown,
    maxSignalsPerHour: config.arbitrage.maxSignalsPerHour,
    debug: Boolean(config.debug?.enabled || config.debug?.logAllMessages)
});
```

Step 2 - detector.js 读取并使用：
```javascript
// constructor
this.SLIPPAGE = config.slippage || 0.005;  // 默认 0.5%

// detect() 函数
const grossProfit = 1.0 - sum;
const totalFee = sum * this.TRADING_FEE * 2;
const totalSlippage = sum * this.SLIPPAGE * 2;  // 双边滑点
const netProfit = grossProfit - totalFee - totalSlippage;
```

**验证用例：**
```
输入: YES=0.49, NO=0.49, fee=0.2%, slippage=0.5%
sum = 0.98
grossProfit = 0.02 (2%)
totalFee = 0.98 * 0.002 * 2 = 0.00392
totalSlippage = 0.98 * 0.005 * 2 = 0.0098
netProfit = 0.02 - 0.00392 - 0.0098 = 0.00628 (0.64%)

如果 MIN_PROFIT=0.3%, 信号触发 ✅
如果 MIN_PROFIT=1.0%, 信号不触发 ✅
```

---

### 修复 #3：套利深度检查

**设计方案：**

需要从 `agg_orderbook` 消息中提取深度信息，存入 priceCache。

Step 1 - 扩展缓存结构：
```javascript
// updateCache() 或新增 updateDepthCache()
const cacheEntry = {
    price: price,
    askDepthUsd: askDepthUsd,  // 新增：前N档ask深度
    timestamp: Date.now(),
    // ...其他字段
};
```

Step 2 - 在 processOrderbook() 中计算深度：
```javascript
processOrderbook(message) {
    const payload = message.payload;
    const asks = payload.asks || [];
    
    // 计算前3档深度
    let askDepthUsd = 0;
    for (let i = 0; i < Math.min(3, asks.length); i++) {
        askDepthUsd += asks[i].size || 0;
    }
    
    // 更新缓存时带上深度
    this.updateCache(tokenId, bestAsk, market, payload, askDepthUsd);
}
```

Step 3 - 在 detect() 中检查深度：
```javascript
// 新增配置
this.MIN_DEPTH = config.minDepth || 100;  // 最小 $100

// detect() 中检查
const yesDepth = yesData.askDepthUsd || 0;
const noDepth = noData.askDepthUsd || 0;
const minDepth = Math.min(yesDepth, noDepth);

if (minDepth < this.MIN_DEPTH) {
    return null;  // 深度不足，跳过
}
```

**验证用例：**
```
输入: YES深度=$50, NO深度=$200, minDepth=$100
minDepth = min(50, 200) = 50 < 100
结果: 不触发 ✅

输入: YES深度=$150, NO深度=$200, minDepth=$100
minDepth = min(150, 200) = 150 >= 100
结果: 继续检查其他条件 ✅
```

---

### 修复 #4：minPriceImpact 配置生效

**当前代码：**
```javascript
// bot.js - 未传递
this.modules.orderbook = new OrderbookDetector({
    minImbalance: config.orderbook.minImbalance,
    // minPriceImpact 未传递
});

// orderbook/detector.js:304 - 硬编码
if (priceImpact < 1) {
    return null;
}
```

**修复后：**

Step 1 - bot.js 传递：
```javascript
this.modules.orderbook = new OrderbookDetector({
    minImbalance: config.orderbook.minImbalance,
    minDepth: config.orderbook.minDepth,
    depthLevels: config.orderbook.depthLevels,
    cooldown: config.orderbook.cooldown,
    maxSignalsPerHour: config.orderbook.maxSignalsPerHour,
    historySize: config.orderbook.historySize,
    minPriceImpact: config.orderbook.minPriceImpact  // 新增
});
```

Step 2 - detector.js 读取：
```javascript
// constructor
this.MIN_PRICE_IMPACT = config.minPriceImpact || 1.0;

// detect() 中使用
if (priceImpact < this.MIN_PRICE_IMPACT) {
    return null;
}
```

---

### 修复 #5：套利价格缓存过期检查

**设计方案：**

```javascript
// detect() 函数中，获取价格后检查时间差
const yesData = this.priceCache.get(tokens.yes);
const noData = this.priceCache.get(tokens.no);

if (!yesData || !noData) return null;

// 新增：检查价格数据是否过期
const MAX_PRICE_AGE_MS = 60000;  // 1分钟
const now = Date.now();
const yesAge = now - yesData.timestamp;
const noAge = now - noData.timestamp;

if (yesAge > MAX_PRICE_AGE_MS || noAge > MAX_PRICE_AGE_MS) {
    return null;  // 价格数据过期
}

// 新增：检查 YES/NO 时间差是否过大
const timeDiff = Math.abs(yesData.timestamp - noData.timestamp);
if (timeDiff > 30000) {  // 30秒
    return null;  // 价格不同步
}
```

---

### 修复 #6：扫尾盘排序逻辑

**当前代码：**
```javascript
// 注释说"按照得分优先"
function compareMarkets(a, b) {
    if (a.timeRemainingMs !== b.timeRemainingMs) {
        return a.timeRemainingMs - b.timeRemainingMs;  // 实际先按时间
    }
    // ...
}
```

**方案A - 改代码（得分优先）：**
```javascript
function compareMarkets(a, b) {
    if (b.score !== a.score) {
        return b.score - a.score;  // 先按得分
    }
    if (a.timeRemainingMs !== b.timeRemainingMs) {
        return a.timeRemainingMs - b.timeRemainingMs;
    }
    return b.volume - a.volume;
}
```

**方案B - 改注释（时间优先）：**
```javascript
/**
 * 排序比较函数：按照剩余时间优先，其次按得分、成交量排序。
 */
```

**建议**：采用方案A，得分优先更符合业务逻辑。

---

## 三、执行顺序

```
Phase 1 - P0 修复（影响准确性）
├── #1 套利手续费计算
└── #2 套利滑点计算

Phase 2 - P1 修复（防止假阳性）
├── #3 套利深度检查
└── #4 minPriceImpact 配置

Phase 3 - P2 修复（提升质量）
├── #5 价格缓存过期
└── #6 排序逻辑对齐

Phase 4 - 验证
├── 单元测试
├── 集成测试
└── 生产验证
```

---

## 四、影响评估

### 信号数量变化预估

| 修复项 | 预计影响 |
|-------|---------|
| #1 手续费 | 信号减少 ~10-20%（边缘信号被过滤） |
| #2 滑点 | 信号减少 ~20-30%（更多边缘信号被过滤） |
| #3 深度检查 | 信号减少 ~30-50%（薄盘口被过滤） |
| #4 minPriceImpact | 无变化（当前硬编码值=配置值） |
| #5 过期检查 | 信号减少 ~5-10%（过期数据被过滤） |
| #6 排序 | 无数量变化，顺序变化 |

### 返工风险点

1. **#3 深度检查需要修改数据流**
   - `processOrderbook()` 需要计算并传递深度
   - `updateCache()` 需要接收深度参数
   - 建议：先在 `processOrderbook` 中单独维护深度缓存

2. **#1+#2 组合后阈值可能需要调整**
   - 当前 `MIN_PROFIT=0.3%` 可能过低
   - 修复后实际可触发的机会更少
   - 建议：观察一周后再决定是否调整

---

## 五、回滚方案

每个修复独立提交，便于单独回滚：

```bash
git revert <commit-hash>  # 回滚单个修复
```

建议 commit 格式：
```
fix(arbitrage): correct fee calculation with bilateral deduction
fix(arbitrage): add slippage to profit calculation
fix(arbitrage): add depth check before signal emission
fix(orderbook): use minPriceImpact from config
fix(arbitrage): add price cache expiration check
fix(closing): align sort logic with score-first strategy
```

---

## 六、配置参数汇总

修复后需要关注的配置项：

```javascript
// config/settings.js
arbitrage: {
    minProfit: 0.003,      // 最低净利润 0.3%
    tradingFee: 0.002,     // 手续费 0.2%（双边扣）
    slippage: 0.005,       // 滑点 0.5%（双边扣）
    minDepth: 100,         // 新增：最小深度 $100
    maxPriceAge: 60000,    // 新增：价格最大有效期 60秒
    maxPriceTimeDiff: 30000 // 新增：YES/NO最大时间差 30秒
},
orderbook: {
    minPriceImpact: 1.0,   // 已有，需传递
}
```

---

*文档结束*
