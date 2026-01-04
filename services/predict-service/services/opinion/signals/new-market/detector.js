/**
 * 新市场检测器 (Opinion 版本)
 * 
 * 数据源: Opinion Open API
 * 职责: 第一时间发现新上线的市场
 */

class NewMarketDetector {
    constructor(config = {}) {
        this.cooldown = config.cooldown || 0;
        this.maxSignalsPerHour = config.maxSignalsPerHour || 100;
        this.scanIntervalMs = config.scanIntervalMs || 60000;
        this.maxAge = config.maxAge || 3600000;             // 只推送1小时内的新市场
        this.minLiquidity = config.minLiquidity || 0;
        this.ttl = config.ttl || 86400000;                  // 24小时去重
        this.maxSeenMarkets = config.maxSeenMarkets || 10000;
        this.disableRateLimit = config.disableRateLimit === true;

        this.seenMarkets = new Map(); // marketId -> timestamp
        this.lastScanTime = 0;
        this.baselineLoaded = false;
        this.stats = { detected: 0, sent: 0, skipped: 0, signalsThisHour: 0, lastHourReset: Date.now() };

        // Opinion 客户端 (外部注入)
        this.client = config.client || null;
    }

    /**
     * 设置 Opinion 客户端
     */
    setClient(client) {
        this.client = client;
    }

    /**
     * 检查是否为新市场（供外部调用）
     */
    checkNewMarket(market) {
        if (!market || !market.marketId) return false;
        
        const now = Date.now();
        const existingTs = this.seenMarkets.get(market.marketId);
        
        if (existingTs) return false;
        
        // 记录并返回 true
        this.seenMarkets.set(market.marketId, now);
        this.trimSeenMarkets();
        this.stats.detected++;
        
        return true;
    }

    /**
     * 处理市场数据
     */
    process(market) {
        if (!market || !market.marketId) return null;

        const now = Date.now();

        // 去重检查
        const existingTs = this.seenMarkets.get(market.marketId);
        if (existingTs && now - existingTs < this.ttl) {
            return null;
        }

        // 流动性过滤
        if (this.minLiquidity > 0 && (market.liquidity || 0) < this.minLiquidity) {
            return null;
        }

        // 小时限制
        if (!this.disableRateLimit) {
            if (now - this.stats.lastHourReset > 3600000) {
                this.stats.signalsThisHour = 0;
                this.stats.lastHourReset = now;
            }
            if (this.stats.signalsThisHour >= this.maxSignalsPerHour) {
                this.stats.skipped++;
                return null;
            }
        }

        // 记录已见
        this.seenMarkets.set(market.marketId, now);
        this.trimSeenMarkets();

        this.stats.detected++;
        if (!this.disableRateLimit) this.stats.signalsThisHour++;

        return {
            type: 'new_market',
            market: market.marketId,
            marketId: market.marketId,
            marketTitle: market.marketTitle,
            marketSlug: market.slug,
            description: market.description,
            yesTokenId: market.yesTokenId,
            noTokenId: market.noTokenId,
            volume: market.volume,
            volume24h: market.volume24h,
            status: market.status,
            statusEnum: market.statusEnum,
            timestamp: now
        };
    }

    /**
     * 使用 Opinion API 扫描新市场
     */
    async scan() {
        if (!this.client) return [];

        const now = Date.now();
        if (now - this.lastScanTime < this.scanIntervalMs) {
            return [];
        }
        this.lastScanTime = now;

        const signals = [];
        const isBaseline = !this.baselineLoaded;

        try {
            const markets = await this.client.getMarkets({ useCache: false });

            for (const market of markets) {
                if (isBaseline) {
                    this.seenMarkets.set(market.marketId, now);
                } else {
                    const signal = this.process(market);
                    if (signal) {
                        signals.push(signal);
                    }
                }
            }

            if (isBaseline) {
                this.baselineLoaded = true;
                console.log(`✅ 新市场基线加载完成: ${this.seenMarkets.size} 个市场`);
            }
        } catch (error) {
            console.error('❌ 新市场扫描失败:', error.message);
        }

        return signals;
    }

    /**
     * 获取热门新市场
     */
    async getTrendingNew(limit = 10) {
        if (!this.client) return [];

        const signals = [];
        try {
            const markets = await this.client.getMarkets({ sortBy: 5, limit });

            for (const market of markets) {
                // 如果 volume24h 占比高，说明是新市场
                if (market.volume > 0 && market.volume24h > 0) {
                    if (market.volume24h / market.volume > 0.8) {
                        const signal = this.process(market);
                        if (signal) {
                            signal.subtype = 'trending_new';
                            signals.push(signal);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('❌ 热门新市场获取失败:', error.message);
        }

        return signals;
    }

    getStats() {
        return { ...this.stats, seenMarkets: this.seenMarkets.size };
    }

    cleanup() {
        const now = Date.now();
        let removed = 0;

        for (const [k, v] of this.seenMarkets) {
            if (now - v > this.ttl) {
                this.seenMarkets.delete(k);
                removed++;
            }
        }

        this.trimSeenMarkets();

        if (removed > 0) {
            console.log(`🧹 新市场缓存清理: ${removed} 条 (剩余 ${this.seenMarkets.size})`);
        }
    }

    trimSeenMarkets() {
        while (this.seenMarkets.size > this.maxSeenMarkets) {
            const oldestKey = this.seenMarkets.keys().next().value;
            this.seenMarkets.delete(oldestKey);
        }
    }
}

module.exports = NewMarketDetector;
