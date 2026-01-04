/**
 * 流动性枯竭检测器
 * 
 * 数据源: WebSocket book
 * 逻辑: 检测订单簿深度突然下降
 */

class LiquidityAlertDetector {
    constructor(config = {}) {
        this.dropThreshold = config.dropThreshold || 0.5;   // 深度下降 50%
        this.minDepth = config.minDepth || 1000;            // 最小关注深度 $1K
        this.windowMs = config.windowMs || 60000;           // 对比窗口 1分钟
        this.cooldown = config.cooldown ?? 300000;          // 冷却 5分钟
        this.maxSignalsPerHour = config.maxSignalsPerHour || 20;
        this.disableRateLimit = config.disableRateLimit === true;

        // market -> { history: [{depth, ts}], lastUpdate }
        this.depthHistory = new Map();
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

        // 计算当前深度 (前5档)
        const bidDepth = (book.bids || []).slice(0, 5).reduce((sum, l) => sum + (l.size * l.price), 0);
        const askDepth = (book.asks || []).slice(0, 5).reduce((sum, l) => sum + (l.size * l.price), 0);
        const totalDepth = bidDepth + askDepth;

        if (totalDepth < this.minDepth) return null;

        // 更新历史
        const entry = this.depthHistory.get(market) || { history: [] };
        entry.history.push({ depth: totalDepth, ts: now });
        entry.history = entry.history.filter(h => now - h.ts <= this.windowMs);
        entry.lastUpdate = now;
        entry.meta = { ...entry.meta, ...meta };
        this.depthHistory.set(market, entry);

        if (entry.history.length < 2) return null;

        // 计算变化
        const oldDepth = entry.history[0].depth;
        const dropRatio = (oldDepth - totalDepth) / oldDepth;

        if (dropRatio < this.dropThreshold) return null;

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

        return {
            type: 'liquidity_alert',
            market,
            conditionId: market,
            marketSlug: entry.meta?.slug,
            eventSlug: entry.meta?.eventSlug,
            marketName: entry.meta?.question || entry.meta?.title,
            oldDepth,
            newDepth: totalDepth,
            dropRatio,
            bidDepth,
            askDepth,
            timestamp: now
        };
    }

    getStats() {
        return { ...this.stats, trackedMarkets: this.depthHistory.size };
    }

    cleanup() {
        const now = Date.now();
        for (const [k, v] of this.depthHistory) {
            if (now - (v.lastUpdate || 0) > this.windowMs * 5) this.depthHistory.delete(k);
        }
        for (const [k, v] of this.lastSignals) {
            if (now - v > this.cooldown * 10) this.lastSignals.delete(k);
        }
    }
}

module.exports = LiquidityAlertDetector;
