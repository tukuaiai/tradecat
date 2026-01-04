/**
 * 订单簿倾斜检测器
 * 
 * 数据源: WebSocket book
 * 逻辑: 检测 bid/ask 比例突然变化
 */

class BookSkewDetector {
    constructor(config = {}) {
        this.minSkewChange = config.minSkewChange || 0.5;   // 倾斜变化 50%
        this.minDepth = config.minDepth || 500;             // 最小深度 $500
        this.windowMs = config.windowMs || 30000;           // 对比窗口 30秒
        this.cooldown = config.cooldown ?? 120000;          // 冷却 2分钟
        this.maxSignalsPerHour = config.maxSignalsPerHour || 30;
        this.disableRateLimit = config.disableRateLimit === true;

        // market -> { history: [{skew, ts}], lastUpdate }
        this.skewHistory = new Map();
        this.lastSignals = new Map();
        this.stats = { detected: 0, sent: 0, skipped: 0, signalsThisHour: 0, lastHourReset: Date.now() };
    }

    /**
     * 处理 WebSocket book 更新
     */
    process(book, meta = {}) {
        if (!book || !book.assetId) return null;

        const market = meta.conditionId || book.assetId;
        const now = Date.now();

        // 计算深度
        const bidDepth = (book.bids || []).slice(0, 5).reduce((sum, l) => sum + (l.size * l.price), 0);
        const askDepth = (book.asks || []).slice(0, 5).reduce((sum, l) => sum + (l.size * l.price), 0);
        const totalDepth = bidDepth + askDepth;

        if (totalDepth < this.minDepth) return null;

        // 计算倾斜度 (bid / ask)
        const skew = askDepth > 0 ? bidDepth / askDepth : 0;

        // 更新历史
        const entry = this.skewHistory.get(market) || { history: [] };
        entry.history.push({ skew, bidDepth, askDepth, ts: now });
        entry.history = entry.history.filter(h => now - h.ts <= this.windowMs);
        entry.lastUpdate = now;
        entry.meta = { ...entry.meta, ...meta };
        this.skewHistory.set(market, entry);

        if (entry.history.length < 2) return null;

        // 计算变化
        const oldSkew = entry.history[0].skew;
        if (oldSkew === 0) return null;

        const skewChange = Math.abs(skew - oldSkew) / oldSkew;

        if (skewChange < this.minSkewChange) return null;

        // 冷却检查
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

        const direction = skew > oldSkew ? 'bullish' : 'bearish';

        return {
            type: 'book_skew',
            market,
            conditionId: market,
            marketSlug: entry.meta?.slug,
            eventSlug: entry.meta?.eventSlug,
            marketName: entry.meta?.question || entry.meta?.title,
            oldSkew,
            newSkew: skew,
            skewChange,
            direction,
            bidDepth,
            askDepth,
            timestamp: now
        };
    }

    getStats() {
        return { ...this.stats, trackedMarkets: this.skewHistory.size };
    }

    cleanup() {
        const now = Date.now();
        for (const [k, v] of this.skewHistory) {
            if (now - (v.lastUpdate || 0) > this.windowMs * 5) this.skewHistory.delete(k);
        }
        for (const [k, v] of this.lastSignals) {
            if (now - v > this.cooldown * 10) this.lastSignals.delete(k);
        }
    }
}

module.exports = BookSkewDetector;
