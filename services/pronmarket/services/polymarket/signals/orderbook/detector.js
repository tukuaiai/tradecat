/**
 * 📚 订单簿失衡检测器
 *
 * 功能：检测买卖力量严重失衡
 * 难度：⭐⭐☆☆☆
 */

class OrderbookDetector {
    constructor(config = {}) {
        // 配置
        this.MIN_IMBALANCE = config.minImbalance || 10;      // 最低10倍失衡
        this.MIN_DEPTH = config.minDepth || 1000;            // 最小深度$1K
        this.DEPTH_LEVELS = config.depthLevels || 3;         // 计算前3档
        this.MIN_PRICE_IMPACT = config.minPriceImpact || 1.0; // 最小价格冲击1%
        this.COOLDOWN = config.cooldown || 120000;           // 2分钟冷却
        this.MAX_SIGNALS_PER_HOUR = config.maxSignalsPerHour || 15;
        this.HISTORY_SIZE = config.historySize || 10;

        // 冷却时间管理
        this.lastSignals = new Map();

        // 警报历史（最多10条）
        this.alertHistory = [];
        this.MAX_ALERT_HISTORY = 10;

        // 每小时信号计数
        this.hourlySignals = [];

        // 订单簿历史（用于检测稳定性）
        this.orderbookHistory = new Map();

        // 市场元数据缓存（名称/slug，用于警报面板展示）
        this.marketNames = new Map();
        this.marketSlugs = new Map();
        this.eventSlugs = new Map();

        // 统计
        this.stats = {
            detected: 0,
            sent: 0,
            skipped: 0,
            lastSignal: null
        };

        console.log('✅ 订单簿检测器初始化完成');
        console.log(`   最低失衡比例: ${this.MIN_IMBALANCE}倍`);
        console.log(`   最小深度: $${this.MIN_DEPTH}`);
        console.log(`   计算档位: 前${this.DEPTH_LEVELS}档`);
    }

    /**
     * 处理订单簿更新
     * @param {Object} message - WebSocket消息
     * @returns {Object|null} - 信号对象或null
     */
    processOrderbook(message) {
        try {
        const payload = message.payload;

        // 提取关键信息
        const market = payload.market || payload.condition_id;
        const bids = this.normalizeBook(payload.bids);
        const asks = this.normalizeBook(payload.asks);
        const marketName = payload.title || null;
        const marketSlug = payload.slug || payload.marketSlug || null;
        const eventSlug = payload.eventSlug || payload.event_slug || null;

        if (!market || bids.length === 0 || asks.length === 0) {
            return null;
        }

        // 缓存市场元信息，供警报历史与链接使用
        if (marketName) this.marketNames.set(market, marketName);
        if (marketSlug) this.marketSlugs.set(market, marketSlug);
        if (eventSlug) this.eventSlugs.set(market, eventSlug);

        // 分析订单簿
        const analysis = this.analyzeOrderbook(bids, asks);

            // 保存订单簿历史摘要
            this.saveHistory(market, {
                buyDepth: analysis.buyDepth,
                sellDepth: analysis.sellDepth,
                imbalance: analysis.imbalance,
                direction: analysis.direction,
                bestBid: analysis.bestBid,
                bestAsk: analysis.bestAsk
            });

            // 检测失衡
        const signal = this.detect(market, analysis);

        // 如果检测到信号，添加 slug 信息
        if (signal) {
            // 从 payload 中提取 slug（如果有的话）
            signal.marketSlug = marketSlug || this.marketSlugs.get(market) || null;
            signal.eventSlug = eventSlug || this.eventSlugs.get(market) || null;
            signal.marketName = marketName || this.marketNames.get(market) || signal.market;
        }

            return signal;

        } catch (error) {
            console.error('❌ 处理订单簿更新失败:', error.message);
            return null;
        }
    }

    /**
     * 提取价格（支持多种格式）
     */
    extractPrice(order) {
        if (!order) return 0;

        // 格式1: {price: number}
        if (order.price !== undefined) {
            return parseFloat(order.price) || 0;
        }

        // 格式2: [price, size]
        if (Array.isArray(order) && order.length >= 1) {
            return parseFloat(order[0]) || 0;
        }

        // 格式3: 直接是数字
        if (typeof order === 'number') {
            return order;
        }

        return 0;
    }

    normalizeOrder(order) {
        if (!order) {
            return null;
        }

        if (Array.isArray(order)) {
            const price = parseFloat(order[0]);
            const size = parseFloat(order[1] ?? 0);
            if (!Number.isFinite(price) || !Number.isFinite(size)) {
                return null;
            }
            return { price, size };
        }

        const rawPrice = order.price ?? order.p ?? order[0];
        const rawSize = order.size ?? order.amount ?? order.quantity ?? order.q ?? order[1];

        const price = parseFloat(rawPrice);
        const size = parseFloat(rawSize);

        if (!Number.isFinite(price) || !Number.isFinite(size)) {
            return null;
        }

        return { price, size };
    }

    normalizeBook(orders) {
        const normalized = [];
        for (const order of orders || []) {
            const normalizedOrder = this.normalizeOrder(order);
            if (normalizedOrder) {
                normalized.push(normalizedOrder);
            }
        }
        return normalized;
    }

    /**
     * 分析订单簿（核心逻辑）
     */
    analyzeOrderbook(bids, asks) {
        // 1. 计算买方深度（前N档）
        const buyDepth = this.calculateDepth(bids, this.DEPTH_LEVELS);

        // 2. 计算卖方深度（前N档）
        const sellDepth = this.calculateDepth(asks, this.DEPTH_LEVELS);

        // 3. 计算失衡比例
        let ratio, direction, imbalance;

        if (buyDepth > sellDepth && sellDepth > 0) {
            // 买方强势
            direction = 'BULLISH';
            ratio = buyDepth / sellDepth;
            imbalance = ratio;
        } else if (sellDepth > buyDepth && buyDepth > 0) {
            // 卖方强势
            direction = 'BEARISH';
            ratio = sellDepth / buyDepth;
            imbalance = ratio;
        } else {
            // 均衡
            direction = 'NEUTRAL';
            ratio = 1;
            imbalance = 1;
        }

        // 4. 预测价格变动
        const priceImpact = this.estimatePriceImpact(
            direction === 'BULLISH' ? asks : bids,
            direction === 'BULLISH' ? buyDepth : sellDepth
        );

        // 5. 获取最优价格（支持多种格式）
        const bestBid = this.extractPrice(bids[0]);
        const bestAsk = this.extractPrice(asks[0]);
        const hasValidQuotes = Number.isFinite(bestBid) && Number.isFinite(bestAsk);
        const midPrice = hasValidQuotes ? (bestBid + bestAsk) / 2 : 0;
        const spread = hasValidQuotes ? (bestAsk - bestBid) : 0;

        return {
            buyDepth,
            sellDepth,
            ratio,
            direction,
            imbalance,
            priceImpact,
            bestBid,
            bestAsk,
            midPrice,
            spread,
            bids: bids.slice(0, Math.min(3, bids.length)),
            asks: asks.slice(0, Math.min(3, asks.length))
        };
    }

    /**
     * 计算订单簿深度（美元面值）
     * 在 Polymarket 中，size 已经是美元面值，不需要乘以 price
     */
    calculateDepth(orders, levels) {
        let depth = 0;

        for (let i = 0; i < Math.min(levels, orders.length); i++) {
            const size = orders[i]?.size || 0;
            if (Number.isFinite(size)) {
                depth += size;
            }
        }

        return depth;
    }

    /**
     * 估算价格冲击
     * 模拟用 volume 数量的订单去吃对手盘
     */
    estimatePriceImpact(passiveOrders, volume) {
        if (!passiveOrders || passiveOrders.length === 0 || volume === 0) {
            return 0;
        }

        let remaining = volume;
        let totalCost = 0;
        let filledVolume = 0;

        for (const order of passiveOrders) {
            if (remaining <= 0) break;

            if (!Number.isFinite(order.size) || order.size <= 0) {
                continue;
            }

            const fillSize = Math.min(remaining, order.size);

            totalCost += fillSize * order.price;
            filledVolume += fillSize;
            remaining -= fillSize;
        }

        if (filledVolume === 0) return 0;

        // 平均成交价
        const avgPrice = totalCost / filledVolume;

        // 当前最优价
        const currentPrice = passiveOrders[0]?.price || avgPrice;

        if (currentPrice === 0) return 0;

        // 价格冲击百分比
        const impact = ((avgPrice - currentPrice) / currentPrice) * 100;

        return Math.abs(impact);
    }

    /**
     * 检测失衡并生成信号
     */
    detect(market, analysis) {
        const {
            buyDepth,
            sellDepth,
            imbalance,
            direction,
            priceImpact,
            bestBid,
            bestAsk,
            midPrice,
            spread
        } = analysis;

        // 1. 检查方向（只关注买方或卖方强势，不关注中性）
        if (direction === 'NEUTRAL') {
            return null;
        }

        // 2. 检查失衡是否达到阈值
        if (imbalance < this.MIN_IMBALANCE) {
            return null;
        }

        // 3. 检查深度是否足够
        const maxDepth = Math.max(buyDepth, sellDepth);
        if (maxDepth < this.MIN_DEPTH) {
            return null;
        }

        // 4. 检查价格冲击是否足够大
        if (priceImpact < this.MIN_PRICE_IMPACT) {
            return null;  // 预期涨跌幅太小
        }

        // 5. 检查冷却时间
        if (!this.checkCooldown(market)) {
            this.stats.skipped++;
            return null;
        }

        // 6. 检查每小时限流
        if (!this.checkHourlyLimit()) {
            this.stats.skipped++;
            return null;
        }

        // 检测到失衡！
        this.stats.detected++;
        this.stats.sent++;
        this.stats.lastSignal = Date.now();

        // 更新冷却时间
        this.lastSignals.set(market, Date.now());

        // 添加到警报历史
        const displayName = this.marketNames.get(market) || market.substring(0, 12);
        const historySlug = this.marketSlugs.get(market) || null;
        const historyEventSlug = this.eventSlugs.get(market) || null;
        this.alertHistory.push({
            market,
            name: displayName,
            time: Date.now(),
            value: imbalance.toFixed(1) + 'x',
            slug: historySlug,
            eventSlug: historyEventSlug
        });
        if (this.alertHistory.length > this.MAX_ALERT_HISTORY) {
            this.alertHistory.shift();
        }

        // 添加到每小时计数
        this.hourlySignals.push(Date.now());

        // 计算预期价格
        const expectedChange = direction === 'BULLISH' ? priceImpact : -priceImpact;
        let expectedPrice = midPrice * (1 + expectedChange / 100);
        const spreadPercent = midPrice > 0 ? (spread / midPrice) * 100 : 0;

        // 限制价格在 0-1 范围内（Polymarket 预测市场特性）
        expectedPrice = Math.max(0.001, Math.min(0.999, expectedPrice));

        console.log(`🎉 发现订单簿失衡！市场: ${market.substring(0, 12)}, 方向: ${direction}, 失衡: ${imbalance.toFixed(1)}x`);

        return {
            type: 'ORDERBOOK_IMBALANCE',
            market: market,
            direction: direction,
            imbalance: imbalance.toFixed(1),
            buyDepth: Math.round(buyDepth),
            sellDepth: Math.round(sellDepth),
            currentPrice: midPrice.toFixed(3),
            expectedPrice: expectedPrice.toFixed(3),
            priceImpact: priceImpact.toFixed(2),
            expectedChange: expectedChange.toFixed(2),
            spread: spread.toFixed(4),
            spreadPercent: spreadPercent.toFixed(2),
            strength: this.calculateStrength(imbalance, priceImpact),
            urgency: imbalance > 20 ? 'URGENT' : 'HIGH',
            timeWindow: 1800,  // 30分钟
            timestamp: Date.now(),

            // 详细信息
            details: {
                bestBid: bestBid.toFixed(3),
                bestAsk: bestAsk.toFixed(3),
                bidVolume: Math.round(buyDepth),
                askVolume: Math.round(sellDepth),
                bids: analysis.bids,
                asks: analysis.asks
            }
        };
    }

    /**
     * 计算信号强度（1-5星）
     */
    calculateStrength(imbalance, priceImpact) {
        let score = 0;

        // 失衡贡献（最多3分）
        if (imbalance > 50) score += 3;
        else if (imbalance > 30) score += 2.5;
        else if (imbalance > 20) score += 2;
        else if (imbalance > 10) score += 1;

        // 价格冲击贡献（最多2分）
        if (Math.abs(priceImpact) > 10) score += 2;
        else if (Math.abs(priceImpact) > 5) score += 1.5;
        else if (Math.abs(priceImpact) > 3) score += 1;

        return Math.min(5, Math.max(1, Math.round(score)));
    }

    /**
     * 检查冷却时间
     */
    checkCooldown(market) {
        const lastTime = this.lastSignals.get(market);
        if (!lastTime) return true;

        const elapsed = Date.now() - lastTime;
        if (elapsed < this.COOLDOWN) {
            console.log(`⏸️ 冷却中... 剩余 ${Math.ceil((this.COOLDOWN - elapsed) / 1000)}s`);
            return false;
        }

        return true;
    }

    /**
     * 检查每小时限流
     */
    checkHourlyLimit() {
        const now = Date.now();
        const oneHourAgo = now - 3600000;

        // 清理1小时前的记录
        this.hourlySignals = this.hourlySignals.filter(time => time > oneHourAgo);

        if (this.hourlySignals.length >= this.MAX_SIGNALS_PER_HOUR) {
            console.log(`⏸️ 达到每小时限制 (${this.MAX_SIGNALS_PER_HOUR})`);
            return false;
        }

        return true;
    }

    /**
     * 保存订单簿历史
     */
    saveHistory(market, summary) {
        if (!this.orderbookHistory.has(market)) {
            this.orderbookHistory.set(market, []);
        }

        const history = this.orderbookHistory.get(market);
        history.push({
            timestamp: Date.now(),
            metrics: summary
        });

        // 只保留最近 N 条（默认 10 条）
        if (history.length > this.HISTORY_SIZE) {
            history.shift();
        }
    }

    /**
     * 获取统计信息
     */
    getStats() {
        return {
            ...this.stats,
            marketsTracked: this.orderbookHistory.size,
            signalsThisHour: this.hourlySignals.length
        };
    }

    /**
     * 获取警报历史
     */
    getAlertHistory() {
        return this.alertHistory.map(a => ({ ...a, type: 'orderbook', icon: '📚' }));
    }

    /**
     * 清理过期数据
     */
    cleanup(maxAge = 3600000) {
        const now = Date.now();
        let removed = 0;

        for (const [market, history] of this.orderbookHistory.entries()) {
            if (history.length > 0) {
                const latestTime = history[history.length - 1].timestamp;
                if (now - latestTime > maxAge) {
                    this.orderbookHistory.delete(market);
                    this.lastSignals.delete(market);
                    removed++;
                }
            }
        }

        // 清理孤立的 lastSignals
        for (const [market, time] of this.lastSignals.entries()) {
            if (now - time > maxAge * 10) {
                this.lastSignals.delete(market);
            }
        }

        if (removed > 0) {
            console.log(`🧹 清理了 ${removed} 个市场的订单簿历史`);
        }
    }
}

module.exports = OrderbookDetector;
