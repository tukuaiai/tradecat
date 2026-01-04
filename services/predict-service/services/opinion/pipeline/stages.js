/**
 * Pipeline 阶段函数 - 阶段0.5 抽象
 * 从 sendSignal 拆分出的独立函数，不改变行为
 */

const metrics = require('../utils/metrics');
const marketDataFetcher = require('../utils/marketData');
const { formatArbitrageSignal } = require('../signals/arbitrage/formatter');
const { formatOrderbookSignal } = require('../signals/orderbook/formatter');
const { formatClosingSignal } = require('../signals/closing');

/**
 * 补全信号元数据（slug、name）
 */
async function enrichSignalMeta(signal, moduleName, ctx) {
    if (moduleName === 'closing' || !signal.market || signal.marketSlug) {
        return signal;
    }

    const timer = metrics.startTimer('enrichMeta');

    // 策略1: 从共享缓存获取
    if (moduleName === 'orderbook' && ctx.tryGetSlugFromCache) {
        const cached = ctx.tryGetSlugFromCache(signal.market);
        if (cached) {
            if (typeof cached === 'string') {
                signal.marketSlug = cached;
            } else {
                signal.eventSlug = cached.eventSlug || signal.eventSlug || null;
                signal.marketSlug = cached.marketSlug || cached.eventSlug || signal.marketSlug || null;
                if (!signal.marketName && cached.title) {
                    signal.marketName = cached.title;
                }
            }
            metrics.increment('cache.hit');
        }
    }
    metrics.increment('cache.total');

    // 策略2: CLOB API
    const nameMissingOrId = !signal.marketName || signal.marketName === signal.market;
    const needSlug = !(signal.marketSlug || signal.eventSlug);
    const needName = nameMissingOrId;

    if (needSlug || needName) {
        const promises = [
            needSlug ? marketDataFetcher.getMarketSlug(signal.market) : Promise.resolve(signal.marketSlug),
            needName ? marketDataFetcher.getMarketName(signal.market) : Promise.resolve(signal.marketName)
        ];
        const [slug, name] = await Promise.all(promises);
        if (slug && needSlug) signal.marketSlug = slug;
        if (name && needName) signal.marketName = name;
    }

    metrics.endTimer(timer);
    return signal;
}

/**
 * 格式化信号为消息
 */
async function formatSignal(signal, moduleName, config, enrichClosingFn) {
    const timer = metrics.startTimer('format');

    let formatted;
    if (moduleName === 'arbitrage') {
        formatted = formatArbitrageSignal(signal, config.arbitrage?.messageVariant);
    } else if (moduleName === 'orderbook') {
        formatted = formatOrderbookSignal(signal, config.orderbook?.messageVariant);
    } else if (moduleName === 'closing') {
        if (enrichClosingFn) await enrichClosingFn(signal);
        formatted = formatClosingSignal(signal, config.closing?.messageVariant || 'list');
    } else {
        metrics.endTimer(timer);
        return null;
    }

    metrics.endTimer(timer);
    return formatted;
}

/**
 * 筛选符合条件的接收用户
 */
function filterRecipients(subscribedUsers, moduleName, signal, userManager) {
    const recipients = [];
    let skipped = 0;

    for (const chatId of subscribedUsers) {
        if (!userManager.isNotificationEnabled(chatId, moduleName)) {
            skipped++;
            continue;
        }
        const threshold = userManager.getThreshold(chatId, moduleName);
        if (!userManager.checkSignalThreshold(signal, moduleName, threshold)) {
            skipped++;
            continue;
        }
        recipients.push(chatId);
    }

    return { recipients, skipped };
}

/**
 * 发送消息到单个用户
 */
async function sendToUser(chatId, formatted, moduleName, ctx) {
    const { telegramBot, config, translationService, addTranslationTask, signal } = ctx;

    const sentMessage = await telegramBot.sendMessage(chatId, formatted.text, {
        parse_mode: config.telegram.parseMode,
        reply_markup: formatted.keyboard,
        disable_notification: config.telegram.disableNotification
    });

    // 异步翻译（不阻塞）
    if (translationService && addTranslationTask) {
        const messageState = {
            text: formatted.text,
            keyboard: formatted.keyboard,
            signalType: moduleName
        };
        scheduleTranslation(signal, formatted, moduleName, chatId, sentMessage.message_id, messageState, ctx);
    }

    return sentMessage;
}

/**
 * 调度翻译任务
 */
function scheduleTranslation(signal, formatted, moduleName, chatId, messageId, messageState, ctx) {
    const { addTranslationTask, createBatchInfo } = ctx;

    if (moduleName === 'closing' && Array.isArray(formatted.translationTargets) && formatted.translationTargets.length > 0) {
        const batchInfo = createBatchInfo?.(formatted.translationTargets);
        if (batchInfo) {
            messageState.translationBatchInfo = batchInfo;
            batchInfo.entries.forEach(({ original }) => {
                addTranslationTask(original, chatId, messageId, moduleName, messageState);
            });
        }
    } else if (signal.marketName) {
        addTranslationTask(signal.marketName, chatId, messageId, moduleName, messageState);
    } else if (Array.isArray(formatted.translationTargets)) {
        formatted.translationTargets
            .map(t => typeof t === 'string' ? t : t?.text)
            .filter(t => t?.trim())
            .forEach(t => addTranslationTask(t, chatId, messageId, moduleName, messageState));
    }
}

module.exports = {
    enrichSignalMeta,
    formatSignal,
    filterRecipients,
    sendToUser,
    scheduleTranslation
};
