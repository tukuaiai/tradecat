/**
 * 价格突变检测器 (SDK 版本)
 * 
 * 数据源: poly-sdk WebSocket price_update + Gamma API
 * 职责: 检测短时间内价格剧烈波动
 */

class PriceSpikeDetector {
    constructor(config = {}) {
        this.minChange = config.minChange || 0.05;          // 最小变化 5%
        this.windowMs = config.windowMs || 60000;           // 时间窗口 60秒
        this.cooldown = config.cooldown ?? 300000;          // 冷却 5分钟
        this.maxSignalsPerHour = config.maxSignalsPerHour || 50;
        this.historyTtl = config.historyTtl || 600000;      // 历史保留 10分钟
        this.maxMarkets = config.maxMarkets || 50000;       // 市场上限
        this.minVolume24hr = config.minVolume24hr || 1000;  // 最小24h成交量过滤
        this.disableRateLimit = config.disableRateLimit === true;

        // market -> { prices: [{price, ts}], lastAccess }
        this.priceHistory = new Map();
        this.lastSignals = new Map();
        this.stats = { detected: 0, sent: 0, skipped: 0, signalsThisHour: 0, lastHourReset: Date.now() };

        // SDK 实例 (外部注入)
        this.sdk = config.sdk || null;
    }

    /**
     * 设置 SDK 实例
     */
    setSDK(sdk) {
        this.sdk = sdk;
    }

    /**
     * 处理 WebSocket price_update 事件
     * @param {Object} update - { assetId, price, midpoint, spread, timestamp }
     * @param {Object} marketMeta - 市场元数据 (可选)
     */
    process(update, marketMeta = {}) {
        if (!update || !update.assetId) return null;

        const market = marketMeta.conditionId || update.assetId;
        const price = update.midpoint || update.price;
        if (!Number.isFinite(price) || price <= 0) return null;

        const now = Date.now();
        const entry = this.ensureEntry(market);
        entry.lastAccess = now;

        // 添加价格点
        entry.prices.push({ price, ts: now });

        // 移除窗口外的价格
        entry.prices = entry.prices.filter(p => now - p.ts <= this.windowMs);

        if (entry.prices.length < 2) return null;

        // 计算变化
        const oldPrice = entry.prices[0].price;
        const change = Math.abs(price - oldPrice) / oldPrice;

        if (change < this.minChange) return null;

        // 24h 成交量过滤
        if (marketMeta.volume24hr && marketMeta.volume24hr < this.minVolume24hr) {
            return null;
        }

        // 冷却检查
        if (!this.disableRateLimit) {
            const lastTime = this.lastSignals.get(market) || 0;
            if (now - lastTime < this.cooldown) {
                this.stats.skipped++;
                return null;
            }

            // 小时限制
            if (now - this.stats.lastHourReset > 3600000) {
                this.stats.signalsThisHour = 0;
                this.stats.lastHourReset = now;
            }
            if (this.stats.signalsThisHour >= this.maxSignalsPerHour) {
                this.stats.skipped++;
                return null;
            }
        }

        this.lastSignals.set(market, now);
        this.stats.detected++;
        if (!this.disableRateLimit) this.stats.signalsThisHour++;

        const direction = price > oldPrice ? 'up' : 'down';

        return {
            type: 'price_spike',
            market,
            conditionId: marketMeta.conditionId || market,
            marketSlug: marketMeta.slug || null,
            eventSlug: marketMeta.eventSlug || null,
            marketName: marketMeta.question || marketMeta.title || null,
            oldPrice,
            newPrice: price,
            change,
            direction,
            windowMs: this.windowMs,
            // SDK 额外数据
            spread: update.spread,
            volume24hr: marketMeta.volume24hr,
            liquidity: marketMeta.liquidity,
            oneDayPriceChange: marketMeta.oneDayPriceChange,
            timestamp: now
        };
    }

    /**
     * 使用 SDK 主动扫描热门市场价格变化
     */
    async scanTrending(limit = 50) {
        if (!this.sdk) return [];

        const signals = [];
        try {
            const trending = await this.sdk.gammaApi.getTrendingMarkets(limit);

            for (const market of trending) {
                if (!market.conditionId) continue;

                // 获取当前价格
                const yesPrice = market.outcomePrices?.[0] || 0;

                const signal = this.process(
                    { assetId: market.conditionId, price: yesPrice, midpoint: yesPrice, timestamp: Date.now() },
                    {
                        conditionId: market.conditionId,
                        slug: market.slug,
                        question: market.question,
                        volume24hr: market.volume24hr,
                        liquidity: market.liquidity,
                        oneDayPriceChange: market.oneDayPriceChange
                    }
                );

                if (signal) signals.push(signal);
            }
        } catch (error) {
            console.error('❌ 价格突变扫描失败:', error.message);
        }

        return signals;
    }

    getStats() {
        return { ...this.stats, marketsTracked: this.priceHistory.size };
    }

    cleanup() {
        const now = Date.now();
        let removed = 0;

        for (const [k, v] of this.priceHistory) {
            if (!v || v.prices.length === 0 || now - v.lastAccess > this.historyTtl) {
                this.priceHistory.delete(k);
                removed++;
            }
        }

        // 容量限制
        while (this.priceHistory.size > this.maxMarkets) {
            const oldestKey = this.priceHistory.keys().next().value;
            this.priceHistory.delete(oldestKey);
            removed++;
        }

        // 清理冷却缓存
        for (const [k, v] of this.lastSignals) {
            if (now - v > this.cooldown * 10) this.lastSignals.delete(k);
        }

        if (removed > 0) {
            console.log(`🧹 价格突变缓存清理: ${removed} 个 (剩余 ${this.priceHistory.size})`);
        }
    }

    ensureEntry(market) {
        if (!this.priceHistory.has(market)) {
            this.priceHistory.set(market, { prices: [], lastAccess: Date.now() });
        }
        const entry = this.priceHistory.get(market);
        // LRU: 重新插入
        this.priceHistory.delete(market);
        this.priceHistory.set(market, entry);
        return entry;
    }
}

module.exports = PriceSpikeDetector;
