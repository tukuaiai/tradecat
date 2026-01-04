/**
 * 深度套利检测器
 * 
 * 数据源: WebSocket book (双边订单簿)
 * 逻辑: 使用 effectivePrices 计算精准套利机会
 * 
 * 比普通套利更准确：考虑订单簿镜像特性
 */

class DeepArbDetector {
    constructor(config = {}) {
        this.minProfit = config.minProfit || 0.005;         // 最小利润 0.5%
        this.minDepth = config.minDepth || 100;             // 最小深度 $100
        this.cooldown = config.cooldown ?? 60000;           // 冷却 1分钟
        this.maxSignalsPerHour = config.maxSignalsPerHour || 30;
        this.disableRateLimit = config.disableRateLimit === true;

        // 缓存: market -> { yesBook, noBook, lastUpdate }
        this.bookCache = new Map();
        this.lastSignals = new Map();
        this.stats = { detected: 0, sent: 0, skipped: 0, signalsThisHour: 0, lastHourReset: Date.now() };
    }

    /**
     * 处理 WebSocket book 更新
     * @param {Object} book - { assetId, bids, asks, timestamp }
     * @param {Object} meta - { conditionId, isYes, yesTokenId, noTokenId, ... }
     */
    process(book, meta = {}) {
        if (!book || !book.assetId) return null;

        const market = meta.conditionId;
        if (!market) return null;

        // 更新缓存
        const cached = this.bookCache.get(market) || {};
        if (meta.isYes) {
            cached.yesBook = book;
            cached.yesTokenId = book.assetId;
        } else {
            cached.noBook = book;
            cached.noTokenId = book.assetId;
        }
        cached.lastUpdate = Date.now();
        cached.meta = { ...cached.meta, ...meta };
        this.bookCache.set(market, cached);

        // 需要双边数据
        if (!cached.yesBook || !cached.noBook) return null;

        // 计算有效价格
        const yesAsk = cached.yesBook.asks?.[0]?.price || 1;
        const yesBid = cached.yesBook.bids?.[0]?.price || 0;
        const noAsk = cached.noBook.asks?.[0]?.price || 1;
        const noBid = cached.noBook.bids?.[0]?.price || 0;

        // 有效买入价 (考虑镜像)
        const effectiveBuyYes = Math.min(yesAsk, 1 - noBid);
        const effectiveBuyNo = Math.min(noAsk, 1 - yesBid);

        // 有效卖出价
        const effectiveSellYes = Math.max(yesBid, 1 - noAsk);
        const effectiveSellNo = Math.max(noBid, 1 - yesAsk);

        // 套利计算
        const longCost = effectiveBuyYes + effectiveBuyNo;
        const shortRevenue = effectiveSellYes + effectiveSellNo;

        const longProfit = 1 - longCost;
        const shortProfit = shortRevenue - 1;

        // 检查深度
        const yesAskSize = cached.yesBook.asks?.[0]?.size || 0;
        const noAskSize = cached.noBook.asks?.[0]?.size || 0;
        const minAskDepth = Math.min(yesAskSize * effectiveBuyYes, noAskSize * effectiveBuyNo);

        const yesBidSize = cached.yesBook.bids?.[0]?.size || 0;
        const noBidSize = cached.noBook.bids?.[0]?.size || 0;
        const minBidDepth = Math.min(yesBidSize * effectiveSellYes, noBidSize * effectiveSellNo);

        let signal = null;

        // Long Arb: 买入成本 < 1
        if (longProfit >= this.minProfit && minAskDepth >= this.minDepth) {
            signal = {
                type: 'deep_arb',
                subtype: 'long',
                market,
                profit: longProfit,
                cost: longCost,
                depth: minAskDepth,
                effectiveBuyYes,
                effectiveBuyNo,
                yesAsk,
                noAsk
            };
        }

        // Short Arb: 卖出收入 > 1
        if (shortProfit >= this.minProfit && shortProfit > longProfit && minBidDepth >= this.minDepth) {
            signal = {
                type: 'deep_arb',
                subtype: 'short',
                market,
                profit: shortProfit,
                revenue: shortRevenue,
                depth: minBidDepth,
                effectiveSellYes,
                effectiveSellNo,
                yesBid,
                noBid
            };
        }

        if (!signal) return null;

        // 冷却检查
        const now = Date.now();
        if (!this.disableRateLimit) {
            const lastTime = this.lastSignals.get(market) || 0;
            if (now - lastTime < this.cooldown) {
                this.stats.skipped++;
                return null;
            }

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

        return {
            ...signal,
            conditionId: market,
            marketSlug: cached.meta?.slug,
            eventSlug: cached.meta?.eventSlug,
            marketName: cached.meta?.question || cached.meta?.title,
            timestamp: now
        };
    }

    getStats() {
        return { ...this.stats, cachedMarkets: this.bookCache.size };
    }

    cleanup() {
        const now = Date.now();
        // 清理 5 分钟无更新的缓存
        for (const [k, v] of this.bookCache) {
            if (now - (v.lastUpdate || 0) > 300000) this.bookCache.delete(k);
        }
        for (const [k, v] of this.lastSignals) {
            if (now - v > this.cooldown * 10) this.lastSignals.delete(k);
        }
    }
}

module.exports = DeepArbDetector;
