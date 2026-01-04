/**
 * 新市场信号格式化器 (SDK 版本)
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

function formatNewMarketSignal(signal, options = {}) {
    const lang = options.lang || 'zh-CN';
    const i18n = t(lang);
    
    const { marketName, volume, volume24hr, liquidity, outcomes, outcomePrices, tags, subtype } = signal;

    const time = getCurrentTime();
    const link = buildMarketUrl(signal);

    // 子类型标题
    let title = i18n.newMarket.title;
    if (subtype === 'trending_new') title = i18n.newMarket.trending;

    // 构建代码块
    const codeLines = [];

    // 价格信息
    if (outcomes && outcomePrices && outcomes.length >= 2) {
        const yesPrice = (outcomePrices[0] * 100).toFixed(0);
        const noPrice = (outcomePrices[1] * 100).toFixed(0);
        codeLines.push(`✅ ${yesPrice}% ❎ ${noPrice}%`);
    }

    // SDK 额外数据
    if (volume24hr) codeLines.push(`${i18n.newMarket.volume24h} ${formatAmount(volume24hr)}`);
    else if (volume) codeLines.push(`${i18n.newMarket.totalVolume} ${formatAmount(volume)}`);
    if (liquidity) codeLines.push(`${lang === 'en' ? 'Liq' : '流动性'} ${formatAmount(liquidity)}`);

    // 标签
    if (tags && tags.length > 0) {
        codeLines.push(`🏷️ ${tags.slice(0, 3).join(' · ')}`);
    }

    const codeBlock = codeLines.length > 0 ? ['```', ...codeLines, '```'].join('\n') : '';

    const textLines = [
        `🏷️ ${marketName || i18n.unknownMarket}`
    ];

    if (codeBlock) textLines.push(codeBlock);
    textLines.push(`⏱️ ${time} ${title}`);

    const text = textLines.join('\n');

    return {
        text,
        keyboard: link ? { inline_keyboard: [[{ text: i18n.viewMarket, url: link }]] } : undefined,
        translationTargets: marketName ? [{ text: marketName, conditionId: signal.conditionId }] : []
    };
}

module.exports = { formatNewMarketSignal, buildMarketUrl, formatAmount, getCurrentTime };
