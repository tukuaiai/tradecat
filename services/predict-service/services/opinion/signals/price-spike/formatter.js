/**
 * 价格突变信号格式化器 (SDK 版本)
 */

const { t } = require('../../i18n');

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

function formatPriceSpikeSignal(signal, options = {}) {
    const lang = options.lang || 'zh-CN';
    const i18n = t(lang);
    
    const { direction, oldPrice, newPrice, change, marketName, volume24hr, liquidity, oneDayPriceChange } = signal;

    const emoji = direction === 'up' ? '📈' : '📉';
    const arrow = direction === 'up' ? '↑' : '↓';
    const changeStr = (change * 100).toFixed(1);
    const oldStr = (oldPrice * 100).toFixed(1);
    const newStr = (newPrice * 100).toFixed(1);
    const time = getCurrentTime();
    const link = buildMarketUrl(signal);

    // 构建代码块
    const codeLines = [
        `${arrow} ${oldStr}¢ → ${newStr}¢ (${direction === 'up' ? '+' : '-'}${changeStr}%)`
    ];

    // SDK 额外数据
    if (volume24hr) codeLines.push(`${i18n.priceSpike.volume24h} ${formatAmount(volume24hr)}`);
    if (liquidity) codeLines.push(`${lang === 'en' ? 'Liq' : '流动性'} ${formatAmount(liquidity)}`);
    if (oneDayPriceChange) {
        const dayChange = (oneDayPriceChange * 100).toFixed(1);
        codeLines.push(`${i18n.priceSpike.dayChange} ${oneDayPriceChange > 0 ? '+' : ''}${dayChange}%`);
    }

    const codeBlock = ['```', ...codeLines, '```'].join('\n');

    const text = [
        `🏷️ ${marketName || i18n.unknownMarket}`,
        codeBlock,
        `⏱️ ${time} ${emoji} ${i18n.priceSpike.title}`
    ].join('\n');

    return {
        text,
        keyboard: link ? { inline_keyboard: [[{ text: i18n.openMarket, url: link }]] } : undefined,
        translationTargets: marketName ? [{ text: marketName, conditionId: signal.conditionId }] : []
    };
}

module.exports = { formatPriceSpikeSignal, buildMarketUrl, formatAmount, getCurrentTime };
