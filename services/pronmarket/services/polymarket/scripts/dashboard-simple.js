#!/usr/bin/env node

/**
 * Polymarket 实时数据 - 简单美化版
 * 使用颜色和表格让数据更易读
 */

const { RealTimeDataClient } = require("./dist/client");
const chalk = require("chalk");
const Table = require("cli-table3");

// 统计数据
const stats = {
    trades: 0,
    comments: 0,
    priceUpdates: 0,
    marketEvents: 0,
    startTime: Date.now(),
};

// 最新价格缓存
const latestPrices = {};

console.clear();
console.log(chalk.blue.bold("═".repeat(80)));
console.log(chalk.green.bold("         🚀 Polymarket 实时数据看板 [简化版]"));
console.log(chalk.blue.bold("═".repeat(80)));
console.log(chalk.gray(`启动时间: ${new Date().toLocaleString("zh-CN")}`));
console.log(chalk.blue.bold("═".repeat(80)));
console.log("");

// 显示统计信息
function showStats() {
    const runtime = Math.floor((Date.now() - stats.startTime) / 1000);
    console.log(chalk.cyan(`\n📊 统计信息 (运行 ${runtime}秒):`));
    console.log(chalk.white(`  交易: ${chalk.yellow(stats.trades)}  评论: ${chalk.yellow(stats.comments)}  价格更新: ${chalk.yellow(stats.priceUpdates)}  市场事件: ${chalk.yellow(stats.marketEvents)}`));
}

// 格式化交易数据
function formatTrade(trade) {
    const table = new Table({
        chars: { 'mid': '', 'left-mid': '', 'mid-mid': '', 'right-mid': '' },
        style: { head: ['cyan'] }
    });

    const sideColor = trade.side === 'BUY' ? chalk.green : chalk.red;
    const sideIcon = trade.side === 'BUY' ? '📈' : '📉';

    table.push(
        [chalk.gray('时间'), new Date(trade.timestamp * 1000).toLocaleTimeString("zh-CN")],
        [chalk.gray('事件'), chalk.yellow(trade.title || trade.eventSlug)],
        [chalk.gray('市场'), chalk.cyan(trade.slug)],
        [chalk.gray('结果'), chalk.white(trade.outcome)],
        [chalk.gray('方向'), sideColor(`${sideIcon} ${trade.side}`)],
        [chalk.gray('价格'), chalk.yellow.bold(`$${trade.price}`)],
        [chalk.gray('数量'), chalk.white(trade.size)],
        [chalk.gray('用户'), chalk.magenta(trade.name || trade.pseudonym || '匿名')]
    );

    console.log(chalk.blue("─".repeat(80)));
    console.log(chalk.green.bold("💰 新交易"));
    console.log(table.toString());
    stats.trades++;
}

// 格式化评论数据
function formatComment(comment) {
    console.log(chalk.blue("─".repeat(80)));
    console.log(chalk.green.bold("💬 新评论"));
    console.log(chalk.gray("时间:"), new Date(comment.createdAt).toLocaleTimeString("zh-CN"));
    console.log(chalk.gray("用户:"), chalk.magenta(comment.userAddress.substring(0, 10) + "..."));
    console.log(chalk.gray("内容:"), chalk.white(comment.body));
    if (comment.parentCommentID) {
        console.log(chalk.gray("回复:"), chalk.cyan(comment.parentCommentID));
    }
    stats.comments++;
}

// 格式化价格数据
function formatPrice(data) {
    const symbol = data.symbol.toUpperCase();
    const price = parseFloat(data.value);
    const oldPrice = latestPrices[symbol] || price;
    const change = price - oldPrice;
    const changePercent = ((change / oldPrice) * 100).toFixed(2);

    latestPrices[symbol] = price;

    let changeColor = chalk.gray;
    let changeIcon = '━';
    if (change > 0) {
        changeColor = chalk.green;
        changeIcon = '▲';
    } else if (change < 0) {
        changeColor = chalk.red;
        changeIcon = '▼';
    }

    console.log(chalk.blue("─".repeat(80)));
    console.log(chalk.yellow.bold(`📈 ${symbol}`));
    console.log(chalk.gray("时间:"), new Date(data.timestamp).toLocaleTimeString("zh-CN"));
    console.log(chalk.gray("价格:"), chalk.yellow.bold(`$${price.toFixed(2)}`));
    if (change !== 0) {
        console.log(chalk.gray("变化:"), changeColor(`${changeIcon} $${Math.abs(change).toFixed(2)} (${changePercent}%)`));
    }
    stats.priceUpdates++;
}

// 格式化市场数据
function formatMarket(data, type) {
    console.log(chalk.blue("─".repeat(80)));
    console.log(chalk.green.bold(`📊 市场 ${type}`));
    console.log(chalk.gray("市场ID:"), chalk.cyan(data.market || data.m));
    console.log(chalk.gray("时间:"), new Date().toLocaleTimeString("zh-CN"));

    if (type === 'price_change' && data.pc) {
        const changes = data.pc.slice(0, 3); // 只显示前3个
        changes.forEach(change => {
            const side = change.s === 'BUY' ? chalk.green('买入') : chalk.red('卖出');
            console.log(chalk.gray(`  ${side} $${change.p} x ${change.si}`));
        });
    } else if (type === 'last_trade_price') {
        const side = data.side === 'BUY' ? chalk.green('📈 买入') : chalk.red('📉 卖出');
        console.log(chalk.gray("方向:"), side);
        console.log(chalk.gray("价格:"), chalk.yellow.bold(`$${data.price}`));
        console.log(chalk.gray("数量:"), chalk.white(data.size));
    } else if (type === 'market_created') {
        console.log(chalk.green.bold("🎉 新市场创建！"));
        console.log(chalk.gray("资产ID:"), chalk.cyan(data.asset_ids?.join(', ')));
        console.log(chalk.gray("最小订单:"), chalk.white(data.min_order_size));
        console.log(chalk.gray("价格跳动:"), chalk.white(data.tick_size));
    }

    stats.marketEvents++;
}

// 格式化反应
function formatReaction(reaction) {
    console.log(chalk.blue("─".repeat(80)));
    console.log(chalk.green.bold(`${reaction.icon} 新反应`));
    console.log(chalk.gray("类型:"), chalk.yellow(reaction.reactionType));
    console.log(chalk.gray("用户:"), chalk.magenta(reaction.userAddress.substring(0, 10) + "..."));
    stats.comments++;
}

// 消息处理
const onMessage = (_, message) => {
    const { topic, type, payload } = message;

    try {
        if (topic === "activity" && type === "trades") {
            formatTrade(payload);
        } else if (topic === "comments" && type === "comment_created") {
            formatComment(payload);
        } else if (topic === "comments" && type === "reaction_created") {
            formatReaction(payload);
        } else if (topic === "crypto_prices" && type === "update") {
            formatPrice(payload);
        } else if (topic === "clob_market") {
            formatMarket(payload, type);
        } else {
            // 其他消息简单显示
            console.log(chalk.blue("─".repeat(80)));
            console.log(chalk.white(`📨 ${topic}/${type}`));
            console.log(chalk.gray(JSON.stringify(payload, null, 2).substring(0, 200)));
        }

        // 每 10 条消息显示一次统计
        const totalMessages = stats.trades + stats.comments + stats.priceUpdates + stats.marketEvents;
        if (totalMessages > 0 && totalMessages % 10 === 0) {
            showStats();
        }
    } catch (error) {
        console.error(chalk.red("处理消息出错:"), error.message);
    }
};

const onConnect = (client) => {
    console.log(chalk.green.bold("✅ 成功连接到 Polymarket！\n"));
    console.log(chalk.cyan("📡 正在订阅数据流..."));

    // 订阅评论
    client.subscribe({
        subscriptions: [{ topic: "comments", type: "*" }],
    });
    console.log(chalk.gray("  ✓ 评论和反应"));

    // 订阅交易
    client.subscribe({
        subscriptions: [{ topic: "activity", type: "*" }],
    });
    console.log(chalk.gray("  ✓ 交易活动"));

    // 订阅 BTC 价格
    client.subscribe({
        subscriptions: [{
            topic: "crypto_prices",
            type: "*",
            filters: '{"symbol":"btcusdt"}',
        }],
    });
    console.log(chalk.gray("  ✓ BTC 价格"));

    // 订阅 ETH 价格
    client.subscribe({
        subscriptions: [{
            topic: "crypto_prices",
            type: "*",
            filters: '{"symbol":"ethusdt"}',
        }],
    });
    console.log(chalk.gray("  ✓ ETH 价格"));

    // 订阅市场数据
    client.subscribe({
        subscriptions: [{ topic: "clob_market", type: "*" }],
    });
    console.log(chalk.gray("  ✓ 市场数据"));

    console.log("");
    console.log(chalk.yellow("⏳ 等待实时数据..."));
    console.log(chalk.gray("💡 提示: 按 Ctrl+C 退出\n"));
    console.log(chalk.blue("═".repeat(80)));
};

const onError = (error) => {
    console.error(chalk.red("\n❌ 错误:"), error.message);
};

// 启动客户端
new RealTimeDataClient({
    onConnect,
    onMessage,
    onError,
    autoReconnect: true,
}).connect();

// 优雅退出
process.on('SIGINT', () => {
    console.log(chalk.yellow("\n\n⚠️  正在退出..."));
    showStats();
    console.log(chalk.blue("\n═".repeat(80)));
    console.log(chalk.green.bold("👋 再见！"));
    console.log(chalk.blue("═".repeat(80) + "\n"));
    process.exit(0);
});
