/**
 * 聪明钱检测器 (SDK 版本)
 * 
 * 数据源: poly-sdk Data API (positions, trades, leaderboard)
 * 职责: 跟踪排行榜顶级交易者的持仓变化
 * 
 * 核心逻辑:
 * - 监控 Top N 交易者的持仓变化
 * - 检测建仓/加仓/减仓/清仓
 * - 聪明钱 = 排行榜高手，不是大额交易
 */

class SmartMoneyDetector {
    constructor(config = {}) {
        this.trackTopN = config.trackTopN ?? 20;            // 跟踪前20名
        this.minSmartScore = config.minSmartScore || 60;    // 最低评分
        this.minPositionValue = config.minPositionValue ?? 1000; // 最小持仓价值
        this.scanIntervalMs = config.scanIntervalMs || 300000;   // 扫描间隔 5分钟
        this.cooldown = config.cooldown ?? 600000;          // 同一市场冷却 10分钟
        this.maxSignalsPerHour = config.maxSignalsPerHour || 50;
        this.disableRateLimit = config.disableRateLimit === true;

        // 跟踪的钱包
        this.trackedWallets = new Map(); // address -> { profile, lastPositions }
        this.lastSignals = new Map();    // `${wallet}:${market}` -> timestamp
        this.lastScanTime = 0;
        this.stats = { detected: 0, sent: 0, skipped: 0, signalsThisHour: 0, lastHourReset: Date.now() };

        // SDK 实例 (外部注入)
        this.sdk = config.sdk || null;
    }

    setSDK(sdk) {
        this.sdk = sdk;
    }

    /**
     * 扫描聪明钱持仓变化
     */
    async scan() {
        if (!this.sdk) return [];

        const now = Date.now();
        if (now - this.lastScanTime < this.scanIntervalMs) {
            return [];
        }
        this.lastScanTime = now;

        const signals = [];

        try {
            // 1. 获取排行榜
            const topTraders = await this.sdk.wallets.getTopTraders(this.trackTopN);

            for (const trader of topTraders) {
                // 2. 获取钱包画像
                let profile;
                try {
                    profile = await this.sdk.wallets.getWalletProfile(trader.address);
                } catch (e) {
                    continue;
                }

                // 过滤低评分
                if (profile.smartScore < this.minSmartScore) continue;

                // 3. 获取当前持仓
                const currentPositions = await this.sdk.dataApi.getPositions(trader.address);

                // 4. 对比历史持仓
                const tracked = this.trackedWallets.get(trader.address);
                const prevPositions = tracked?.lastPositions || [];
                const prevMap = new Map(prevPositions.map(p => [p.conditionId, p]));

                for (const pos of currentPositions) {
                    const value = (pos.size || 0) * (pos.curPrice || pos.avgPrice || 0);
                    if (value < this.minPositionValue) continue;

                    const prev = prevMap.get(pos.conditionId);
                    const key = `${trader.address}:${pos.conditionId}`;

                    // 冷却检查
                    if (!this.disableRateLimit) {
                        const lastTime = this.lastSignals.get(key) || 0;
                        if (now - lastTime < this.cooldown) continue;
                    }

                    let signal = null;

                    // 新建仓
                    if (!prev && pos.size > 0) {
                        signal = this.createSignal('new_position', trader, profile, pos, { value });
                    }
                    // 加仓 (增加 > 20%)
                    else if (prev && pos.size > prev.size * 1.2) {
                        const addedSize = pos.size - prev.size;
                        const addedValue = addedSize * (pos.curPrice || 0);
                        if (addedValue >= this.minPositionValue) {
                            signal = this.createSignal('add_position', trader, profile, pos, {
                                value: addedValue,
                                previousSize: prev.size,
                                currentSize: pos.size
                            });
                        }
                    }
                    // 减仓 (减少 > 20%)
                    else if (prev && pos.size < prev.size * 0.8) {
                        const reducedSize = prev.size - pos.size;
                        const reducedValue = reducedSize * (pos.curPrice || 0);
                        if (reducedValue >= this.minPositionValue) {
                            signal = this.createSignal('reduce_position', trader, profile, pos, {
                                value: reducedValue,
                                previousSize: prev.size,
                                currentSize: pos.size
                            });
                        }
                    }

                    if (signal) {
                        this.lastSignals.set(key, now);
                        signals.push(signal);
                    }
                }

                // 清仓检测
                for (const [conditionId, prev] of prevMap) {
                    const current = currentPositions.find(p => p.conditionId === conditionId);
                    if (!current || current.size === 0) {
                        const value = (prev.size || 0) * (prev.curPrice || 0);
                        if (value >= this.minPositionValue) {
                            const key = `${trader.address}:${conditionId}`;
                            const lastTime = this.lastSignals.get(key) || 0;
                            if (this.disableRateLimit || now - lastTime >= this.cooldown) {
                                const signal = this.createSignal('close_position', trader, profile, prev, {
                                    value,
                                    pnl: prev.cashPnl,
                                    pnlPercent: prev.percentPnl
                                });
                                this.lastSignals.set(key, now);
                                signals.push(signal);
                            }
                        }
                    }
                }

                // 更新跟踪数据
                this.trackedWallets.set(trader.address, {
                    profile,
                    lastPositions: currentPositions,
                    updatedAt: now
                });
            }
        } catch (error) {
            console.error('❌ 聪明钱扫描失败:', error.message);
        }

        this.stats.detected += signals.length;
        return signals;
    }

    createSignal(subtype, trader, profile, position, extra = {}) {
        return {
            type: 'smart_money',
            subtype,
            market: position.conditionId,
            conditionId: position.conditionId,
            marketSlug: position.slug,
            eventSlug: position.eventSlug,
            marketName: position.title,
            outcome: position.outcome,
            price: position.curPrice || position.avgPrice,
            size: position.size,
            // 交易者信息
            trader: trader.address,
            traderRank: trader.rank,
            traderPnL: trader.pnl,
            traderVolume: trader.volume,
            smartScore: profile.smartScore,
            // 额外数据
            ...extra,
            timestamp: Date.now()
        };
    }

    getStats() {
        return {
            ...this.stats,
            trackedWallets: this.trackedWallets.size,
            cacheSize: this.lastSignals.size
        };
    }

    cleanup() {
        const now = Date.now();
        for (const [k, v] of this.lastSignals) {
            if (now - v > this.cooldown * 10) this.lastSignals.delete(k);
        }
    }
}

module.exports = SmartMoneyDetector;
