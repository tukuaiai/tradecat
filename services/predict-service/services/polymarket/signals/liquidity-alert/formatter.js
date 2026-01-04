/**
 * 流动性枯竭信号格式化器
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

function formatLiquidityAlertSignal(signal) {
    const { oldDepth, newDepth, dropRatio, bidDepth, askDepth, marketName } = signal;
    const time = getCurrentTime();
    const link = buildMarketUrl(signal);
    const dropPercent = (dropRatio * 100).toFixed(0);

    const codeLines = [
        `🚨 深度下降 ${dropPercent}%`,
        `📉 ${formatAmount(oldDepth)} → ${formatAmount(newDepth)}`,
        `买盘 ${formatAmount(bidDepth)}`,
        `卖盘 ${formatAmount(askDepth)}`
    ];

    const codeBlock = ['```', ...codeLines, '```'].join('\n');

    const text = [
        `🏷️ ${marketName || '未知市场'}`,
        codeBlock,
        `⏱️ ${time} 🚨 流动性预警`
    ].join('\n');

    return {
        text,
        keyboard: link ? { inline_keyboard: [[{ text: '📊 查看市场', url: link }]] } : undefined,
        translationTargets: marketName ? [{ text: marketName, conditionId: signal.conditionId }] : []
    };
}

module.exports = { formatLiquidityAlertSignal, buildMarketUrl, formatAmount, getCurrentTime };
