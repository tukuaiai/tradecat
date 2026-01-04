/**
 * 订单簿分析器
 *
 * 提供更多分析工具和可视化功能
 */

class OrderbookAnalyzer {
    /**
     * 可视化订单簿（生成ASCII图）
     * @param {Array} bids - 买单数组
     * @param {Array} asks - 卖单数组
     * @param {number} maxWidth - 最大条形宽度
     * @returns {string} - ASCII可视化
     */
    static visualize(bids, asks, maxWidth = 20) {
        if (!bids || !asks || bids.length === 0 || asks.length === 0) {
            return '订单簿为空';
        }

        const maxBidSize = Math.max(...bids.map(b => b.size || 0));
        const maxAskSize = Math.max(...asks.map(a => a.size || 0));
        const maxSize = Math.max(maxBidSize, maxAskSize);

        if (maxSize === 0) {
            return '订单簿无有效数据';
        }

        let output = '\n订单簿可视化：\n\n';

        // 卖单（从上到下，价格从高到低）
        const topAsks = asks.slice(0, 5).reverse();
        topAsks.forEach(ask => {
            const size = ask.size || 0;
            const barLength = Math.round((size / maxSize) * maxWidth);
            const bar = '█'.repeat(barLength);
            output += `${ask.price.toFixed(3)} │ ${bar.padEnd(maxWidth)} ${size.toFixed(0)}\n`;
        });

        output += '─────────┼' + '─'.repeat(maxWidth) + '──────────\n';

        // 买单（从上到下，价格从高到低）
        const topBids = bids.slice(0, 5);
        topBids.forEach(bid => {
            const size = bid.size || 0;
            const barLength = Math.round((size / maxSize) * maxWidth);
            const bar = '█'.repeat(barLength);
            output += `${bid.price.toFixed(3)} │ ${bar.padEnd(maxWidth)} ${size.toFixed(0)}\n`;
        });

        return output;
    }

    /**
     * 计算订单簿倾斜度
     * 返回值: -1到1之间，正值表示买方强，负值表示卖方强
     */
    static calculateSkew(bids, asks, levels = 10) {
        const bidSum = bids
            .slice(0, levels)
            .reduce((sum, b) => sum + (b.size || 0), 0);

        const askSum = asks
            .slice(0, levels)
            .reduce((sum, a) => sum + (a.size || 0), 0);

        const total = bidSum + askSum;
        if (total === 0) return 0;

        return (bidSum - askSum) / total;
    }

    /**
     * 检测订单簿墙（大单）
     * @param {Array} orders - 订单数组
     * @param {number} threshold - 阈值
     * @returns {Array} - 检测到的墙
     */
    static detectWalls(orders, threshold = 10000) {
        return orders
            .filter(order => (order.size || 0) >= threshold)
            .map(order => ({
                price: order.price,
                size: order.size,
                type: 'WALL'
            }));
    }

    /**
     * 计算订单簿流动性
     * @param {Array} bids - 买单
     * @param {Array} asks - 卖单
     * @returns {Object} - 流动性指标
     */
    static calculateLiquidity(bids, asks) {
        const totalBids = bids.reduce((sum, b) => sum + (b.size || 0), 0);
        const totalAsks = asks.reduce((sum, a) => sum + (a.size || 0), 0);

        return {
            total: totalBids + totalAsks,
            bids: totalBids,
            asks: totalAsks,
            ratio: totalAsks > 0 ? totalBids / totalAsks : Infinity,
            balance: totalBids - totalAsks
        };
    }

    /**
     * 计算加权平均价格
     * @param {Array} orders - 订单数组
     * @param {number} levels - 计算档位数
     * @returns {number} - 加权平均价格
     */
    static calculateWeightedAverage(orders, levels = 5) {
        const relevantOrders = orders.slice(0, levels);
        const totalSize = relevantOrders.reduce((sum, o) => sum + (o.size || 0), 0);

        if (totalSize === 0) return 0;

        const weightedSum = relevantOrders.reduce(
            (sum, o) => sum + o.price * (o.size || 0),
            0
        );

        return weightedSum / totalSize;
    }

    /**
     * 分析价差
     * @param {Array} bids - 买单
     * @param {Array} asks - 卖单
     * @returns {Object} - 价差分析
     */
    static analyzeSpread(bids, asks) {
        if (!bids || !asks || bids.length === 0 || asks.length === 0) {
            return null;
        }

        const bestBid = bids[0].price;
        const bestAsk = asks[0].price;
        const spread = bestAsk - bestBid;
        const midPrice = (bestBid + bestAsk) / 2;
        const spreadPercent = (spread / midPrice) * 100;

        return {
            bestBid,
            bestAsk,
            spread,
            midPrice,
            spreadPercent: spreadPercent.toFixed(2),
            isTight: spreadPercent < 1,  // <1% 认为是紧密价差
            isWide: spreadPercent > 5    // >5% 认为是宽松价差
        };
    }

    /**
     * 生成订单簿深度柱状图（用于Telegram）
     * @param {number} buyDepth - 买方深度
     * @param {number} sellDepth - 卖方深度
     * @param {number} maxLength - 最大长度
     * @returns {Object} - {buyBar, sellBar}
     */
    static generateDepthBars(buyDepth, sellDepth, maxLength = 16) {
        const maxDepth = Math.max(buyDepth, sellDepth);

        if (maxDepth === 0) {
            return { buyBar: '', sellBar: '' };
        }

        const buyBarLength = Math.round((buyDepth / maxDepth) * maxLength);
        const sellBarLength = Math.round((sellDepth / maxDepth) * maxLength);

        return {
            buyBar: '█'.repeat(buyBarLength),
            sellBar: '█'.repeat(sellBarLength)
        };
    }

    /**
     * 格式化金额（K, M, B）
     * @param {number} amount - 金额
     * @returns {string} - 格式化后的金额
     */
    static formatAmount(amount) {
        if (amount >= 1000000000) {
            return `$${(amount / 1000000000).toFixed(2)}B`;
        } else if (amount >= 1000000) {
            return `$${(amount / 1000000).toFixed(2)}M`;
        } else if (amount >= 1000) {
            return `$${(amount / 1000).toFixed(1)}K`;
        } else {
            return `$${amount.toFixed(0)}`;
        }
    }

    /**
     * 检测订单簿模式
     * @param {Array} bids - 买单
     * @param {Array} asks - 卖单
     * @returns {string} - 模式名称
     */
    static detectPattern(bids, asks) {
        const liquidity = this.calculateLiquidity(bids, asks);
        const spread = this.analyzeSpread(bids, asks);

        if (!spread) return 'UNKNOWN';

        // 检测各种模式
        if (liquidity.ratio > 10) {
            return 'BULLISH_IMBALANCE';  // 买方失衡
        } else if (liquidity.ratio < 0.1) {
            return 'BEARISH_IMBALANCE';  // 卖方失衡
        } else if (spread.isTight && Math.abs(liquidity.balance) < liquidity.total * 0.1) {
            return 'TIGHT_BALANCED';     // 紧密均衡
        } else if (spread.isWide) {
            return 'WIDE_ILLIQUID';      // 宽松低流动性
        } else {
            return 'NORMAL';             // 正常
        }
    }

    /**
     * 计算订单簿健康度评分（0-100）
     * @param {Array} bids - 买单
     * @param {Array} asks - 卖单
     * @returns {number} - 健康度评分
     */
    static calculateHealthScore(bids, asks) {
        let score = 100;

        const liquidity = this.calculateLiquidity(bids, asks);
        const spread = this.analyzeSpread(bids, asks);

        if (!spread) return 0;

        // 流动性评分（最多-30分）
        if (liquidity.total < 1000) score -= 30;
        else if (liquidity.total < 5000) score -= 20;
        else if (liquidity.total < 10000) score -= 10;

        // 价差评分（最多-30分）
        const spreadPercent = parseFloat(spread.spreadPercent);
        if (spreadPercent > 10) score -= 30;
        else if (spreadPercent > 5) score -= 20;
        else if (spreadPercent > 2) score -= 10;

        // 均衡评分（最多-40分）
        const imbalance = Math.abs(liquidity.ratio - 1);
        if (imbalance > 20) score -= 40;
        else if (imbalance > 10) score -= 30;
        else if (imbalance > 5) score -= 20;
        else if (imbalance > 2) score -= 10;

        return Math.max(0, Math.min(100, score));
    }
}

module.exports = OrderbookAnalyzer;
