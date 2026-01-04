/**
 * 扫尾盘检测器 (SDK 版本)
 * 
 * 数据源: poly-sdk Gamma API
 * 职责: 扫描即将结束的高确定性市场
 */

class ClosingMarketScanner {
    constructor(config = {}) {
        this.timeWindowHours = config.timeWindowHours || 6;
        this.highConfidenceHours = config.highConfidenceHours || 2;
        this.mediumConfidenceHours = config.mediumConfidenceHours || 12;
        this.minVolume = config.minVolume || 0;
        this.minLiquidity = config.minLiquidity || 0;
        this.minPriceDeviation = config.minPriceDeviation || 0;
        this.minAbsoluteThreshold = config.minAbsoluteThreshold || 0;
        this.maxMarkets = config.maxMarkets || 10;
        this.refreshIntervalMs = config.refreshIntervalMs || 300000;
        this.emitEmpty = config.emitEmpty === true;
        this.debug = Boolean(config.debug);

        this.lastDigest = null;
        this.lastScanTime = 0;
        this.stats = { scans: 0, emissions: 0, marketsLastSignal: 0, lastSignalAt: null };
        this.alertHistory = [];
        this.MAX_ALERT_HISTORY = 10;

        // SDK 实例 (外部注入)
        this.sdk = config.sdk || null;
    }

    setSDK(sdk) {
        this.sdk = sdk;
    }

    /**
     * 使用 SDK 扫描即将结束的市场
     */
    async scan() {
        const now = Date.now();
        if (now - this.lastScanTime < this.refreshIntervalMs) {
            return null;
        }
        this.lastScanTime = now;
        this.stats.scans++;
        console.log(`📋 [扫尾盘] 开始扫描... (第${this.stats.scans}次)`);

        let markets = [];

        try {
            if (this.sdk) {
                // 使用 SDK
                markets = await this.fetchWithSDK();
            } else {
                // 降级到原生 fetch
                markets = await this.fetchWithNative();
            }
            console.log(`📋 [扫尾盘] 获取到 ${markets.length} 个市场`);
        } catch (error) {
            console.error('❌ 扫尾盘扫描失败:', error.message);
            return null;
        }

        if (!markets.length && !this.emitEmpty) {
            console.log('📋 [扫尾盘] 无市场数据，跳过');
            return null;
        }

        const processed = this.analyzeMarkets(markets);
        console.log(`📋 [扫尾盘] 过滤后 ${processed.length} 个市场`);
        const digest = this.buildDigest(processed);

        if (digest === this.lastDigest) {
            console.log('📋 [扫尾盘] 数据无变化，跳过');
            return null;
        }
        this.lastDigest = digest;

        if (processed.length === 0 && !this.emitEmpty) {
            return null;
        }

        const payload = this.buildPayload(processed);
        this.updateStats(payload, processed);
        this.updateAlertHistory(processed);

        return payload;
    }

    /**
     * 使用 SDK 获取快结算的市场（分页拉取全部）
     */
    async fetchWithSDK() {
        const endMax = Date.now() + this.timeWindowHours * 3600 * 1000;
        const allMarkets = [];
        let offset = 0;
        const limit = 500;

        while (true) {
            const batch = await this.sdk.gammaApi.getMarkets({
                active: true,
                closed: false,
                limit,
                offset,
                order: 'endDate',
                ascending: true
            });

            if (!batch.length) break;
            
            // 过滤时间窗口内的市场
            for (const m of batch) {
                if (!m.endDate) continue;
                const endTime = new Date(m.endDate).getTime();
                if (endTime > Date.now() && endTime <= endMax) {
                    allMarkets.push(m);
                }
            }

            // 如果最后一个市场已超出时间窗口，停止拉取
            const lastEnd = batch[batch.length - 1]?.endDate;
            if (lastEnd && new Date(lastEnd).getTime() > endMax) break;
            
            if (batch.length < limit) break;
            offset += limit;
        }

        console.log(`📋 [扫尾盘] 分页拉取完成，共 ${allMarkets.length} 个市场`);
        return allMarkets;
    }

    /**
     * 降级: 原生 fetch（分页拉取全部）
     */
    async fetchWithNative() {
        const endMax = Date.now() + this.timeWindowHours * 3600 * 1000;
        const allMarkets = [];
        let offset = 0;
        const limit = 500;

        while (true) {
            const params = new URLSearchParams({
                active: 'true',
                closed: 'false',
                limit: String(limit),
                offset: String(offset),
                order: 'endDate',
                ascending: 'true'
            });

            const url = `https://gamma-api.polymarket.com/markets?${params}`;
            const response = await fetch(url, { headers: { 'Accept': 'application/json' } });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            const batch = Array.isArray(data) ? data : (data?.data || []);

            if (!batch.length) break;

            for (const m of batch) {
                if (!m.endDate) continue;
                const endTime = new Date(m.endDate).getTime();
                if (endTime > Date.now() && endTime <= endMax) {
                    allMarkets.push(m);
                }
            }

            const lastEnd = batch[batch.length - 1]?.endDate;
            if (lastEnd && new Date(lastEnd).getTime() > endMax) break;

            if (batch.length < limit) break;
            offset += limit;
        }

        console.log(`📋 [扫尾盘] 分页拉取完成，共 ${allMarkets.length} 个市场`);
        return allMarkets;
    }

    /**
     * 分析和过滤市场
     */
    analyzeMarkets(markets) {
        const now = Date.now();

        return markets
            .map(raw => this.processMarket(raw, now))
            .filter(Boolean)
            .sort((a, b) => {
                if (b.score !== a.score) return b.score - a.score;
                if (a.timeRemainingMs !== b.timeRemainingMs) return a.timeRemainingMs - b.timeRemainingMs;
                return b.volume - a.volume;
            })
            .slice(0, this.maxMarkets);
    }

    /**
     * 处理单个市场
     */
    processMarket(raw, now) {
        // 解析结束时间
        const endDateIso = raw.endDate || raw.end_date || raw.endDateIso;
        if (!endDateIso) return null;

        const endTime = new Date(endDateIso).getTime();
        if (!Number.isFinite(endTime)) return null;

        const timeRemainingMs = endTime - now;
        const hoursLeft = timeRemainingMs / 3600000;

        if (hoursLeft <= 0 || hoursLeft > this.timeWindowHours) return null;

        // SDK 数据字段 - API 返回的是字符串，需要转数字
        const volume = parseFloat(raw.volumeNum || raw.volume) || 0;
        const liquidity = parseFloat(raw.liquidityNum || raw.liquidity) || 0;

        // 价格 (API 返回字符串数组如 ["0.061", "0.939"])
        let yesPrice = null;
        let noPrice = null;
        
        if (raw.outcomePrices) {
            const prices = typeof raw.outcomePrices === 'string' 
                ? JSON.parse(raw.outcomePrices) 
                : raw.outcomePrices;
            yesPrice = parseFloat(prices[0]);
            noPrice = parseFloat(prices[1]);
        }

        // 兼容 tokens 格式
        if (!Number.isFinite(yesPrice) && raw.tokens) {
            const yesToken = raw.tokens.find(t => t.outcome?.toLowerCase() === 'yes') || raw.tokens[0];
            const noToken = raw.tokens.find(t => t.outcome?.toLowerCase() === 'no') || raw.tokens[1];
            yesPrice = parseFloat(yesToken?.price);
            noPrice = parseFloat(noToken?.price);
        }

        yesPrice = Number.isFinite(yesPrice) ? yesPrice : null;
        noPrice = Number.isFinite(noPrice) ? noPrice : null;

        // 评分（仅用于排序，不过滤）
        const { score, confidence, reasons } = this.scoreMarket({ hoursLeft, volume, liquidity, yesPrice, noPrice });

        return {
            conditionId: raw.conditionId || raw.condition_id || raw.id,
            marketId: raw.id || raw.conditionId,
            eventSlug: raw.eventSlug || raw.event_slug,
            marketSlug: raw.slug || raw.market_slug,
            question: raw.question || raw.title || 'Unknown',
            endDateIso,
            timeRemainingMs,
            hoursLeft,
            minutesLeft: timeRemainingMs / 60000,
            volume,
            liquidity,
            yesPrice,
            noPrice,
            // SDK 额外数据
            volume24hr: raw.volume24hr,
            oneDayPriceChange: raw.oneDayPriceChange,
            bestBid: raw.bestBid,
            bestAsk: raw.bestAsk,
            tags: raw.tags,
            score,
            confidence,
            reasons
        };
    }

    /**
     * 评分
     */
    scoreMarket(metrics) {
        const reasons = [];
        let score = 0;
        let confidence = 'LOW';

        // 时间评分
        if (metrics.hoursLeft <= this.highConfidenceHours) {
            score += 40;
            confidence = 'HIGH';
            reasons.push('⏰ 剩余时间极短');
        } else if (metrics.hoursLeft <= this.mediumConfidenceHours) {
            score += 25;
            confidence = 'MEDIUM';
            reasons.push('🕒 剩余时间适中');
        } else {
            score += 10;
        }

        // 成交量评分
        if (metrics.volume >= 200000) {
            score += 25;
            reasons.push('💰 成交量 > $200K');
        } else if (metrics.volume >= 50000) {
            score += 18;
        } else if (metrics.volume >= 10000) {
            score += 10;
        }

        // 流动性评分
        if (metrics.liquidity >= 100000) {
            score += 20;
            reasons.push('💧 流动性 > $100K');
        } else if (metrics.liquidity >= 25000) {
            score += 12;
        }

        // 价格确定性评分
        if (metrics.yesPrice !== null && metrics.noPrice !== null) {
            const maxPrice = Math.max(metrics.yesPrice, metrics.noPrice);

            if (maxPrice >= 0.95) {
                score += 30;
                reasons.push('🔥 极端市场 ≥ 95%');
            } else if (maxPrice >= 0.90) {
                score += 25;
                reasons.push('🎯 高确定性 ≥ 90%');
            } else if (maxPrice >= 0.80) {
                score += 20;
                reasons.push('📈 强倾向 ≥ 80%');
            } else if (maxPrice >= 0.70) {
                score += 15;
            }
        }

        return { score, confidence, reasons };
    }

    buildDigest(markets) {
        if (!markets.length) return 'EMPTY';
        return markets.map(m => m.conditionId).sort().join('|');
    }

    buildPayload(processed) {
        const confidenceOrder = { HIGH: 3, MEDIUM: 2, LOW: 1 };
        const maxConfidence = processed.reduce((best, m) => {
            return (confidenceOrder[m.confidence] || 0) > (confidenceOrder[best] || 0) ? m.confidence : best;
        }, 'LOW');

        return {
            generatedAt: new Date(),
            windowHours: this.timeWindowHours,
            refreshIntervalMs: this.refreshIntervalMs,
            markets: processed,
            maxConfidence,
            maxConfidenceRank: confidenceOrder[maxConfidence] || 0
        };
    }

    updateStats(payload, processed) {
        this.stats.emissions++;
        this.stats.lastSignalAt = payload.generatedAt;
        this.stats.marketsLastSignal = processed.length;
    }

    updateAlertHistory(processed) {
        for (const m of processed) {
            if (!this.alertHistory.find(a => a.market === m.conditionId)) {
                this.alertHistory.push({
                    market: m.conditionId,
                    name: m.question?.substring(0, 50) || m.conditionId.substring(0, 12),
                    time: Date.now(),
                    value: this.formatTimeLeft(m.minutesLeft),
                    slug: m.marketSlug,
                    eventSlug: m.eventSlug
                });
            }
        }
        if (this.alertHistory.length > this.MAX_ALERT_HISTORY) {
            this.alertHistory = this.alertHistory.slice(-this.MAX_ALERT_HISTORY);
        }
    }

    formatTimeLeft(minutes) {
        if (minutes < 60) return `${Math.round(minutes)}分`;
        if (minutes < 1440) return `${Math.round(minutes / 60)}小时`;
        return `${Math.round(minutes / 1440)}天`;
    }

    getStats() {
        return { ...this.stats };
    }

    getAlertHistory() {
        return this.alertHistory.map(a => ({ ...a, type: 'closing', icon: '⏰' }));
    }
}

module.exports = ClosingMarketScanner;
