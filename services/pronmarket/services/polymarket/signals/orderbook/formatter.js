/**
 * Telegram消息格式化器 - 订单簿信号
 *
 * 功能：将订单簿失衡信号转换为Telegram消息格式
 */

const OrderbookAnalyzer = require('./analyzer');
const { t } = require('../../i18n');

/**
 * 构建市场URL（优先使用slug）
 */
function buildMarketUrl(signal) {
    const slug = signal.eventSlug || signal.marketSlug;
    return slug
        ? `https://polymarket.com/event/${slug}`
        : `https://polymarket.com/event/${signal.market}`;
}

/**
 * 格式化订单簿信号 - 变体2（进度条紧凑版）
 */
function formatOrderbookV2(signal) {
    const direction = signal.direction === 'BULLISH' ? '📈 看涨' : '📉 看跌';
    const { buyBar, sellBar } = OrderbookAnalyzer.generateDepthBars(
        signal.buyDepth,
        signal.sellDepth,
        20
    );

    const buyAmount = OrderbookAnalyzer.formatAmount(signal.buyDepth);
    const sellAmount = OrderbookAnalyzer.formatAmount(signal.sellDepth);

    const text = `
📚 *订单簿失衡*

${signal.marketName || signal.market.substring(0, 30)} | ${direction}

🔵 买方 ${buyAmount}
${buyBar}

🔴 卖方 ${sellAmount}
${sellBar}

⚖️ 失衡 *${signal.imbalance}倍*

💰 ${signal.currentPrice} → ${signal.expectedPrice} (*${signal.expectedChange > 0 ? '+' : ''}${signal.expectedChange}%*)

✅ ${signal.direction === 'BULLISH' ? '买入' : '观望'} | ⏱️ ${signal.timeWindow / 60}分 | ${'⭐'.repeat(signal.strength)}
    `.trim();

    const keyboard = {
        inline_keyboard: [
            [
                { text: '📊 打开市场', url: buildMarketUrl(signal) }
            ]
        ]
    };

    return { text, keyboard };
}

/**
 * 格式化订单簿信号 - 变体3（表格式 - 使用代码块）
 */
function formatOrderbookV3(signal) {
    const buyAmount = OrderbookAnalyzer.formatAmount(signal.buyDepth);
    const sellAmount = OrderbookAnalyzer.formatAmount(signal.sellDepth);

    const buyBarLength = Math.round((signal.buyDepth / Math.max(signal.buyDepth, signal.sellDepth)) * 16);
    const sellBarLength = Math.round((signal.sellDepth / Math.max(signal.buyDepth, signal.sellDepth)) * 16);
    const buyBar = '█'.repeat(buyBarLength);
    const sellBar = '█'.repeat(sellBarLength);

    const text = `
📚 *订单簿警报*

🏷️ ${signal.marketName || signal.market.substring(0, 30)}
\`\`\`
买方  ${buyAmount.padEnd(8)}  ${buyBar}
卖方  ${sellAmount.padEnd(8)}  ${sellBar}
比例  ${signal.imbalance}x  ← 极度失衡！
\`\`\`
📈 价格预测
${signal.currentPrice} → ${signal.expectedPrice} (*${signal.expectedChange > 0 ? '+' : ''}${signal.expectedChange}%*)

💡 ${signal.direction === 'BULLISH' ? '买入' : '观望'} | ⏱️ ${signal.timeWindow / 60}分 | ${'⭐'.repeat(signal.strength)}
    `.trim();

    const keyboard = {
        inline_keyboard: [
            [
                { text: '📊 打开市场', url: buildMarketUrl(signal) }
            ]
        ]
    };

    return { text, keyboard };
}

/**
 * 格式化订单簿信号 - 变体4（单列紧凑版）
 */
function formatOrderbookV4(signal) {
    const buyAmount = OrderbookAnalyzer.formatAmount(signal.buyDepth);
    const sellAmount = OrderbookAnalyzer.formatAmount(signal.sellDepth);

    const buyBarLength = Math.round((signal.buyDepth / Math.max(signal.buyDepth, signal.sellDepth)) * 16);
    const sellBarLength = Math.round((signal.sellDepth / Math.max(signal.buyDepth, signal.sellDepth)) * 16);
    const buyBar = '█'.repeat(buyBarLength);
    const sellBar = '█'.repeat(sellBarLength);

    const text = `
📚 订单簿失衡 | ${signal.marketName || signal.market.substring(0, 20)}

买方 ${buyAmount} ${buyBar}
卖方 ${sellAmount} ${sellBar}

失衡 *${signal.imbalance}x* ⚠️

预期 *${signal.expectedChange > 0 ? '+' : ''}${signal.expectedChange}%* ${signal.direction === 'BULLISH' ? '📈' : '📉'}

✅ ${signal.direction === 'BULLISH' ? '买入' : '观望'} | ⏱️ ${signal.timeWindow / 60}分 | ${'⭐'.repeat(signal.strength)}
    `.trim();

    const keyboard = {
        inline_keyboard: [
            [
                { text: '📊 打开市场', url: buildMarketUrl(signal) }
            ]
        ]
    };

    return { text, keyboard };
}

/**
 * 格式化订单簿信号 - 变体5（极简版）
 */
function formatOrderbookV5(signal) {
    const buyAmount = OrderbookAnalyzer.formatAmount(signal.buyDepth);
    const sellAmount = OrderbookAnalyzer.formatAmount(signal.sellDepth);

    const text = `
📚 订单簿 | ${signal.marketName || signal.market.substring(0, 20)}

买${buyAmount} vs 卖${sellAmount} = ${signal.imbalance}x

预期 *${signal.expectedChange > 0 ? '+' : ''}${signal.expectedChange}%* ${signal.direction === 'BULLISH' ? '📈' : '📉'}

✅ ${signal.direction === 'BULLISH' ? '买入' : '观望'} | ⏱️${signal.timeWindow / 60}分 | ${'⭐'.repeat(signal.strength)}
    `.trim();

    const keyboard = {
        inline_keyboard: [
            [
                { text: '📊 打开市场', url: buildMarketUrl(signal) }
            ]
        ]
    };

    return { text, keyboard };
}

/**
 * 格式化订单簿信号 - 变体6（仪表盘风格）
 */
function formatOrderbookV6(signal) {
    const buyAmount = OrderbookAnalyzer.formatAmount(signal.buyDepth);
    const sellAmount = OrderbookAnalyzer.formatAmount(signal.sellDepth);

    const totalDepth = signal.buyDepth + signal.sellDepth;
    const buyPercent = Math.round((signal.buyDepth / totalDepth) * 100);
    const sellPercent = Math.round((signal.sellDepth / totalDepth) * 100);

    const buyBarLength = Math.round(buyPercent / 100 * 16);
    const sellBarLength = Math.round(sellPercent / 100 * 16);
    const buyBar = '█'.repeat(buyBarLength);
    const sellBar = '█'.repeat(sellBarLength);

    const text = `
📚 *订单簿监控*

${signal.marketName || signal.market.substring(0, 30)}

┌──────────────────┐
│ 买方 ${buyAmount.padEnd(6)} ${buyPercent}%  │ ${buyBar}
│ 卖方 ${sellAmount.padEnd(6)} ${sellPercent}%  │ ${sellBar}
├──────────────────┤
│ 失衡 ${signal.imbalance}倍 ⚠️   │
└──────────────────┘

📈 预期 *${signal.expectedChange > 0 ? '+' : ''}${signal.expectedChange}%*

✅ ${signal.direction === 'BULLISH' ? '买入建议' : '观望'}
⏱️ ${signal.timeWindow / 60}分钟 | ${'⭐'.repeat(signal.strength)}
    `.trim();

    const keyboard = {
        inline_keyboard: [
            [
                { text: '📊 打开市场', url: buildMarketUrl(signal) }
            ]
        ]
    };

    return { text, keyboard };
}

/**
 * 格式化订单簿信号 - 详细版（用于用户示例）
 */
function formatOrderbookDetailed(signal) {
    const buyAmount = OrderbookAnalyzer.formatAmount(signal.buyDepth);
    const sellAmount = OrderbookAnalyzer.formatAmount(signal.sellDepth);

    const buyBarLength = Math.round((signal.buyDepth / Math.max(signal.buyDepth, signal.sellDepth)) * 16);
    const sellBarLength = Math.round((signal.sellDepth / Math.max(signal.buyDepth, signal.sellDepth)) * 16);
    const buyBar = '█'.repeat(buyBarLength);
    const sellBar = '█'.repeat(sellBarLength);

    const text = `
📚 *订单簿警报*

📊 ${signal.marketName || signal.market.substring(0, 30)}

订单簿对比：
\`\`\`
方向     深度      图示
────────────────────────
买方   ${buyAmount.padEnd(8)}   ${buyBar}
卖方   ${sellAmount.padEnd(8)}   ${sellBar}

                ↑
          失衡${signal.imbalance}倍！
\`\`\`
价格分析：

当前价格   ${signal.currentPrice}
目标价格   ${signal.expectedPrice}
涨幅预期   *${signal.expectedChange > 0 ? '+' : ''}${signal.expectedChange}%* ${signal.direction === 'BULLISH' ? '📈' : '📉'}

结论：
${signal.direction === 'BULLISH' ? '大量买盘堆积，供应不足\n价格即将上涨' : '大量卖盘堆积，需求不足\n价格可能下跌'}

💡 操作 ›› ${signal.direction === 'BULLISH' ? '买入' : '观望'}
⏱️ 时效 ›› ${signal.timeWindow / 60}分钟
⭐ 强度 ›› ${'★'.repeat(signal.strength)}${'☆'.repeat(5 - signal.strength)}
    `.trim();

    const keyboard = {
        inline_keyboard: [
            [
                { text: '📊 打开市场', url: buildMarketUrl(signal) }
            ]
        ]
    };

    return { text, keyboard };
}

/**
 * 获取当前时间 (HH:MM:SS)
 */
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('zh-CN', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * 生成整体对比进度条（高的用实线，低的用虚线）
 */
function generateComparisonBars(buyDepth, sellDepth, maxLength = 16) {
    const maxDepth = Math.max(buyDepth, sellDepth);
    const buyLength = Math.round((buyDepth / maxDepth) * maxLength);
    const sellLength = Math.round((sellDepth / maxDepth) * maxLength);

    if (buyDepth > sellDepth) {
        return {
            buyBar: '█'.repeat(buyLength),
            sellBar: '░'.repeat(sellLength)
        };
    } else {
        return {
            buyBar: '░'.repeat(buyLength),
            sellBar: '█'.repeat(sellLength)
        };
    }
}

/**
 * 生成单个档位的进度条
 */
function generateDepthBar(size, maxSize, maxLength = 10) {
    const length = Math.round((size / maxSize) * maxLength);
    return '█'.repeat(Math.max(1, length));
}

/**
 * 格式化金额
 */
function formatAmount(amount) {
    // 确保 amount 是数字
    const num = parseFloat(amount);

    if (num >= 1000000) {
        return `$${(num / 1000000).toFixed(1)}M`;
    } else if (num >= 1000) {
        return `$${(num / 1000).toFixed(0)}K`;
    } else {
        return `$${num.toFixed(0)}`;
    }
}

/**
 * 最终确定的格式 - 传统订单簿显示（价格从高到低）
 */
function formatOrderbookFinal(signal, options = {}) {
    const lang = options.lang || 'zh-CN';
    const i18n = t(lang);
    
    // 确保数值字段是数字类型
    const buyDepth = parseFloat(signal.buyDepth);
    const sellDepth = parseFloat(signal.sellDepth);

    const { buyBar, sellBar } = generateComparisonBars(buyDepth, sellDepth, 8);
    const buyAmount = formatAmount(buyDepth);
    const sellAmount = formatAmount(sellDepth);
    const time = getCurrentTime();

    // 构建订单簿深度信息
    let orderbookLines = '';

    // 检查是否有详细的订单簿数据
    if (signal.details && signal.details.bids && signal.details.asks) {
        const maxBidSize = Math.max(...signal.details.bids.map(b => parseFloat(b.size)));
        const maxAskSize = Math.max(...signal.details.asks.map(a => parseFloat(a.size)));
        const totalBids = signal.details.bids.reduce((sum, b) => sum + parseFloat(b.size), 0);
        const totalAsks = signal.details.asks.reduce((sum, a) => sum + parseFloat(a.size), 0);

        // 卖盘：价格从高到低
        const sortedAsks = [...signal.details.asks].sort((a, b) => b.price - a.price);
        // 买盘：价格从高到低
        const sortedBids = [...signal.details.bids].sort((a, b) => b.price - a.price);

        sortedAsks.forEach((ask) => {
            const size = parseFloat(ask.size);
            const bar = generateDepthBar(size, maxAskSize, 10);
            const percent = ((size / totalAsks) * 100).toFixed(0);
            const price = parseFloat(ask.price);
            const priceStr = `$${price.toFixed(3)}`;
            const sizeStr = formatAmount(size).padStart(5);
            orderbookLines += ` ${priceStr} × ${sizeStr} ${bar} ${percent}%\n`;
        });

        // 中间价
        const midPrice = parseFloat(signal.currentPrice);
        orderbookLines += `--- 🔃 ---\n`;

        sortedBids.forEach((bid) => {
            const size = parseFloat(bid.size);
            const bar = generateDepthBar(size, maxBidSize, 10);
            const percent = ((size / totalBids) * 100).toFixed(0);
            const price = parseFloat(bid.price);
            const priceStr = `$${price.toFixed(3)}`;
            const sizeStr = formatAmount(size).padStart(5);
            orderbookLines += ` ${priceStr} × ${sizeStr} ${bar} ${percent}%\n`;
        });
    }

    // 确保 imbalance 是数字
    const imbalance = parseFloat(signal.imbalance);

    const codeLines = lang === 'en' ? [
        `Buy   ${buyAmount.padEnd(8)} ${buyBar}`,
        `Sell  ${sellAmount.padEnd(8)} ${sellBar}`,
        `Imbal ${imbalance.toFixed(1)}x`
    ] : [
        `买方  ${buyAmount.padEnd(8)} ${buyBar}`,
        `卖方  ${sellAmount.padEnd(8)} ${sellBar}`,
        `失衡  ${imbalance.toFixed(1)}倍`
    ];

    if (orderbookLines) {
        codeLines.push(lang === 'en' ? '--- Orderbook ---' : '--- 订单簿深度 ---');
        codeLines.push(...orderbookLines.trim().split('\n'));
    }

    const codeBlock = ['```', ...codeLines, '```'].join('\n');

    const text = [
        `🏷️ ${signal.marketName || i18n.unknownMarket}`,
        codeBlock,
        `⏱️ ${time} ${i18n.orderbook.title}`
    ].join('\n');

    const keyboard = {
        inline_keyboard: [[{ text: i18n.openMarket, url: buildMarketUrl(signal) }]]
    };

    return { text, keyboard };
}

/**
 * 默认格式化函数（使用变体3 - 表格式）
 */
function formatOrderbookSignal(signal, variant = 'final', options = {}) {
    // 只有 final 变体支持多语言
    if (variant === 'final') {
        return formatOrderbookFinal(signal, options);
    }
    
    const formatters = {
        'v2': formatOrderbookV2,
        'v3': formatOrderbookV3,
        'v4': formatOrderbookV4,
        'v5': formatOrderbookV5,
        'v6': formatOrderbookV6,
        'detailed': formatOrderbookDetailed,
        'final': formatOrderbookFinal
    };

    const formatter = formatters[variant] || formatOrderbookFinal;
    return formatter(signal);
}

module.exports = {
    formatOrderbookSignal,
    formatOrderbookV2,
    formatOrderbookV3,
    formatOrderbookV4,
    formatOrderbookV5,
    formatOrderbookV6,
    formatOrderbookDetailed,
    formatOrderbookFinal,
    getCurrentTime,
    generateComparisonBars,
    generateDepthBar,
    formatAmount
};
