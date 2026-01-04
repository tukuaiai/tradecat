/**
 * 聪明钱信号格式化器
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

function formatDaysToEnd(endDate) {
    if (!endDate) return null;
    const end = new Date(endDate);
    // 格式: 12-25 23:59
    const month = String(end.getMonth() + 1).padStart(2, '0');
    const day = String(end.getDate()).padStart(2, '0');
    const hour = String(end.getHours()).padStart(2, '0');
    const min = String(end.getMinutes()).padStart(2, '0');
    return `${month}-${day} ${hour}:${min}`;
}

function formatSmartMoneySignal(signal, options = {}) {
    const lang = options.lang || 'zh-CN';
    const i18n = t(lang);
    
    const { subtype, outcome, price, traderRank, marketName, value } = signal;

    const time = getCurrentTime();
    const link = buildMarketUrl(signal);
    const priceStr = ((price || 0) * 100).toFixed(2);

    // 子类型
    let emoji, action;
    switch (subtype) {
        case 'new_position':
            emoji = '🆕'; action = i18n.smartMoney.newPosition; break;
        case 'add_position':
            emoji = '➕'; action = i18n.smartMoney.addPosition; break;
        case 'reduce_position':
            emoji = '➖'; action = i18n.smartMoney.reducePosition; break;
        case 'close_position':
            emoji = '🚪'; action = i18n.smartMoney.closePosition; break;
        default:
            emoji = '🧠'; action = i18n.smartMoney.action;
    }

    // 构建代码块 - 按重要性排序
    const codeLines = [
        `${emoji} ${action} ${outcome || 'YES'} @ ${priceStr}¢`,
        `💰 ${i18n.smartMoney.value} ${formatAmount(value)}`,
        `🏆 ${i18n.smartMoney.rank} #${traderRank || '?'}`
    ];

    // 盈亏%
    if (signal.percentPnl !== undefined) {
        const pnlSign = signal.percentPnl >= 0 ? '+' : '';
        codeLines.push(`📈 ${i18n.smartMoney.pnl} ${pnlSign}${signal.percentPnl.toFixed(2)}%`);
    }

    // 持仓变化
    if (signal.previousSize && signal.currentSize) {
        const changePercent = ((signal.currentSize - signal.previousSize) / signal.previousSize * 100).toFixed(0);
        codeLines.push(`📦 ${i18n.smartMoney.position} ${signal.previousSize.toFixed(0)} → ${signal.currentSize.toFixed(0)} (+${changePercent}%)`);
    }

    // 成本价
    if (signal.avgPrice) {
        codeLines.push(`📊 ${i18n.smartMoney.cost} ${(signal.avgPrice * 100).toFixed(2)}¢`);
    }

    // 结算时间
    if (signal.endDate) {
        codeLines.push(`⏳ ${i18n.smartMoney.settle} ${formatDaysToEnd(signal.endDate)}`);
    }

    // 交易者地址（缩写）- 放最后
    if (signal.traderAddress) {
        const addr = signal.traderAddress;
        codeLines.push(`👤 ${i18n.smartMoney.address} ${addr.slice(0, 6)}...${addr.slice(-4)}`);
    }

    // 盈亏金额 (清仓时)
    if (signal.pnl) {
        const pnlStr = signal.pnl >= 0 ? `+${formatAmount(signal.pnl)}` : formatAmount(signal.pnl);
        codeLines.push(`💵 ${i18n.smartMoney.pnl} ${pnlStr}`);
    }

    const codeBlock = ['```', ...codeLines, '```'].join('\n');

    const text = [
        `🏷️ ${marketName || i18n.unknownMarket}`,
        codeBlock,
        `⏱️ ${time} ${i18n.smartMoney.title}${action}`
    ].join('\n');

    return {
        text,
        keyboard: link ? { inline_keyboard: [[{ text: i18n.openMarket, url: link }]] } : undefined,
        translationTargets: marketName ? [{ text: marketName, conditionId: signal.conditionId }] : []
    };
}

module.exports = { formatSmartMoneySignal, buildMarketUrl, formatAmount, getCurrentTime };
