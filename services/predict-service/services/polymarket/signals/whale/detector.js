/**
 * 大额交易检测器
 * 
 * 数据源: WebSocket last_trade
 * 职责: 检测大额交易，反映市场热度（不是跟单信号）
 * 
 * 注意: 大额买入 ≠ 聪明钱，可能是接盘侠
 */

class LargeTradeDetector {
    constructor(config = {}) {
        this.minValue = config.minValue ?? 10000;           // 最小交易额 $10K
        this.cooldown = config.cooldown ?? 60000;           // 冷却 1分钟
        this.maxSignalsPerHour = config.maxSignalsPerHour || 50;
        this.disableRateLimit = config.disableRateLimit === true;

        this.lastSignals = new Map();  // market -> timestamp
        this.stats = { detected: 0, sent: 0, skipped: 0, signalsThisHour: 0, lastHourReset: Date.now() };
    }

    /**
     * 处理 WebSocket last_trade 事件
     * @param {Object} trade - { assetId, price, side, size, timestamp }
     * @param {Object} marketMeta - 市场元数据
     */
    process(trade, marketMeta = {}) {
        if (!trade) return null;

        const size = parseFloat(trade.size) || 0;
        const price = parseFloat(trade.price) || 0;
        const value = size * price;

        if (value < this.minValue) return null;

        const market = marketMeta.conditionId || trade.assetId;
        if (!market) return null;

        const now = Date.now();

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
            type: 'large_trade',
            market,
            conditionId: marketMeta.conditionId || market,
            marketSlug: marketMeta.slug,
            eventSlug: marketMeta.eventSlug,
            marketName: marketMeta.question || marketMeta.title,
            side: trade.side,
            outcome: marketMeta.outcome || (trade.side === 'BUY' ? 'YES' : 'NO'),
            price,
            size,
            value,
            timestamp: trade.timestamp || now
        };
    }

    getStats() {
        return { ...this.stats, cacheSize: this.lastSignals.size };
    }

    cleanup() {
        const now = Date.now();
        for (const [k, v] of this.lastSignals) {
            if (now - v > this.cooldown * 10) this.lastSignals.delete(k);
        }
    }
}

module.exports = LargeTradeDetector;
