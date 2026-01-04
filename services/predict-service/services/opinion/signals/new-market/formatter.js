/**
 * 新市场信号格式化器 (Opinion 版本)
 */

const { t } = require('../../i18n');

function buildMarketUrl(signal) {
    // Opinion 市场链接
    if (signal.marketId) {
        return `https://opinion.trade/market/${signal.marketId}`;
    }
    return null;
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
    
    const { marketTitle, volume, volume24h, status, statusEnum, subtype } = signal;

    const time = getCurrentTime();
    const link = buildMarketUrl(signal);

    // 子类型标题
    let title = i18n.newMarket?.title || '🆕 新市场';
    if (subtype === 'trending_new') title = i18n.newMarket?.trending || '🔥 热门新市场';

    // 构建代码块
    const codeLines = [];

    if (volume24h) codeLines.push(`24h成交 ${formatAmount(parseFloat(volume24h))}`);
    else if (volume) codeLines.push(`总成交 ${formatAmount(parseFloat(volume))}`);
    
    if (statusEnum) codeLines.push(`状态: ${statusEnum}`);

    const codeBlock = codeLines.length > 0 ? ['```', ...codeLines, '```'].join('\n') : '';

    const textLines = [
        `🏷️ ${marketTitle || '未知市场'}`
    ];

    if (codeBlock) textLines.push(codeBlock);
    textLines.push(`⏱️ ${time} ${title}`);

    const text = textLines.join('\n');

    return {
        text,
        keyboard: link ? { inline_keyboard: [[{ text: i18n.viewMarket || '查看市场', url: link }]] } : undefined,
        translationTargets: marketTitle ? [{ text: marketTitle, marketId: signal.marketId }] : []
    };
}

module.exports = { formatNewMarketSignal, buildMarketUrl, formatAmount, getCurrentTime };
