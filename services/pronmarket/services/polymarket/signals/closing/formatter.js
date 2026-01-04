/*
 * ############################################################
 * # 📘 文件说明：
 * # 本文件实现的功能：将扫尾盘扫描结果格式化为文本和键盘结构，便于 Telegram 或终端输出。
 *
 * # 📋 程序整体伪代码（中文）：
 * # 1. 初始化主要依赖与变量；
 * # 2. 加载输入数据或接收外部请求；
 * # 3. 执行主要逻辑步骤（如计算、处理、训练、渲染等）；
 * # 4. 输出或返回结果；
 * # 5. 异常处理与资源释放；
 *
 * # 🔄 程序流程图（逻辑流）：
 * # ┌──────────┐
 * # │  输入数据 │
 * # └─────┬────┘
 * #       ↓
 * # ┌────────────┐
 * # │  核心处理逻辑 │
 * # └─────┬──────┘
 * #       ↓
 * # ┌──────────┐
 * # │  输出结果 │
 * # └──────────┘
 *
 * # 📊 数据管道说明：
 * # 数据流向：信号对象 → 文本/键盘格式化 → 输出到 Telegram / 控制台
 *
 * # 🧩 文件结构：
 * # - 模块1：公共工具函数 功能；
 * # - 模块2：变体格式化策略 功能；
 * # - 模块3：主导出函数 功能；
 *
 * # 🕒 创建时间：2025-10-26 14:00:00
 * # 👤 作者/责任人：Codex Assistant
 * # 🔖 版本：v1.0.0
 * ############################################################
 */

const { t } = require('../../i18n');

const DISPLAY_COUNT_DEFAULT = 5;

function formatAmount(value) {
    if (!Number.isFinite(value)) {
        return 'N/A';
    }
    if (value >= 1_000_000) {
        return `$${(value / 1_000_000).toFixed(2)}M`;
    }
    if (value >= 1_000) {
        return `$${(value / 1_000).toFixed(1)}K`;
    }
    return `$${value.toFixed(0)}`;
}

function formatTimeRemaining(timeRemainingMs, lang = 'zh-CN') {
    const i18n = t(lang);
    
    if (!Number.isFinite(timeRemainingMs)) {
        return lang === 'en' ? 'Unknown' : '未知';
    }

    const totalSeconds = Math.max(1, Math.floor(timeRemainingMs / 1000));

    if (totalSeconds < 60) {
        return `${totalSeconds}${i18n.time.seconds}`;
    }

    const totalMinutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    if (totalMinutes < 60) {
        return seconds === 0
            ? `${totalMinutes}${i18n.time.minutes}`
            : `${totalMinutes}${i18n.time.minutes} ${seconds}${i18n.time.seconds}`;
    }

    const totalHours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;

    if (totalHours >= 24) {
        const days = Math.floor(totalHours / 24);
        const restHours = totalHours % 24;
        return minutes === 0
            ? `${days}${i18n.time.days} ${restHours}${i18n.time.hours}`
            : `${days}${i18n.time.days} ${restHours}${i18n.time.hours} ${minutes}${i18n.time.minutes}`;
    }

    if (minutes === 0) {
        return `${totalHours}${i18n.time.hours}`;
    }

    return `${totalHours}${i18n.time.hours} ${minutes}${i18n.time.minutes}`;
}

function formatBeijingTimestamp(date) {
    try {
        const formatter = new Intl.DateTimeFormat('zh-CN', {
            timeZone: 'Asia/Shanghai',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });

        const parts = formatter.formatToParts(date);
        const map = Object.fromEntries(parts.map(({ type, value }) => [type, value]));
        return `${map.year}-${map.month}-${map.day} ${map.hour}:${map.minute}`;
    } catch (error) {
        return date.toISOString();
    }
}

function truncate(text, length) {
    if (!text || text.length <= length) {
        return text;
    }
    return `${text.slice(0, length - 1)}…`;
}

function buildMarketUrl(market) {
    const eventSlug = market.eventSlug || null;
    const marketSlug = market.marketSlug || null;

    if (eventSlug) {
        if (marketSlug && marketSlug !== eventSlug) {
            return `https://polymarket.com/event/${eventSlug}?market=${marketSlug}`;
        }
        return `https://polymarket.com/event/${eventSlug}`;
    }

    if (marketSlug) {
        return `https://polymarket.com/event/${marketSlug}`;
    }

    return `https://polymarket.com/event/${market.conditionId || market.marketId}`;
}

function buildKeyboard(signal, options = {}) {
    const { page = 1, pageSize = DISPLAY_COUNT_DEFAULT, lang = 'zh-CN' } = options;
    const i18n = t(lang);
    
    const totalMarkets = signal.markets?.length || 0;
    const totalPages = Math.max(1, Math.ceil(totalMarkets / pageSize));
    const currentPage = Math.max(1, Math.min(page, totalPages));

    const topMarket = signal.markets?.[0];
    if (!topMarket) {
        return undefined;
    }

    const label = `🔗 ${truncate(topMarket.question, 24)}`;

    const keyboard = [[
        {
            text: label,
            url: buildMarketUrl(topMarket)
        }
    ]];

    // 添加分页按钮（仅当有多页时）
    if (totalPages > 1) {
        const paginationRow = [];

        // 上一页按钮
        if (currentPage > 1) {
            paginationRow.push({
                text: i18n.closing.prevPage,
                callback_data: `closing_page_${currentPage - 1}`
            });
        }

        // 下一页按钮
        if (currentPage < totalPages) {
            paginationRow.push({
                text: i18n.closing.nextPage,
                callback_data: `closing_page_${currentPage + 1}`
            });
        }

        // 只有当至少有一个分页按钮时才添加这一行
        if (paginationRow.length > 0) {
            keyboard.push(paginationRow);
        }
    }

    return {
        inline_keyboard: keyboard
    };
}


function confidenceIcon(confidence) {
    switch (confidence) {
        case 'HIGH':
            return '🟥';
        case 'MEDIUM':
            return '🟨';
        default:
            return '🟩';
    }
}

function formatPercentage(value) {
    if (!Number.isFinite(value)) {
        return '--';
    }
    return `${(value * 100).toFixed(1)}%`;
}

function formatRelativeCountdown(market, lang = 'zh-CN') {
    const i18n = t(lang);
    return `${formatTimeRemaining(market.timeRemainingMs, lang)}${i18n.closing.endsIn}`;
}

function formatMarketBlocks(signal, options = {}) {
    const page = options.page || 1;
    const pageSize = options.pageSize || options.displayCount || DISPLAY_COUNT_DEFAULT;
    const translationCache = options.translationCache || null;
    const lang = options.lang || 'zh-CN';
    const i18n = t(lang);
    const blocks = [];
    const translationTargets = [];

    // 计算分页范围
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const marketsToShow = signal.markets.slice(startIndex, endIndex);
    marketsToShow.forEach((market, index) => {
        const icon = confidenceIcon(market.confidence);
        const countdown = formatRelativeCountdown(market, lang);
        const yes = formatPercentage(market.yesPrice);
        const no = formatPercentage(market.noPrice);
        const volume = formatAmount(market.volume);
        const liquidity = formatAmount(market.liquidity);
        const originalTitle = (market.question || i18n.unknownMarket).trim();
        const link = buildMarketUrl(market);

        // 尝试从翻译缓存获取翻译（仅中文需要翻译）
        let displayTitle = originalTitle;
        if (lang === 'zh-CN' && translationCache) {
            const cachedTranslation = translationCache.get(originalTitle);
            if (cachedTranslation) {
                // 如果有缓存,显示双语格式: "中文翻译\n原文"
                displayTitle = `${cachedTranslation}\n${originalTitle}`;
            } else {
                // 如果没有缓存，添加到翻译目标
                translationTargets.push({
                    text: originalTitle,
                    conditionId: market.conditionId || market.marketId
                });
            }
        } else if (lang === 'zh-CN') {
            // 如果没有提供缓存，总是添加到翻译目标
            translationTargets.push({
                text: originalTitle,
                conditionId: market.conditionId || market.marketId
            });
        }

        const blockLines = [
            `${icon} ${countdown}`,
            `✅ ${yes} ❎ ${no}`,
            `💰 ${volume} 💧 ${liquidity}`
        ];

        // SDK 新增字段
        const extraParts = [];
        if (market.oneDayPriceChange && Number.isFinite(market.oneDayPriceChange)) {
            const change = (market.oneDayPriceChange * 100).toFixed(1);
            extraParts.push(`📈 ${market.oneDayPriceChange >= 0 ? '+' : ''}${change}%`);
        }
        if (market.volume24hr && Number.isFinite(market.volume24hr)) {
            extraParts.push(`24h ${formatAmount(market.volume24hr)}`);
        }
        if (extraParts.length > 0) {
            blockLines.push(extraParts.join(' | '));
        }

        // 标签
        if (market.tags && Array.isArray(market.tags) && market.tags.length > 0) {
            blockLines.push(`🏷️ ${market.tags.slice(0, 3).join(' · ')}`);
        }

        blockLines.push(displayTitle);

        const block = ['```', ...blockLines, '```', `[${i18n.closing.jumpToMarket}](${link})`].join('\n');
        blocks.push(block);
    });

    return { blocks, translationTargets };
}

function formatListVariant(signal, options = {}) {
    const lang = options.lang || 'zh-CN';
    const i18n = t(lang);
    
    const headerTime = formatBeijingTimestamp(signal.generatedAt);
    const header = `${i18n.closing.title} ${headerTime}`;
    const legendLines = ['✅=YES ❎=NO', `💰=${lang === 'en' ? 'Vol' : '成交量'} 💧=${lang === 'en' ? 'Liq' : '流动性'}`];

    if (!signal.markets.length) {
        return {
            text: `${header}\n${legendLines.join('\n')}\n\n${i18n.closing.noMarkets}`,
            keyboard: undefined,
            translationTargets: []
        };
    }

    const { blocks, translationTargets } = formatMarketBlocks(signal, options);
    const body = blocks.join('\n');

    // 添加分页信息到页脚
    const page = options.page || 1;
    const pageSize = options.pageSize || options.displayCount || DISPLAY_COUNT_DEFAULT;
    const totalMarkets = signal.markets.length;
    const totalPages = Math.ceil(totalMarkets / pageSize);
    const pageInfo = totalPages > 1 
        ? (lang === 'en' 
            ? `\n📄 Page ${page}/${totalPages} (${totalMarkets} markets)` 
            : `\n📄 第 ${page}/${totalPages} 页 (共 ${totalMarkets} 个市场)`)
        : '';

    const footer = `${header}\n${legendLines.join('\n')}${pageInfo}`;

    return {
        text: `${body}\n${footer}`,
        keyboard: buildKeyboard(signal, options),
        translationTargets
    };
}

function formatCompactVariant(signal, options = {}) {
    return formatListVariant(signal, options);
}

/**
 * 将扫尾盘信号格式化为文本。
 * @param {object} signal - 扫尾盘信号对象
 * @param {string} variant - 消息展示变体
 * @param {object} options - 其他格式化参数
 * @returns {{text:string, keyboard?:object}}
 */
function formatClosingSignal(signal, variant = 'list', options = {}) {
    if (!signal || typeof signal !== 'object') {
        return {
            text: '⏰ 扫尾盘信号暂不可用（未收到有效数据）。',
            keyboard: undefined
        };
    }

    const normalizedSignal = {
        ...signal,
        generatedAt: signal.generatedAt instanceof Date ? signal.generatedAt : new Date(signal.generatedAt || Date.now()),
        markets: Array.isArray(signal.markets) ? signal.markets : []
    };

    if (variant === 'compact') {
        return formatCompactVariant(normalizedSignal, options);
    }

    return formatListVariant(normalizedSignal, options);
}

module.exports = {
    formatClosingSignal
};
