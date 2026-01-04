#!/usr/bin/env node
/**
 * Ask价格迁移监控脚本
 *
 * 用于监控从bid/成交价到ask价格的迁移效果
 * 对比两种方式的差异，跟踪关键指标
 */

const { RealTimeDataClient } = require('../dist/index');

// 配置
const MONITOR_DURATION = 300000;  // 监控5分钟
const LOG_INTERVAL = 30000;       // 每30秒输出统计

// 统计数据
const stats = {
    messages: {
        total: 0,
        priceChange: 0,
        orderbook: 0,
        trades: 0
    },
    prices: {
        withAsk: 0,
        withoutAsk: 0,
        fallbackToLast: 0
    },
    arbitrage: {
        // 使用bid/成交价
        bidMethod: {
            detected: 0,
            totalProfit: 0
        },
        // 使用ask价格
        askMethod: {
            detected: 0,
            totalProfit: 0
        },
        // 差异
        falsePositives: 0,  // bid显示有但ask显示无
        missedOpportunities: 0  // bid显示无但ask显示有
    },
    priceGaps: [],  // ask - bid差价记录
    startTime: Date.now()
};

// 价格缓存（模拟两种方法）
const bidCache = new Map();  // 使用bid/成交价
const askCache = new Map();  // 使用ask价格

/**
 * 计算套利（简化版）
 */
function calculateArbitrage(yesPrice, noPrice) {
    const totalCost = yesPrice + noPrice;
    const netProfit = 1.0 - totalCost - 0.02;  // 2%费用
    return {
        profitable: netProfit > 0.005,  // 0.5%最低利润
        netProfit: netProfit
    };
}

/**
 * 处理消息
 */
function processMessage(message) {
    stats.messages.total++;

    const { topic, type, payload } = message;

    // 处理price_change消息
    if (topic === 'clob_market' && type === 'price_change') {
        stats.messages.priceChange++;

        if (payload.pc && Array.isArray(payload.pc)) {
            payload.pc.forEach(pc => {
                const tokenId = pc.a;
                const bestAsk = pc.ba ? parseFloat(pc.ba) : null;
                const bestBid = pc.bb ? parseFloat(pc.bb) : null;
                const lastPrice = pc.p ? parseFloat(pc.p) : null;

                if (bestAsk && bestBid) {
                    stats.prices.withAsk++;

                    // 记录价差
                    const gap = bestAsk - bestBid;
                    stats.priceGaps.push({
                        gap: gap,
                        gapPercent: (gap / bestBid * 100),
                        timestamp: Date.now()
                    });

                    // 更新两种缓存
                    askCache.set(tokenId, { price: bestAsk, market: payload.m });
                    bidCache.set(tokenId, { price: bestBid, market: payload.m });
                } else if (lastPrice) {
                    stats.prices.fallbackToLast++;
                    askCache.set(tokenId, { price: lastPrice, market: payload.m });
                    bidCache.set(tokenId, { price: lastPrice, market: payload.m });
                } else {
                    stats.prices.withoutAsk++;
                }
            });
        }
    }

    // 处理orderbook消息
    if (topic === 'clob_market' && type === 'agg_orderbook') {
        stats.messages.orderbook++;

        const tokenId = payload.asset_id;
        if (payload.asks && payload.asks[0]) {
            const askPrice = parseFloat(payload.asks[0].price);
            stats.prices.withAsk++;
            askCache.set(tokenId, { price: askPrice, market: payload.market });
        }
        if (payload.bids && payload.bids[0]) {
            const bidPrice = parseFloat(payload.bids[0].price);
            bidCache.set(tokenId, { price: bidPrice, market: payload.market });
        }
    }

    // 处理trades消息
    if (topic === 'activity' && type === 'trades') {
        stats.messages.trades++;

        const tokenId = payload.asset || payload.tokenId;
        const price = parseFloat(payload.price);
        const market = payload.conditionId;

        if (tokenId && price) {
            stats.prices.fallbackToLast++;
            askCache.set(tokenId, { price: price, market: market });
            bidCache.set(tokenId, { price: price, market: market });
        }
    }

    // 检测套利机会（简化检测）
    checkArbitrage();
}

/**
 * 检测套利机会
 */
function checkArbitrage() {
    // 获取市场列表
    const markets = new Set();
    askCache.forEach(entry => markets.add(entry.market));

    markets.forEach(market => {
        // 查找YES和NO token
        let yesAsk = null, noAsk = null;
        let yesBid = null, noBid = null;

        askCache.forEach((entry, tokenId) => {
            if (entry.market === market) {
                // 简化：假设包含'yes'的是YES token
                if (tokenId.toLowerCase().includes('yes')) {
                    yesAsk = entry.price;
                } else if (tokenId.toLowerCase().includes('no')) {
                    noAsk = entry.price;
                }
            }
        });

        bidCache.forEach((entry, tokenId) => {
            if (entry.market === market) {
                if (tokenId.toLowerCase().includes('yes')) {
                    yesBid = entry.price;
                } else if (tokenId.toLowerCase().includes('no')) {
                    noBid = entry.price;
                }
            }
        });

        // 如果有完整的YES/NO对，计算套利
        if (yesAsk && noAsk && yesBid && noBid) {
            const askResult = calculateArbitrage(yesAsk, noAsk);
            const bidResult = calculateArbitrage(yesBid, noBid);

            if (askResult.profitable) {
                stats.arbitrage.askMethod.detected++;
                stats.arbitrage.askMethod.totalProfit += askResult.netProfit;
            }

            if (bidResult.profitable) {
                stats.arbitrage.bidMethod.detected++;
                stats.arbitrage.bidMethod.totalProfit += bidResult.netProfit;
            }

            // 检测差异
            if (bidResult.profitable && !askResult.profitable) {
                stats.arbitrage.falsePositives++;
                console.log(`⚠️ 伪套利检测: 市场 ${market.substring(0, 16)}...`);
            } else if (!bidResult.profitable && askResult.profitable) {
                stats.arbitrage.missedOpportunities++;
                console.log(`📈 错失机会: 市场 ${market.substring(0, 16)}...`);
            }
        }
    });
}

/**
 * 输出统计报告
 */
function printReport() {
    const elapsed = (Date.now() - stats.startTime) / 1000;

    console.log("\n" + "=".repeat(70));
    console.log("Ask价格迁移监控报告");
    console.log("=".repeat(70));
    console.log(`运行时间: ${elapsed.toFixed(0)}秒\n`);

    console.log("📊 消息统计:");
    console.log(`  总消息数: ${stats.messages.total}`);
    console.log(`  - price_change: ${stats.messages.priceChange}`);
    console.log(`  - orderbook: ${stats.messages.orderbook}`);
    console.log(`  - trades: ${stats.messages.trades}`);

    console.log("\n💰 价格数据:");
    console.log(`  包含ask数据: ${stats.prices.withAsk}`);
    console.log(`  降级到成交价: ${stats.prices.fallbackToLast}`);
    console.log(`  无ask数据: ${stats.prices.withoutAsk}`);

    const askCoverage = stats.prices.withAsk / (stats.prices.withAsk + stats.prices.fallbackToLast + stats.prices.withoutAsk) * 100;
    console.log(`  Ask覆盖率: ${askCoverage.toFixed(2)}%`);

    if (stats.priceGaps.length > 0) {
        const avgGap = stats.priceGaps.reduce((sum, g) => sum + g.gapPercent, 0) / stats.priceGaps.length;
        const maxGap = Math.max(...stats.priceGaps.map(g => g.gapPercent));
        console.log(`\n📈 价差分析:`);
        console.log(`  平均bid-ask价差: ${avgGap.toFixed(3)}%`);
        console.log(`  最大价差: ${maxGap.toFixed(3)}%`);
    }

    console.log("\n🎯 套利检测对比:");
    console.log(`  Bid方法: ${stats.arbitrage.bidMethod.detected}个机会, 总利润 ${(stats.arbitrage.bidMethod.totalProfit * 100).toFixed(3)}%`);
    console.log(`  Ask方法: ${stats.arbitrage.askMethod.detected}个机会, 总利润 ${(stats.arbitrage.askMethod.totalProfit * 100).toFixed(3)}%`);
    console.log(`  伪套利（假阳性）: ${stats.arbitrage.falsePositives}个`);
    console.log(`  错失机会: ${stats.arbitrage.missedOpportunities}个`);

    const reductionRate = stats.arbitrage.bidMethod.detected > 0
        ? ((stats.arbitrage.bidMethod.detected - stats.arbitrage.askMethod.detected) / stats.arbitrage.bidMethod.detected * 100)
        : 0;
    console.log(`  机会减少率: ${reductionRate.toFixed(1)}%`);

    console.log("\n✅ 建议:");
    if (stats.arbitrage.falsePositives > 0) {
        console.log("  - 发现伪套利，建议切换到ask价格");
    }
    if (askCoverage < 80) {
        console.log("  - Ask数据覆盖率偏低，建议订阅clob_market.price_change");
    }
    if (stats.priceGaps.length > 0 && Math.max(...stats.priceGaps.map(g => g.gapPercent)) > 2) {
        console.log("  - 存在大价差市场，使用ask价格更准确");
    }
}

// 主函数
function main() {
    console.log("🚀 启动Ask价格迁移监控...");
    console.log(`监控时长: ${MONITOR_DURATION / 1000}秒`);
    console.log(`报告间隔: ${LOG_INTERVAL / 1000}秒\n`);

    const client = new RealTimeDataClient({
        onConnect: (client) => {
            console.log("✅ WebSocket连接成功\n");

            // 订阅所需的topics
            client.subscribe({
                subscriptions: [
                    { topic: "clob_market", type: "price_change" },
                    { topic: "clob_market", type: "agg_orderbook" },
                    { topic: "activity", type: "trades" }
                ]
            });
        },
        onMessage: (client, message) => {
            processMessage(message);
        },
        onStatusChange: (status) => {
            console.log(`🔌 连接状态: ${status}`);
        }
    });

    client.connect();

    // 定期输出报告
    const reportInterval = setInterval(printReport, LOG_INTERVAL);

    // 结束监控
    setTimeout(() => {
        clearInterval(reportInterval);
        printReport();  // 最终报告

        console.log("\n🏁 监控完成");
        client.disconnect();
        process.exit(0);
    }, MONITOR_DURATION);
}

// 启动
if (require.main === module) {
    main();
}