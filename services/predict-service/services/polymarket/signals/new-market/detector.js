/**
 * 新市场检测器 (SDK 版本)
 * 
 * 数据源: poly-sdk Gamma API (markets, events)
 * 职责: 第一时间发现新上线的市场
 */

class NewMarketDetector {
    constructor(config = {}) {
        this.cooldown = config.cooldown || 0;               // 新市场无需冷却
        this.maxSignalsPerHour = config.maxSignalsPerHour || 100;
        this.scanIntervalMs = config.scanIntervalMs || 60000; // 扫描间隔 1分钟
        this.maxAge = config.maxAge || 3600000;             // 只推送1小时内的新市场
        this.minLiquidity = config.minLiquidity || 0;       // 最小流动性过滤
        this.ttl = config.ttl || 86400000;                  // 24小时去重
        this.maxSeenMarkets = config.maxSeenMarkets || 10000;
        this.disableRateLimit = config.disableRateLimit === true;

        this.seenMarkets = new Map(); // conditionId -> timestamp
        this.lastScanTime = 0;
        this.baselineLoaded = false;  // 基线标记：第一次扫描只记录不推送
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
     * 处理 WebSocket 或 REST 市场数据
     * @param {Object} market - 市场数据
     */
    process(market) {
        if (!market || !market.conditionId) return null;

        const now = Date.now();

        // 去重检查
        const existingTs = this.seenMarkets.get(market.conditionId);
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
        this.seenMarkets.set(market.conditionId, now);
        this.trimSeenMarkets();

        this.stats.detected++;
        if (!this.disableRateLimit) this.stats.signalsThisHour++;

        return {
            type: 'new_market',
            market: market.conditionId,
            conditionId: market.conditionId,
            marketSlug: market.slug,
            eventSlug: market.eventSlug,
            marketName: market.question || market.title,
            description: market.description,
            // SDK 完整数据
            outcomes: market.outcomes,
            outcomePrices: market.outcomePrices,
            volume: market.volume,
            volume24hr: market.volume24hr,
            liquidity: market.liquidity,
            endDate: market.endDate,
            tags: market.tags,
            image: market.image,
            icon: market.icon,
            active: market.active,
            closed: market.closed,
            tokens: market.tokens,
            timestamp: now
        };
    }

    /**
     * 使用 SDK 扫描新市场
     */
    async scan() {
        if (!this.sdk) return [];

        const now = Date.now();
        if (now - this.lastScanTime < this.scanIntervalMs) {
            return [];
        }
        this.lastScanTime = now;

        const signals = [];
        const isBaseline = !this.baselineLoaded;  // 第一次扫描为基线加载

        try {
            // 获取最新市场列表
            const markets = await this.sdk.gammaApi.getMarkets({
                active: true,
                closed: false,
                order: 'createdAt',
                ascending: false,
                limit: 50
            });

            for (const market of markets) {
                // 检查是否是新市场 (1小时内创建)
                const createdAt = market.createdAt ? new Date(market.createdAt).getTime() : 0;
                if (createdAt && now - createdAt > this.maxAge) continue;

                if (isBaseline) {
                    // 基线加载：只记录不推送
                    this.seenMarkets.set(market.conditionId, now);
                } else {
                    const signal = this.process(market);
                    if (signal) {
                        signal.createdAt = createdAt;
                        signals.push(signal);
                    }
                }
            }

            // 也扫描新事件
            const events = await this.sdk.gammaApi.getEvents({ limit: 20 });
            for (const event of events) {
                if (!event.markets) continue;

                for (const market of event.markets) {
                    if (isBaseline) {
                        this.seenMarkets.set(market.conditionId, now);
                    } else {
                        const signal = this.process({
                            ...market,
                            eventSlug: event.slug,
                            eventTitle: event.title
                        });
                        if (signal) {
                            signal.eventTitle = event.title;
                            signals.push(signal);
                        }
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
     * 使用 SDK 获取热门新市场
     */
    async getTrendingNew(limit = 10) {
        if (!this.sdk) return [];

        const signals = [];
        try {
            const trending = await this.sdk.gammaApi.getTrendingMarkets(100);

            // 过滤出新市场 (24h内有首次交易)
            const newMarkets = trending.filter(m => {
                // 如果 volume24hr 接近 volume，说明是新市场
                if (m.volume > 0 && m.volume24hr > 0) {
                    return m.volume24hr / m.volume > 0.8;
                }
                return false;
            }).slice(0, limit);

            for (const market of newMarkets) {
                const signal = this.process(market);
                if (signal) {
                    signal.subtype = 'trending_new';
                    signals.push(signal);
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
