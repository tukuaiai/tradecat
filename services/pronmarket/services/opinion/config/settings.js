/**
 * Opinion Bot 配置文件
 */

const path = require('path');
const dotenvPath = process.env.DOTENV_CONFIG_PATH || path.join(__dirname, '../.env');
require('dotenv').config({ path: dotenvPath });

module.exports = {
    // ==================== Opinion API ====================
    opinion: {
        host: process.env.OPINION_HOST || 'https://proxy.opinion.trade:8443',
        apiKey: process.env.OPINION_API_KEY || '',
        chainId: Number(process.env.OPINION_CHAIN_ID || 56),
        rpcUrl: process.env.OPINION_RPC_URL || 'https://bsc-dataseed.binance.org',
        pollInterval: Number(process.env.OPINION_POLL_INTERVAL || 10000), // 10秒轮询
        marketsCacheTTL: Number(process.env.OPINION_MARKETS_CACHE_TTL || 300000) // 5分钟缓存
    },

    // ==================== Telegram Bot ====================
    telegram: {
        token: process.env.TELEGRAM_BOT_TOKEN || '',
        chatId: process.env.TELEGRAM_CHAT_ID || '',
        parseMode: 'Markdown',
        disableNotification: false
    },

    // ==================== 模块1：价格套利检测 ====================
    arbitrage: {
        enabled: true,
        minProfit: 0.003,              // 最低净利润 0.3%
        tradingFee: 0.002,             // 交易费 0.2%
        slippage: 0.005,               // 滑点 0.5%
        minDepth: 100,                 // 最小深度 $100
        maxPriceAge: 60000,            // 价格最大有效期 60秒
        maxPriceTimeDiff: 30000,       // YES/NO最大时间差 30秒
        cooldown: 60000,               // 冷却时间 60秒
        maxSignalsPerHour: 9999,
        messageVariant: 'final',
        cacheTTL: 3600000
    },

    // ==================== 模块2：订单簿失衡检测 ====================
    orderbook: {
        enabled: true,
        minImbalance: 1.1,             // 最低失衡比例 1.1x
        minDepth: 10,                  // 最小深度 $10
        depthLevels: 3,                // 计算前N档
        cooldown: 60000,               // 冷却时间 60秒
        maxSignalsPerHour: 9999,
        messageVariant: 'final',
        minPriceImpact: 1.0,
        historySize: 10,
        subscriptionChunkSize: 200,
        subscriptionDebounceMs: 100
    },

    // ==================== 模块3：扫尾盘信号 ====================
    closing: {
        enabled: true,
        timeWindowHours: Number(process.env.CLOSING_TIME_WINDOW_HOURS || 168),
        highConfidenceHours: Number(process.env.CLOSING_HIGH_CONFIDENCE_HOURS || 2),
        mediumConfidenceHours: Number(process.env.CLOSING_MEDIUM_CONFIDENCE_HOURS || 12),
        minVolume: 0,
        minLiquidity: 0,
        maxMarkets: Number(process.env.CLOSING_MAX_MARKETS || 9999),
        pageSize: Number(process.env.CLOSING_PAGE_SIZE || 10),
        refreshIntervalMs: Number(process.env.CLOSING_REFRESH_INTERVAL_MS || 300000),
        opinionApi: process.env.OPINION_HOST || 'https://proxy.opinion.trade:8443',
        fetchTimeoutMs: Number(process.env.CLOSING_FETCH_TIMEOUT_MS || 15000),
        emitEmpty: process.env.CLOSING_EMIT_EMPTY === 'true',
        messageVariant: process.env.CLOSING_MESSAGE_VARIANT || 'list',
        debug: process.env.DEBUG === 'true'
    },

    // ==================== 模块4：大额交易检测 ====================
    largeTrade: {
        enabled: true,
        minValue: Number(process.env.LARGE_TRADE_MIN_VALUE || 5000),
        cooldown: Number(process.env.LARGE_TRADE_COOLDOWN || 30000),
        thresholds: {
            1: 2000,
            2: 5000,
            3: 10000
        }
    },

    // ==================== 模块5：新市场检测 ====================
    newMarket: {
        enabled: true,
        scanIntervalMs: Number(process.env.NEW_MARKET_SCAN_INTERVAL || 60000),
        opinionApi: process.env.OPINION_HOST || 'https://proxy.opinion.trade:8443',
        limit: Number(process.env.NEW_MARKET_LIMIT || 500)
    },

    // ==================== 模块6：聪明钱跟踪 ====================
    smartMoney: {
        enabled: false,  // Opinion 暂不支持
        trackTopN: 100,
        scanIntervalMs: 120000,
        minPositionValue: 500,
        dataApi: process.env.OPINION_HOST || 'https://proxy.opinion.trade:8443',
        thresholds: { 1: 100, 2: 500, 3: 2000 }
    },

    // ==================== 日志配置 ====================
    logging: {
        level: process.env.LOG_LEVEL || 'info',
        enableColors: true,
        logToFile: false,
        logFile: 'logs/bot.log'
    },

    // ==================== 性能配置 ====================
    performance: {
        cleanupInterval: 3600000,
        maxCacheSize: 10000,
        statsInterval: 300000
    },

    // ==================== 调试选项 ====================
    debug: {
        enabled: process.env.DEBUG === 'true',
        logAllMessages: false,
        dryRun: false,
        testMode: false
    },

    // ==================== 翻译配置 ====================
    translation: {
        enabled: true,
        google: {
            projectId: process.env.GOOGLE_CLOUD_PROJECT,
            keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS,
            timeout: 20000,
            retryAttempts: 1,
            retryDelay: 500
        },
        sourceLang: 'en',
        targetLang: 'zh-CN',
        cache: {
            enabled: true,
            maxSize: 5000,
            persistToDisk: true,
            filePath: './data/translation-cache.json'
        },
        queue: {
            enabled: process.env.TRANSLATION_QUEUE_ENABLED === 'true',
            batchSize: 15,
            batchWaitTime: 500,
            maxConcurrent: 3,
            taskTimeout: 30000,
            maxQueueSize: 200
        },
        partialFlushMin: Number(process.env.TRANSLATION_PARTIAL_FLUSH_MIN || 2),
        partialFlushMs: Number(process.env.TRANSLATION_PARTIAL_FLUSH_MS || 3000),
        fallback: {
            onFailure: 'keep-original',
            maxFailures: 5,
            recoverAfter: 300000
        }
    }
};
