/**
 * 订单簿倾斜信号格式化器
 */

function buildMarketUrl(signal) {
    const slug = signal.eventSlug || signal.marketSlug;
    return slug ? `https://polymarket.com/event/${slug}` : null;
}

function formatAmount(value) {
    if (!Number.isFinite(value)) return 'N/A';
    if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
    return `$${value.toFixed(0)}`;
}

function getCurrentTime() {
    return new Date().toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function formatBookSkewSignal(signal) {
    const { direction, oldSkew, newSkew, skewChange, bidDepth, askDepth, marketName } = signal;
    const time = getCurrentTime();
    const link = buildMarketUrl(signal);

    const emoji = direction === 'bullish' ? '📈' : '📉';
    const trend = direction === 'bullish' ? '看涨' : '看跌';
    const changePercent = (skewChange * 100).toFixed(0);

    const codeLines = [
        `${emoji} 倾斜 ${trend}`,
        `比例 ${oldSkew.toFixed(2)} → ${newSkew.toFixed(2)} (${changePercent}%)`,
        `买盘 ${formatAmount(bidDepth)}`,
        `卖盘 ${formatAmount(askDepth)}`
    ];

    const codeBlock = ['```', ...codeLines, '```'].join('\n');

    const text = [
        `🏷️ ${marketName || '未知市场'}`,
        codeBlock,
        `⏱️ ${time} 📊 订单簿倾斜`
    ].join('\n');

    return {
        text,
        keyboard: link ? { inline_keyboard: [[{ text: '📊 查看市场', url: link }]] } : undefined,
        translationTargets: marketName ? [{ text: marketName, conditionId: signal.conditionId }] : []
    };
}

module.exports = { formatBookSkewSignal, buildMarketUrl, formatAmount, getCurrentTime };
