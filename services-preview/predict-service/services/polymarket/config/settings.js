/**
 * Bot配置文件
 *
 * 包含所有模块的配置选项
 */

const path = require('path');
// 统一使用 tradecat/config/.env
const projectRoot = path.resolve(__dirname, '../../../../../');
const dotenvPath = path.join(projectRoot, 'config', '.env');
require('dotenv').config({ path: dotenvPath, override: true });

module.exports = {
    // ==================== Polymarket WebSocket ====================
    polymarket: {
        host: process.env.POLYMARKET_WS_HOST || 'wss://ws-live-data.polymarket.com',
        pingInterval: 5000,
        autoReconnect: true,
        maxReconnectAttempts: Number(process.env.POLYMARKET_WS_MAX_RECONNECT_ATTEMPTS || 0), // 0 = 无限重试
        reconnectDelayMs: Number(process.env.POLYMARKET_WS_RECONNECT_DELAY_MS || 1000),
        reconnectDelayMaxMs: Number(process.env.POLYMARKET_WS_RECONNECT_DELAY_MAX_MS || 30000),
        heartbeat: {
            warnAfterMs: Number(process.env.POLYMARKET_HEARTBEAT_WARN_AFTER_MS || 20000),
            logThrottleMs: Number(process.env.POLYMARKET_HEARTBEAT_LOG_THROTTLE_MS || 60000),
            reconnectAfterConsecutive: Number(process.env.POLYMARKET_HEARTBEAT_RECONNECT_COUNT || 12),
            reconnectDelayMs: Number(process.env.POLYMARKET_HEARTBEAT_RECONNECT_DELAY_MS || 5000)
        }
    },

    // ==================== Telegram Bot ====================
    telegram: {
        token: process.env.TELEGRAM_BOT_TOKEN || '',
        chatId: process.env.TELEGRAM_CHAT_ID || '',
        parseMode: 'Markdown',
        disableNotification: false,
        // 管理员 ID 列表（可使用 /csv 等管理命令）
        adminIds: (process.env.TELEGRAM_ADMIN_IDS || process.env.TELEGRAM_CHAT_ID || '').split(',').map(id => id.trim()).filter(Boolean)
    },

    // ==================== 模块1：价格套利检测 ====================
    arbitrage: {
        enabled: true,                  // 是否启用
        minProfit: 0.003,              // 最低净利润（0.3%）💼 生产模式
        tradingFee: 0.002,             // 交易费用（0.2%）Polymarket真实费率 - 双边扣
        slippage: 0.005,               // 滑点（0.5%）- 双边扣
        minDepth: 100,                 // 最小深度（$100）- YES/NO双边都需满足
        maxPriceAge: 60000,            // 价格最大有效期（60秒）
        maxPriceTimeDiff: 30000,       // YES/NO最大时间差（30秒）
        cooldown: 60000,                // 冷却时间（60秒）
        maxSignalsPerHour: 9999,       // 每小时最多信号数（不限制）
        messageVariant: 'final',       // 消息格式变体 (v1/v2/v4/v5/newA/newB/newC/newD/newE/final)

        // 高级选项
        cacheTTL: 3600000              // 价格缓存有效期（1小时）
    },

    // ==================== 模块2：订单簿失衡检测 ====================
    orderbook: {
        enabled: true,                  // 是否启用
        minImbalance: 1.1,             // 最低失衡比例（1.1倍）🧪 测试模式 - 最宽松
        minDepth: 10,                  // 最小深度（$10）
        depthLevels: 3,                // 计算前N档
        cooldown: 60000,                 // 冷却时间（60秒）
        maxSignalsPerHour: 9999,       // 每小时最多信号数（不限制）
        messageVariant: 'final',       // 消息格式变体 (v2/v3/v4/v5/v6/detailed/final)

        // 高级选项
        minPriceImpact: 1.0,           // 最小价格冲击（1%）
        historySize: 10,               // 保留历史记录数
        subscriptionChunkSize: 200,    // 每条订阅包含的token数量
        subscriptionDebounceMs: 100    // 订阅更新防抖间隔
    },

    // ==================== 模块3：扫尾盘信号 ====================
    closing: {
        enabled: true,                  // 是否启用
        timeWindowHours: Number(process.env.CLOSING_TIME_WINDOW_HOURS || 168),  // 7天内结束的市场
        highConfidenceHours: Number(process.env.CLOSING_HIGH_CONFIDENCE_HOURS || 2),
        mediumConfidenceHours: Number(process.env.CLOSING_MEDIUM_CONFIDENCE_HOURS || 12),
        minVolume: 0,                   // 不过滤成交量
        minLiquidity: 0,                // 不过滤流动性
        maxMarkets: Number(process.env.CLOSING_MAX_MARKETS || 9999),
        pageSize: Number(process.env.CLOSING_PAGE_SIZE || 10),
        refreshIntervalMs: Number(process.env.CLOSING_REFRESH_INTERVAL_MS || 300000), // 5分钟
        gammaApi: process.env.CLOSING_GAMMA_API || 'https://gamma-api.polymarket.com',
        fetchTimeoutMs: Number(process.env.CLOSING_FETCH_TIMEOUT_MS || 15000),
        emitEmpty: process.env.CLOSING_EMIT_EMPTY === 'true',
        messageVariant: process.env.CLOSING_MESSAGE_VARIANT || 'list',
        debug: process.env.DEBUG === 'true'
    },

    // ==================== 模块4：大额交易检测 ====================
    largeTrade: {
        enabled: true,                  // 是否启用
        minValue: Number(process.env.LARGE_TRADE_MIN_VALUE || 5000),  // 最低金额 $5000
        cooldown: Number(process.env.LARGE_TRADE_COOLDOWN || 30000),  // 冷却时间 30秒
        // 阈值档位对应的最低金额
        thresholds: {
            1: 2000,    // 宽松 $2K
            2: 5000,    // 中等 $5K
            3: 10000    // 严格 $10K
        }
    },

    // ==================== 模块5：新市场检测 ====================
    newMarket: {
        enabled: true,                  // 是否启用
        scanIntervalMs: Number(process.env.NEW_MARKET_SCAN_INTERVAL || 60000),  // 扫描间隔 1分钟
        gammaApi: process.env.NEW_MARKET_GAMMA_API || 'https://gamma-api.polymarket.com',
        limit: Number(process.env.NEW_MARKET_LIMIT || 500),  // 每次获取市场数
        // 无阈值档位，只有开关
    },

    // ==================== 模块6：聪明钱跟踪 ====================
    smartMoney: {
        enabled: true,                  // 是否启用
        trackTopN: Number(process.env.SMART_MONEY_TRACK_TOP_N || 100),  // 跟踪 Top 100
        scanIntervalMs: Number(process.env.SMART_MONEY_SCAN_INTERVAL || 120000),  // 扫描间隔 2分钟
        minPositionValue: Number(process.env.SMART_MONEY_MIN_POSITION || 500),  // 最低持仓 $500
        dataApi: process.env.SMART_MONEY_DATA_API || 'https://data-api.polymarket.com',
        // 阈值档位对应的最低持仓变化金额
        thresholds: {
            1: 100,     // 宽松 $100
            2: 500,     // 中等 $500
            3: 2000     // 严格 $2K
        }
    },

    // ==================== 模块7：价格趋势检测（未实现）====================
    priceTrend: {
        enabled: false
    },

    // ==================== 模块8：交易量激增检测（未实现）====================
    volumeSpike: {
        enabled: false
    },

    // ==================== 模块5：快速价格变动检测（未实现）====================
    priceSpike: {
        enabled: false
    },

    // ==================== 模块6：评论情绪分析（未实现）====================
    sentiment: {
        enabled: false
    },

    // ==================== 订阅配置 ====================
    subscriptions: {
        // 订阅价格变化（用于套利检测）
        priceChange: {
            topic: 'clob_market',
            type: 'price_change',
            filters: null  // null = 订阅所有市场
        },

        // 订阅订单簿更新（用于订单簿失衡检测）
        orderbook: {
            topic: 'clob_market',
            type: 'agg_orderbook',
            filters: null  // null = 订阅所有市场
        },

        // 订阅交易活动（可选，用于其他模块）
        trades: {
            topic: 'activity',
            type: 'trades',
            filters: null
        }
    },

    // ==================== 市场过滤（可选）====================
    markets: {
        // 如果指定，只监控这些市场
        whitelist: [],

        // 排除这些市场
        blacklist: [],

        // 只监控特定类别
        categories: []  // 例如: ['politics', 'crypto', 'sports']
    },

    // ==================== 日志配置 ====================
    logging: {
        level: process.env.LOG_LEVEL || 'info',  // debug, info, warn, error
        enableColors: true,
        logToFile: false,
        logFile: 'logs/bot.log'
    },

    // ==================== 性能配置 ====================
    performance: {
        cleanupInterval: 3600000,      // 清理过期数据间隔（1小时）
        maxCacheSize: 10000,           // 最大缓存条目数
        statsInterval: 300000          // 统计信息打印间隔（5分钟）
    },

    // ==================== 调试选项 ====================
    debug: {
        enabled: process.env.DEBUG === 'true',
        logAllMessages: false,         // 记录所有WebSocket消息
        dryRun: false,                 // 不发送Telegram消息（测试用）
        testMode: false                // 使用模拟数据
    },

    // ==================== Google 翻译配置 ====================
    translation: {
        enabled: true,                 // 是否启用翻译功能

        // Google Cloud Translation API 配置
        google: {
            projectId: process.env.GOOGLE_CLOUD_PROJECT,
            keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS,
            timeout: 20000,            // API超时（20秒，充足的网络时间）
            retryAttempts: 1,          // 重试次数（1次，快速失败）
            retryDelay: 500            // 重试延迟（500ms）
        },

        // 语言配置
        sourceLang: 'en',              // 源语言（英文）
        targetLang: 'zh-CN',           // 目标语言（简体中文）

        // 缓存配置（极限性能优化）
        cache: {
            enabled: true,
            maxSize: 5000,             // 最大缓存条目数（翻5倍，提高命中率）
            persistToDisk: true,       // 持久化到磁盘
            filePath: './data/translation-cache.json'
        },

        // 批量翻译队列配置（极限性能优化）
        queue: {
            enabled: process.env.TRANSLATION_QUEUE_ENABLED === 'true',      // 默认使用即时模式，设置为true启用批量队列
            batchSize: 15,             // 每批最多任务数
            batchWaitTime: 500,        // 等待收集任务的时间（500ms，减少频繁编辑）
            maxConcurrent: 3,          // 最大并发批次数
            taskTimeout: 30000,        // 任务超时（30秒，充足时间）
            maxQueueSize: 200          // 队列长度上限
        },

        // 批量翻译插入策略
        partialFlushMin: Number(process.env.TRANSLATION_PARTIAL_FLUSH_MIN || 2),    // 至少积累2条才尝试局部插入
        partialFlushMs: Number(process.env.TRANSLATION_PARTIAL_FLUSH_MS || 3000),   // 首次译文完成3秒后若仍未全量就先插入

        // 降级策略
        fallback: {
            onFailure: 'keep-original', // 失败时保留原文
            maxFailures: 5,             // 连续失败5次后禁用
            recoverAfter: 300000        // 5分钟后恢复尝试
        }
    }
};
