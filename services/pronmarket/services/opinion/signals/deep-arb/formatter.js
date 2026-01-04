/**
 * 深度套利信号格式化器
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

function formatDeepArbSignal(signal) {
    const { subtype, profit, depth, marketName } = signal;
    const time = getCurrentTime();
    const link = buildMarketUrl(signal);
    const profitPercent = (profit * 100).toFixed(2);

    const isLong = subtype === 'long';
    const emoji = isLong ? '📥' : '📤';
    const action = isLong ? '买入套利' : '卖出套利';

    const codeLines = [
        `${emoji} ${action}`,
        `💎 利润 ${profitPercent}%`,
        `📊 深度 ${formatAmount(depth)}`
    ];

    if (isLong) {
        codeLines.push(`买YES ${(signal.effectiveBuyYes * 100).toFixed(1)}¢`);
        codeLines.push(`买NO  ${(signal.effectiveBuyNo * 100).toFixed(1)}¢`);
        codeLines.push(`成本  ${(signal.cost * 100).toFixed(1)}¢`);
    } else {
        codeLines.push(`卖YES ${(signal.effectiveSellYes * 100).toFixed(1)}¢`);
        codeLines.push(`卖NO  ${(signal.effectiveSellNo * 100).toFixed(1)}¢`);
        codeLines.push(`收入  ${(signal.revenue * 100).toFixed(1)}¢`);
    }

    const codeBlock = ['```', ...codeLines, '```'].join('\n');

    const text = [
        `🏷️ ${marketName || '未知市场'}`,
        codeBlock,
        `⏱️ ${time} ⚡ 深度套利`
    ].join('\n');

    return {
        text,
        keyboard: link ? { inline_keyboard: [[{ text: '📊 立即交易', url: link }]] } : undefined,
        translationTargets: marketName ? [{ text: marketName, conditionId: signal.conditionId }] : []
    };
}

module.exports = { formatDeepArbSignal, buildMarketUrl, formatAmount, getCurrentTime };
