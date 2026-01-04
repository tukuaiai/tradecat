# 性能优化：共享 Slug 缓存

> 日期：2024-12-23  
> 阶段：0 + 0.5 + 部分阶段2  
> 效果：P99 延迟从 2642ms 降至 11ms，缓存命中率从 70% 提升至 100%

---

## 1. 问题分析

### 1.1 现象
订单簿信号发送时，P99 延迟高达 2.6 秒，严重影响信号时效性。

### 1.2 根因追踪

通过埋点发现延迟集中在 `enrichMeta` 阶段（获取市场 slug/name）：

```
📊 [Metrics] sendSignal(orderbook) 耗时: 2642ms
enrichMeta: P99=2641ms  ← 瓶颈
format: P99=12ms
send: P99=0ms
```

**数据流分析：**

| WSS 消息类型 | 是否含 slug | 用途 |
|-------------|------------|------|
| `activity.trades` | ✅ 有 `eventSlug` / `slug` | 套利检测 |
| `clob_market.price_change` | ❌ 无 | 套利检测 |
| `clob_market.agg_orderbook` | ❌ 无 | 订单簿检测 |

订单簿检测器只收 `agg_orderbook`，该消息不含 slug，导致每次都要调用 CLOB HTTP API：

```javascript
// 之前的逻辑
const url = `https://clob.polymarket.com/markets/${conditionId}`;
// HTTP 请求延迟 = DNS + TCP + TLS + 响应 ≈ 800-2600ms
```

### 1.3 为什么缓存命中率只有 70%？

- 套利检测器从 `activity.trades` 缓存 slug
- 订单簿检测器尝试复用套利缓存
- 但套利缓存按 `tokenId` 索引，订单簿信号按 `market`（conditionId）查找
- 索引不匹配导致部分 miss

---

## 2. 解决方案

### 2.1 核心思路

建立**共享 slug 缓存**，按 `market`（conditionId）索引，所有模块共用（缓存 eventSlug/marketSlug 双字段，URL 优先 eventSlug）。

```
activity.trades 消息到达
    ↓
提取 slug 到共享缓存 (market → slug)
    ↓
收集 tokenId，触发订单簿订阅
    ↓
agg_orderbook 消息到达
    ↓
检测信号 → sendSignal
    ↓
从共享缓存获取 slug（0ms）✅
```

### 2.2 关键洞察

订单簿订阅是**动态的**：
1. 先订阅 `activity.trades`（全量）
2. 从 trades 消息收集活跃 tokenId
3. 再订阅这些 tokenId 的 `agg_orderbook`

**时序假设**：`activity.trades` 通常会先于对应的 `agg_orderbook` 到达，因此大部分情况下 slug 已被缓存；极端情况下仍会回退到 HTTP API。

---

## 3. 代码改动

### 3.1 新增文件

**`utils/metrics.js`** - 性能指标收集器
```javascript
class Metrics {
    startTimer(stage)      // 开始计时
    endTimer(timer)        // 结束计时并记录
    increment(name)        // 计数器
    percentile(arr, p)     // 计算百分位
    getHitRate(hit, total) // 计算命中率
    logReport()            // 输出报告
}
```

**`pipeline/stages.js`** - 阶段函数抽象（为后续 pipeline 重构准备）
```javascript
enrichSignalMeta()    // 元数据补全
formatSignal()        // 消息格式化
filterRecipients()    // 用户筛选
sendToUser()          // 单用户发送
```

### 3.2 修改文件

**`bot.js`**

1. 新增共享缓存：
```javascript
// 构造函数中
this.slugCache = new Map();  // market → { eventSlug, marketSlug, title, timestamp }
this.SLUG_CACHE_TTL = 30 * 60 * 1000;  // 30分钟
this.SLUG_CACHE_MAX = 10000;
```

2. 从 activity.trades 提取 slug：
```javascript
handlePriceChange(message) {
    const payload = message?.payload;
    if (payload) {
        const marketKeys = new Set([
            payload.conditionId,
            payload.condition_id,
            payload.market
        ].filter(Boolean));
        const marketSlug = payload.slug || payload.marketSlug || payload.market_slug || null;
        const eventSlug = payload.eventSlug || payload.event_slug || null;
        if (marketKeys.size > 0 && (eventSlug || marketSlug)) {
            this.cacheSlug(Array.from(marketKeys), {
                eventSlug: eventSlug || marketSlug,
                marketSlug,
                title: payload.title || payload.question
            });
        }
    }
    // ... 原有逻辑
}
```

3. sendSignal 优先从共享缓存获取：
```javascript
async sendSignal(moduleName, signal) {
    // 策略0: 共享 slug 缓存（最快）
    const sharedCache = this.getSlugFromCache(signal.market);
    if (sharedCache) {
        signal.eventSlug = sharedCache.eventSlug;
        signal.marketSlug = sharedCache.marketSlug;
        signal.marketName = sharedCache.title;
    }
    // 继续执行后续格式化与发送（不会提前 return）
    // 策略1: 套利检测器缓存（备用）
    // 策略2: HTTP API（最后手段）
}
```

4. 新增缓存方法：
```javascript
cacheSlug(markets, data) {
    const keys = Array.isArray(markets) ? markets : [markets];
    const entry = {
        eventSlug: data.eventSlug || data.marketSlug,
        marketSlug: data.marketSlug || null,
        title: data.title || null,
        timestamp: Date.now()
    };
    keys.forEach((market) => {
        if (!market) return;
        if (this.slugCache.has(market)) {
            this.slugCache.delete(market);
        }
        if (this.slugCache.size >= this.SLUG_CACHE_MAX) {
            const oldest = this.slugCache.keys().next().value;
            this.slugCache.delete(oldest);
        }
        this.slugCache.set(market, entry);
    });
}

getSlugFromCache(market) {
    const cached = this.slugCache.get(market);
    if (!cached) return null;
    if (Date.now() - cached.timestamp > this.SLUG_CACHE_TTL) {
        this.slugCache.delete(market);
        return null;
    }
    // 严格 LRU：命中后刷新顺序
    this.slugCache.delete(market);
    this.slugCache.set(market, cached);
    return cached;
}
```

---

## 4. 性能对比

### 4.1 优化前
```
运行25s 缓存70%
sendSignal: P50=1ms P99=2642ms
enrichMeta: P50=0ms P99=2641ms  ← 瓶颈
```

### 4.2 优化后
```
运行29s 缓存100%
sendSignal: P50=0ms P99=11ms
enrichMeta: P50=0ms P99=0ms  ← 消除
```

### 4.3 改进幅度

| 指标 | 优化前 | 优化后 | 改进 |
|------|--------|--------|------|
| P99 延迟 | 2642ms | 11ms | **240x** |
| P50 延迟 | 1ms | 0ms | - |
| 缓存命中率 | 70% | 100% | +30% |
| HTTP API 调用 | 30% 信号 | 0% | **消除** |

---

## 5. 边界情况

### 5.1 已覆盖
- ✅ 正常运行时的订单簿信号
- ✅ 套利信号（本身就有 slug）
- ✅ 缓存容量限制（10000 条，LRU 淘汰）
- ✅ 缓存过期（30 分钟 TTL）

### 5.2 降级场景
以下情况会 fallback 到 HTTP API（仍可用，只是慢）：

| 场景 | 原因 | 频率 |
|------|------|------|
| 套利模块关闭 | 不收 activity.trades | 罕见配置 |
| 极端冷启动 | 缓存为空 | 仅启动瞬间 |

---

## 6. 监控指标

每次信号发送后输出：
```
📊 [Metrics] sendSignal(orderbook) 耗时: 1ms
📊 [Metrics] 运行29s 缓存100.0% | sendSignal:P50=0ms/P99=11ms(n=8) | enrichMeta:P50=0ms/P99=0ms(n=7)
```

每 5 分钟汇总报告：
```
📊 [Metrics] 运行5m 缓存100% | sendSignal:P50=1ms/P99=15ms(n=120) | ...
```

---

## 7. 后续优化方向

根据 `ARCH_OPTIMIZATION_EXECUTION_PLAN.md`，剩余阶段：

- [ ] 阶段1：SignalPipeline 流水线重构
- [ ] 阶段3：先发简版，后补全更新
- [ ] 阶段4：翻译去重
- [ ] 阶段5：closing 补全分片
- [ ] 阶段6：统一并发调度器

当前优化已解决最大瓶颈（元数据获取），后续阶段为增量优化。
