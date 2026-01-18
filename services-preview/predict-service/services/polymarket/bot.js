/**
 * Polymarket信号检测Bot - 主程序
 *
 * 集成所有信号检测模块
 */

const path = require('path');
const projectRoot = path.resolve(__dirname, '../../../../../');
const dotenvPath = path.join(projectRoot, 'config', '.env');

// 全局代理注入 - 必须在最开头
require('dotenv').config({ path: dotenvPath, override: true });
if (process.env.HTTP_PROXY && !process.env.GLOBAL_AGENT_HTTP_PROXY) {
    process.env.GLOBAL_AGENT_HTTP_PROXY = process.env.HTTP_PROXY;
}
if (process.env.HTTPS_PROXY && !process.env.GLOBAL_AGENT_HTTPS_PROXY) {
    process.env.GLOBAL_AGENT_HTTPS_PROXY = process.env.HTTPS_PROXY;
}
const { bootstrap } = require('global-agent');
bootstrap();

// 加载配置
const config = require('./config/settings');

// 加载Polymarket客户端
const { RealTimeDataClient } = require('../../libs/external/real-time-data-client-main/dist/index');

// 加载Telegram Bot
const TelegramBot = require('node-telegram-bot-api');

// 加载信号检测模块
const ArbitrageDetector = require('./signals/arbitrage/detector');
const OrderbookDetector = require('./signals/orderbook/detector');
const { ClosingMarketScanner, formatClosingSignal } = require('./signals/closing');
const LargeTradeDetector = require('./signals/whale/detector');
const NewMarketDetector = require('./signals/new-market/detector');

// 加载消息格式化器
const { formatArbitrageSignal } = require('./signals/arbitrage/formatter');
const { formatOrderbookSignal } = require('./signals/orderbook/formatter');
const { formatLargeTradeSignal } = require('./signals/whale/formatter');
const { formatNewMarketSignal } = require('./signals/new-market/formatter');
const { formatSmartMoneySignal } = require('./signals/smart-money/formatter');

// 加载命令处理器
const CommandHandler = require('./commands/index');

// 加载市场数据获取器
const marketDataFetcher = require('./utils/marketData');

// 加载用户管理器
const UserManager = require('./utils/userManager');

// 加载代理配置
const { getTelegramBotOptions, testProxyConnection } = require('./utils/proxyAgent');

// 加载翻译服务
// ⚡ Google免费接口（推荐 - 速度快，内存占用小）
const GoogleTranslationService = require('./translation/google-service-free');
// 如需使用本地AI（需要2GB+内存），请改为：
// const GoogleTranslationService = require('./translation/local-ai-service');
// 如需使用官方API（需要Google Cloud配置），请改为：
// const GoogleTranslationService = require('./translation/google-service');
const TranslationBatchQueue = require('./translation/batch-queue');
const MessageUpdater = require('./translation/updater');

// 加载性能指标收集器
const metrics = require('./utils/metrics');

const ORDERBOOK_SUBSCRIPTION_CHUNK_SIZE = 200;
const ORDERBOOK_SUBSCRIPTION_DEBOUNCE_MS = 100;
const DEFAULT_TELEGRAM_MIN_DELAY_MS = 0;
const DEFAULT_TELEGRAM_RETRY_PADDING_MS = 500;
const DEFAULT_TELEGRAM_RATE_LIMIT_RETRIES = 1;
const DEFAULT_HEARTBEAT_LOG_THROTTLE_MS = 60000;

const delay = (ms = 0) => new Promise((resolve) => setTimeout(resolve, Math.max(0, ms)));

const ensurePositiveNumber = (value, fallback) => {
    const num = Number(value);
    return Number.isFinite(num) && num > 0 ? num : fallback;
};

const ensurePositiveInteger = (value, fallback) => {
    const num = Number(value);
    return Number.isFinite(num) && num >= 1 ? Math.floor(num) : fallback;
};

const ensureNonNegativeNumber = (value, fallback) => {
    const num = Number(value);
    return Number.isFinite(num) && num >= 0 ? num : fallback;
};

// ==================== 主类 ====================

class PolymarketSignalBot {
    constructor(config) {
        this.config = config;

        // 初始化统计
        this.stats = {
            startTime: Date.now(),
            messagesProcessed: 0,
            signalsSent: 0,
            errors: 0,
            byModule: {
                arbitrage: { detected: 0, sent: 0 },
                orderbook: { detected: 0, sent: 0 },
                closing: { detected: 0, sent: 0 }
            }
        };

        // 初始化用户管理器
        this.userManager = new UserManager();

        // 最近一次信号缓存
        this.lastSignals = {
            arbitrage: null,
            orderbook: null,
            closing: null
        };

        this.telegramRateLimiter = null;

        // 初始化Telegram Bot
        if (config.telegram.token) {
            // 获取代理配置
            const botOptions = getTelegramBotOptions();
            this.telegramBot = new TelegramBot(config.telegram.token, botOptions);
            console.log('✅ Telegram Bot 初始化完成');
            this.initializeTelegramRateLimiter();
        } else {
            console.warn('⚠️ Telegram Token缺失，将只打印信号到控制台');
            this.telegramBot = null;
        }

        // 初始化信号检测模块
        this.modules = {};

        if (config.arbitrage.enabled) {
            this.modules.arbitrage = new ArbitrageDetector({
                minProfit: config.arbitrage.minProfit,
                tradingFee: config.arbitrage.tradingFee,
                slippage: config.arbitrage.slippage,  // 新增
                minDepth: config.arbitrage.minDepth,  // 新增
                maxPriceAge: config.arbitrage.maxPriceAge,  // 新增
                maxPriceTimeDiff: config.arbitrage.maxPriceTimeDiff,  // 新增
                cooldown: config.arbitrage.cooldown,
                maxSignalsPerHour: config.arbitrage.maxSignalsPerHour,
                debug: Boolean(config.debug?.enabled || config.debug?.logAllMessages)
            });
            console.log('✅ 套利检测模块已启用');
        }

        if (config.orderbook.enabled) {
            this.modules.orderbook = new OrderbookDetector({
                minImbalance: config.orderbook.minImbalance,
                minDepth: config.orderbook.minDepth,
                depthLevels: config.orderbook.depthLevels,
                cooldown: config.orderbook.cooldown,
                maxSignalsPerHour: config.orderbook.maxSignalsPerHour,
                historySize: config.orderbook.historySize,
                minPriceImpact: config.orderbook.minPriceImpact  // 新增 - 修复#4
            });
            console.log('✅ 订单簿失衡检测模块已启用');
        }

        if (config.closing?.enabled) {
            this.modules.closing = new ClosingMarketScanner({
                gammaApi: config.closing.gammaApi,
                timeWindowHours: config.closing.timeWindowHours,
                highConfidenceHours: config.closing.highConfidenceHours,
                mediumConfidenceHours: config.closing.mediumConfidenceHours,
                minVolume: config.closing.minVolume,
                minLiquidity: config.closing.minLiquidity,
                maxMarkets: config.closing.maxMarkets,
                refreshIntervalMs: config.closing.refreshIntervalMs,
                fetchTimeoutMs: config.closing.fetchTimeoutMs,
                emitEmpty: config.closing.emitEmpty,
                debug: config.closing.debug
            });
            console.log('✅ 扫尾盘扫描模块已启用');
        }

        // 大额交易检测模块
        if (config.largeTrade?.enabled) {
            this.largeTradeDetector = new LargeTradeDetector({
                minValue: config.largeTrade.minValue,
                cooldown: config.largeTrade.cooldown,
                disableRateLimit: true
            });
            console.log('✅ 大额交易检测模块已启用');
        }

        const heartbeatOptions = config.polymarket?.heartbeat || {};
        const warnAfterFallback = Math.max(config.polymarket.pingInterval * 2, 20000);
        const logThrottleFallback = Math.max(config.polymarket.pingInterval * 6, DEFAULT_HEARTBEAT_LOG_THROTTLE_MS);
        const rawReconnectCount = Number(heartbeatOptions.reconnectAfterConsecutive);
        const reconnectAfterConsecutive = Number.isFinite(rawReconnectCount) && rawReconnectCount === 0
            ? 0
            : ensurePositiveInteger(heartbeatOptions.reconnectAfterConsecutive, 12);

        this.heartbeatConfig = {
            warnAfterMs: ensurePositiveNumber(heartbeatOptions.warnAfterMs, warnAfterFallback),
            logThrottleMs: ensurePositiveNumber(heartbeatOptions.logThrottleMs, logThrottleFallback),
            reconnectAfterConsecutive,
            reconnectDelayMs: ensurePositiveNumber(heartbeatOptions.reconnectDelayMs, 5000)
        };

        this.heartbeatState = {
            lastLogAt: 0,
            pendingReconnectTimer: null,
            restarting: false
        };

        // WebSocket客户端（稍后初始化）
        this.wsClient = null;

        // 初始化命令处理器
        if (this.telegramBot) {
            this.commandHandler = new CommandHandler(
                this.telegramBot,
                config,
                this.modules,
                this.userManager,
                {
                    sendLatestClosing: this.sendLatestClosingMessage.bind(this),
                    updateClosingPage: this.updateClosingMessagePage.bind(this)
                }
            );
            // 传递检测器引用
            this.commandHandler.setDetectors(this.modules);
            this.setupTelegramHandlers();

            // 确保 polling 已启动（防止代理或初始化异常导致未启动）
            if (typeof this.telegramBot.isPolling === 'function' && !this.telegramBot.isPolling()) {
                this.telegramBot.startPolling().catch((error) => {
                    console.error('❌ Telegram polling 启动失败:', error?.message || error);
                });
            }
            this.telegramBot.on('polling_error', (error) => {
                console.error('❌ Telegram polling 错误:', error?.message || error);
            });
        }

        // 初始化翻译服务
        this.translationService = null;
        this.translationQueue = null;
        this.messageUpdater = null;
        this.translationUpdateQueue = new Map();
        this.translationApplied = new Map();
        this.translationRetryTimers = new Map();
        const translationConfig = config.translation || {};
        const queueConfig = translationConfig.queue || {};
        const queueEnabled = queueConfig.enabled === true;
        const partialMs = ensureNonNegativeNumber(translationConfig.partialFlushMs, 3000);
        const rawPartialMin = Number(translationConfig.partialFlushMin);
        this.translationBatchPartialFlushMs = partialMs;
        this.translationBatchPartialFlushMin = Number.isFinite(rawPartialMin) && rawPartialMin > 0
            ? Math.floor(rawPartialMin)
            : 2;

        if (config.translation && config.translation.enabled && this.telegramBot) {
            try {
                // 初始化 Google 翻译服务
                this.translationService = new GoogleTranslationService({
                    ...config.translation.google,
                    sourceLang: config.translation.sourceLang,
                    targetLang: config.translation.targetLang,
                    cache: config.translation.cache,
                    maxFailures: config.translation.fallback.maxFailures,
                    recoverAfter: config.translation.fallback.recoverAfter
                });

                // 初始化批量翻译队列
                if (queueEnabled) {
                    this.translationQueue = new TranslationBatchQueue(
                        this.translationService,
                        queueConfig
                    );
                    console.log('✅ 翻译服务启用批量队列模式');
                } else {
                    console.log('ℹ️ 翻译服务启用即时模式（无队列）');
                }

                // 初始化消息更新器
                this.messageUpdater = new MessageUpdater(this.telegramBot);

                console.log('✅ Google 翻译服务已启用');
            } catch (error) {
                console.error('❌ 翻译服务初始化失败:', error.message);
                console.warn('⚠️ Bot将继续运行，但不会翻译消息');
                this.translationService = null;
                this.translationQueue = null;
                this.messageUpdater = null;
            }
        } else if (!config.translation || !config.translation.enabled) {
            console.log('ℹ️ 翻译服务未启用');
        }

        // 定时任务
        this.intervals = [];
        this.closingScanInterval = null;

        // 活跃市场追踪（用于订单簿订阅）
        this.activeTokens = new Set();
        this.orderbookSubscribed = false;
        this.lastOrderbookFilters = [];
        this.orderbookRefreshTimer = null;
        this.orderbookSubscriptionChunkSize = config.orderbook?.subscriptionChunkSize || ORDERBOOK_SUBSCRIPTION_CHUNK_SIZE;
        this.orderbookSubscriptionDebounceMs = config.orderbook?.subscriptionDebounceMs || ORDERBOOK_SUBSCRIPTION_DEBOUNCE_MS;

        // 共享 slug 缓存（从 activity.trades 提取，供所有模块使用）
        this.slugCache = new Map();  // market -> { eventSlug, marketSlug, title, timestamp }
        this.SLUG_CACHE_TTL = 30 * 60 * 1000;  // 30分钟
        this.SLUG_CACHE_MAX = 10000;

        if (process.env.DEBUG_SLUG_CACHE === 'true') {
            this.runSlugCacheSelfCheck();
        }
    }

    /**
     * 设置Telegram处理器
     */
    setupTelegramHandlers() {
        // 注册所有命令
        this.commandHandler.registerCommands();

        // 设置命令菜单
        this.telegramBot.setMyCommands([
            { command: 'start', description: '🏠 打开主面板' },
            { command: 'help', description: '❓ 查看帮助' },
            { command: 'closing', description: '📋 最新扫尾盘' }
        ]);

        // 处理Callback Query（内联按钮点击）
        this.telegramBot.on('callback_query', async (query) => {
            const action = query.data;
            const chatId = query.message.chat.id;
            const messageId = query.message.message_id;

            // 自动注册用户（同步操作）
            this.userManager.registerUser(chatId, query.from);

            // 立即回应callback（不阻塞）
            this.telegramBot.answerCallbackQuery(query.id).catch(() => {});

            try {
                const handled = await this.commandHandler.handlePanelAction(action, { chatId, messageId });
                if (handled) return;

                if (action === 'reset_stats') {
                    this.handleResetStats(chatId);
                    this.commandHandler.showMainPanel(chatId, { messageId, flashMessage: '🧹 统计已重置' }).catch(() => {});
                } else {
                    console.log(`⚠️ 未知的callback action: ${action}`);
                }
            } catch (error) {
                console.error('❌ 处理callback query失败:', error.message);
                this.telegramBot.sendMessage(chatId, '❌ 操作失败，请重试').catch(() => {});
            }
        });

        // 处理文本消息（兼容旧版自定义键盘）
        this.telegramBot.on('message', async (msg) => {
            if (msg.text?.startsWith('/')) return;

            const chatId = msg.chat.id;
            const text = msg.text;

            this.userManager.registerUser(chatId, msg.from);

            const panelInfo = this.commandHandler.mainPanels.get(chatId);
            const panelMessageId = panelInfo?.messageId;

            const forwardAction = (action) => {
                this.commandHandler.handlePanelAction(action, { chatId, messageId: null })
                    .then(handled => {
                        if (!handled) this.commandHandler.showMainPanel(chatId, { messageId: panelMessageId }).catch(() => {});
                    })
                    .catch(() => {});
            };

            switch (text) {
                case '📋 扫尾盘':
                case '📋 最新扫尾盘':
                case '📋 Closing':
                    forwardAction('show_closing_latest');
                    break;
                case '🎚️ 阈值':
                case '🎚️ Threshold':
                    forwardAction('menu_thresholds');
                    break;
                case '📢 通知开关':
                case '📢 通知':
                case '📢 Notif':
                    forwardAction('menu_notifications');
                    break;
                case '📊 统计':
                case '📊 统计数据':
                    this.commandHandler.showMainPanel(chatId, { flashMessage: '统计摘要已刷新。' }).catch(() => {});
                    break;
                case '⚙️ 设置':
                    this.commandHandler.showMainPanel(chatId, { flashMessage: '提示：下方按钮可直接调整通知与阈值。' }).catch(() => {});
                    break;
                case '📦 模块':
                    this.commandHandler.showMainPanel(chatId, { flashMessage: '提示：使用按钮切换各模块的启停状态。' }).catch(() => {});
                    break;
                case '❓ 帮助':
                case '❓ Help':
                    this.commandHandler.sendHelpMessage(chatId).catch(() => {});
                    break;
                case '🏠 主菜单':
                case '🏠 Menu':
                    this.commandHandler.showMainPanel(chatId, { forceNew: true, forceKeyboardRefresh: true }).catch(() => {});
                    break;
                case '🌐 中文':
                    this.userManager.setLang(chatId, 'zh-CN');
                    this.commandHandler.showMainPanel(chatId, { forceKeyboardRefresh: true }).catch(() => {});
                    break;
                case '🌐 EN':
                    this.userManager.setLang(chatId, 'en');
                    this.commandHandler.showMainPanel(chatId, { forceKeyboardRefresh: true }).catch(() => {});
                    break;
                case '⏸️ 暂停信号':
                    forwardAction('pause');
                    break;
                case '▶️ 开启信号':
                    forwardAction('resume');
                    break;
                case '🔄 刷新面板':
                case '🔄 刷新订阅状态':
                    forwardAction('refresh_main');
                    break;
            }
        });

        console.log('✅ Telegram处理器已设置（命令、按钮、回调）');
    }

    /**
     * 重置统计信息
     */
    async handleResetStats(chatId) {
        // 重置统计
        this.stats.messagesProcessed = 0;
        this.stats.signalsSent = 0;
        this.stats.errors = 0;
        this.stats.startTime = Date.now();
        this.stats.byModule.arbitrage = { detected: 0, sent: 0 };
        this.stats.byModule.orderbook = { detected: 0, sent: 0 };
        this.stats.byModule.closing = { detected: 0, sent: 0 };

        // 重置模块统计
        if (this.modules.arbitrage) {
            this.modules.arbitrage.stats = {
                detected: 0,
                sent: 0,
                skipped: 0,
                signalsThisHour: 0,
                lastHourReset: Date.now()
            };
        }

        if (this.modules.orderbook) {
            this.modules.orderbook.stats = {
                detected: 0,
                sent: 0,
                skipped: 0,
                signalsThisHour: 0,
                lastHourReset: Date.now()
            };
        }

        if (this.modules.closing) {
            this.modules.closing.stats = {
                scans: 0,
                emissions: 0,
                marketsLastSignal: 0,
                lastSignalAt: null
            };
        }

        return true;
    }

    /**
     * 并发执行任务（限制并发数）
     */
    async runWithConcurrency(items, limit, worker) {
        let idx = 0;
        const runners = Array(Math.min(limit, items.length)).fill(0).map(async () => {
            while (idx < items.length) {
                const current = items[idx++];
                await worker(current);
            }
        });
        await Promise.all(runners);
    }

    /**
     * 启动Bot
     */
    async start() {
        console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('🤖 Polymarket信号检测Bot 启动中...');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

        // 测试代理连接
        if (this.telegramBot) {
            console.log('🔍 测试网络和代理连接...');
            const proxyTest = await testProxyConnection();
            if (proxyTest.success) {
                console.log('✅ 网络连接正常,可以访问 Telegram API');
            } else {
                console.warn('⚠️  代理测试失败:', proxyTest.error || proxyTest.message);
                console.warn('⚠️  如果 Telegram 消息发送失败,请检查代理配置');
            }
        }

        // 打印配置信息
        this.printConfig();

        // 连接WebSocket
        await this.connectWebSocket();

        // 启动定时任务
        this.startScheduledTasks();

        console.log('\n✅ Bot 已启动！正在监听信号...\n');
    }

    /**
     * 连接WebSocket
     */
    async connectWebSocket() {
        console.log('🔌 连接到Polymarket WebSocket...');

        const heartbeatConfig = this.heartbeatConfig || {
            warnAfterMs: Math.max(this.config.polymarket.pingInterval * 2, 20000),
            logThrottleMs: Math.max(this.config.polymarket.pingInterval * 6, DEFAULT_HEARTBEAT_LOG_THROTTLE_MS),
            reconnectAfterConsecutive: 0,
            reconnectDelayMs: 5000
        };

        this.wsClient = new RealTimeDataClient({
            host: this.config.polymarket.host,
            pingInterval: this.config.polymarket.pingInterval,
            autoReconnect: this.config.polymarket.autoReconnect,
            maxReconnectAttempts: this.config.polymarket.maxReconnectAttempts > 0
                ? this.config.polymarket.maxReconnectAttempts
                : undefined,
            reconnectDelayMs: this.config.polymarket.reconnectDelayMs,
            reconnectDelayMaxMs: this.config.polymarket.reconnectDelayMaxMs,
            heartbeatWarningThresholdMs: heartbeatConfig.warnAfterMs,
            heartbeatWarningCooldownMs: heartbeatConfig.logThrottleMs,
            wsOptions: {
                agent: require('./utils/proxyAgent').createHttpProxyAgent()
            },

            onConnect: (client) => {
                console.log('✅ WebSocket 连接成功');
                this.onWebSocketConnect(client);
            },

            onMessage: (client, message) => {
                this.onWebSocketMessage(client, message);
            },

            onStatusChange: (status) => {
                console.log(`📡 WebSocket 状态: ${status}`);
            },

            onError: (error) => {
                const message = error instanceof Error
                    ? error.message
                    : (error && typeof error === 'object' && 'message' in error ? error.message : String(error));
                console.error('❌ WebSocket 错误:', message);
                this.stats.errors++;
            },

            onDisconnect: (event) => {
                const reason = event?.reason || '无';
                console.warn(`⚠️ WebSocket 断开: code=${event?.code}, reason=${reason}`);
            },

            onHeartbeatDelay: (_, info) => {
                this.handleHeartbeatDelay(info);
            },

            onHeartbeatRecover: () => {
                this.handleHeartbeatRecovery();
            }
        });

        this.wsClient.connect();
    }

    handleHeartbeatDelay(info = {}) {
        if (!info || typeof info.delayMs !== 'number') {
            return;
        }

        const { delayMs } = info;
        const rawConsecutive = Number(info.consecutive);
        const consecutive = Number.isFinite(rawConsecutive) && rawConsecutive > 0 ? rawConsecutive : 1;
        const now = Date.now();
        const shouldLog = consecutive === 1
            || now - this.heartbeatState.lastLogAt >= this.heartbeatConfig.logThrottleMs;

        if (shouldLog) {
            const seconds = delayMs / 1000;
            const formattedDelay = seconds >= 1
                ? `${seconds.toFixed(1)} 秒`
                : `${Math.round(delayMs)} 毫秒`;
            console.warn(`⚠️ WebSocket 心跳延迟 ${formattedDelay} (连续 ${consecutive} 次)`);
            this.heartbeatState.lastLogAt = now;
        }

        if (
            this.heartbeatConfig.reconnectAfterConsecutive > 0 &&
            consecutive >= this.heartbeatConfig.reconnectAfterConsecutive &&
            !this.heartbeatState.restarting &&
            !this.heartbeatState.pendingReconnectTimer
        ) {
            const delaySeconds = Math.ceil(this.heartbeatConfig.reconnectDelayMs / 1000);
            console.warn(`🔄 心跳连续异常 ${consecutive} 次，将在 ${delaySeconds} 秒后主动重连 WebSocket`);
            this.heartbeatState.pendingReconnectTimer = setTimeout(() => {
                this.heartbeatState.pendingReconnectTimer = null;
                this.restartWebSocketConnection('heartbeat-delay').catch((error) => {
                    console.error(`❌ 主动重连失败: ${error?.message || error}`);
                });
            }, this.heartbeatConfig.reconnectDelayMs);
        }
    }

    handleHeartbeatRecovery() {
        if (this.heartbeatState.pendingReconnectTimer) {
            clearTimeout(this.heartbeatState.pendingReconnectTimer);
            this.heartbeatState.pendingReconnectTimer = null;
        }

        if (this.heartbeatState.lastLogAt) {
            console.log('✅ WebSocket 心跳恢复正常');
        }

        this.heartbeatState.lastLogAt = 0;
    }

    async restartWebSocketConnection(reason = 'manual') {
        if (this.heartbeatState.restarting) {
            console.warn('ℹ️ WebSocket 重启请求已在处理，跳过重复操作');
            return;
        }

        this.heartbeatState.restarting = true;

        if (this.heartbeatState.pendingReconnectTimer) {
            clearTimeout(this.heartbeatState.pendingReconnectTimer);
            this.heartbeatState.pendingReconnectTimer = null;
        }

        console.warn(`🔁 正在重启 WebSocket 连接（原因: ${reason}）...`);

        try {
            if (this.wsClient) {
                try {
                    this.wsClient.disconnect();
                } catch (error) {
                    console.warn(`⚠️ 主动断开现有 WebSocket 失败: ${error?.message || error}`);
                }
                this.wsClient = null;
            }

            await delay(500);
            await this.connectWebSocket();
        } catch (error) {
            console.error(`❌ WebSocket 重启失败: ${error?.message || error}`);
        } finally {
            this.heartbeatState.restarting = false;
            this.heartbeatState.lastLogAt = 0;
        }
    }

    initializeTelegramRateLimiter() {
        if (!this.telegramBot || this.telegramRateLimiter) {
            return;
        }

        const rateConfig = this.config.telegram?.rateLimit || {};
        if (rateConfig.enabled !== true) {
            console.log('ℹ️ Telegram 限频队列已禁用');
            return;
        }
        const minIntervalMs = ensureNonNegativeNumber(rateConfig.minIntervalMs, DEFAULT_TELEGRAM_MIN_DELAY_MS);
        const retryPaddingMs = ensureNonNegativeNumber(rateConfig.retryAfterPaddingMs, DEFAULT_TELEGRAM_RETRY_PADDING_MS);
        const maxRetries = Math.max(0, Math.floor(ensureNonNegativeNumber(rateConfig.maxRetries, DEFAULT_TELEGRAM_RATE_LIMIT_RETRIES)));

        this.telegramRateLimiter = {
            queue: Promise.resolve(),
            lastSentAt: 0,
            cooldownUntil: 0,
            minIntervalMs,
            retryPaddingMs,
            maxRetries
        };

        const originalSendMessage = this.telegramBot.sendMessage.bind(this.telegramBot);
        const originalEditMessageText = this.telegramBot.editMessageText.bind(this.telegramBot);
        const originalEditMessageCaption = typeof this.telegramBot.editMessageCaption === 'function'
            ? this.telegramBot.editMessageCaption.bind(this.telegramBot)
            : null;

        this.telegramBot.sendMessage = (...args) =>
            this.enqueueTelegramCall(() => originalSendMessage(...args), {
                method: 'sendMessage',
                chatId: this.extractChatIdFromArgs('sendMessage', args)
                });

        this.telegramBot.editMessageText = (...args) =>
            this.enqueueTelegramCall(() => originalEditMessageText(...args), {
                method: 'editMessageText',
                chatId: this.extractChatIdFromArgs('editMessageText', args)
                });

        if (originalEditMessageCaption) {
            this.telegramBot.editMessageCaption = (...args) =>
                this.enqueueTelegramCall(() => originalEditMessageCaption(...args), {
                    method: 'editMessageCaption',
                    chatId: this.extractChatIdFromArgs('editMessageCaption', args)
                });
        }

        console.log(`✅ Telegram 限频队列已启用 (最小间隔 ${minIntervalMs}ms, 重试上限 ${maxRetries} 次)`);
    }

    enqueueTelegramCall(executor, meta = {}, attempt = 0) {
        if (typeof executor !== 'function') {
            throw new Error('enqueueTelegramCall 需要有效的执行函数');
        }

        if (!this.telegramRateLimiter) {
            return executor();
        }

        const limiter = this.telegramRateLimiter;

        const run = async (retryAttempt) => {
            const now = Date.now();
            const waitUntil = Math.max(limiter.cooldownUntil, limiter.lastSentAt + limiter.minIntervalMs);
            const waitMs = waitUntil > now ? waitUntil - now : 0;
            if (waitMs > 0) {
                await delay(waitMs);
            }

            try {
                const result = await executor();
                limiter.lastSentAt = Date.now();
                limiter.cooldownUntil = 0;
                return result;
            } catch (error) {
                const { isRateLimit, retryAfterMs } = this.parseTelegramRateLimit(error);
                if (isRateLimit && retryAttempt < limiter.maxRetries) {
                    const safeRetryAfter = Math.max(0, Number(retryAfterMs) || 0);
                    const totalDelay = safeRetryAfter + limiter.retryPaddingMs;
                    limiter.cooldownUntil = Date.now() + totalDelay;

                    const label = meta?.method || 'telegram call';
                    const suffix = meta?.chatId ? ` (chat=${meta.chatId})` : '';
                    const seconds = totalDelay / 1000;
                    const formattedDelay = seconds >= 1
                        ? `${seconds.toFixed(1)} 秒`
                        : `${Math.round(totalDelay)} 毫秒`;
                    console.warn(`⚠️ [TelegramRateLimit] ${label}${suffix} 限频，${formattedDelay}后重试 (#${retryAttempt + 1})`);

                    await delay(totalDelay);
                    return run(retryAttempt + 1);
                }

                throw error;
            }
        };

        const job = limiter.queue.then(() => run(attempt));
        limiter.queue = job.then(() => undefined, () => undefined);
        return job;
    }

    extractChatIdFromArgs(methodName, args) {
        if (!Array.isArray(args) || args.length === 0) {
            return undefined;
        }

        if (methodName === 'sendMessage') {
            return args[0];
        }

        if (methodName && methodName.startsWith('editMessage')) {
            const maybeOptions = args[args.length - 1];
            if (maybeOptions && typeof maybeOptions === 'object') {
                if (typeof maybeOptions.chat_id !== 'undefined') {
                    return maybeOptions.chat_id;
                }
                if (typeof maybeOptions.chatId !== 'undefined') {
                    return maybeOptions.chatId;
                }
            }
        }

        return undefined;
    }

    parseTelegramRateLimit(error) {
        if (!error) {
            return { isRateLimit: false, retryAfterMs: 0 };
        }

        const description = error?.response?.body?.description || error?.message || '';
        const statusCode = error?.response?.statusCode;
        const isTooManyRequests = error?.code === 'ETELEGRAM' && (
            statusCode === 429 || /Too Many Requests/i.test(description)
        );

        if (!isTooManyRequests) {
            return { isRateLimit: false, retryAfterMs: 0 };
        }

        const parameters = error?.response?.body?.parameters || error?.parameters || {};
        const retryAfterRaw = parameters.retry_after ?? parameters.retryAfter ?? error?.retryAfter;

        let retryAfterMs = 0;
        if (typeof retryAfterRaw === 'number' && Number.isFinite(retryAfterRaw)) {
            retryAfterMs = retryAfterRaw * 1000;
        } else if (typeof retryAfterRaw === 'string' && retryAfterRaw.trim()) {
            const parsed = Number(retryAfterRaw);
            if (!Number.isNaN(parsed) && Number.isFinite(parsed)) {
                retryAfterMs = parsed * 1000;
            }
        }

        return { isRateLimit: true, retryAfterMs };
    }

    /**
     * WebSocket连接成功回调
     *
     * 完全复用minimal-client的全量订阅
     * 接收所有数据，但只处理clob_market的price_change和agg_orderbook消息
     */
    onWebSocketConnect(client) {
        console.log('📡 建立基础订阅...');

        const subscriptions = [];

        if (this.modules.arbitrage) {
            subscriptions.push({ topic: 'activity', type: 'trades' });
        }

        if (subscriptions.length > 0) {
            client.subscribe({ subscriptions });
            const summary = subscriptions.map(sub => `${sub.topic}.${sub.type}`).join(', ');
            console.log(`✅ 基础订阅完成: ${summary}`);
        } else {
            console.log('ℹ️ 无需基础订阅（相关模块未启用）');
        }

        // 重新订阅订单簿过滤器
        this.orderbookSubscribed = false;
        if (this.modules.orderbook && this.activeTokens.size > 0) {
            this.subscribeOrderbook({ force: true });
        }
    }

    /**
     * WebSocket消息处理
     *
     * 显示所有消息（和minimal-client相同格式）
     * 但只处理activity主题的消息
     */
    onWebSocketMessage(client, message) {
        try {
            this.stats.messagesProcessed++;

            const topic = message?.topic;
            const type = message?.type;
            const payload = message?.payload || {};

            if (!topic || !type) {
                if (this.config.debug?.logAllMessages) {
                    console.debug('📥 控制帧', message);
                }
                return;
            }

            // ===== 打印所有消息（和minimal-client相同格式）=====
            this.printMessage(message);

            // ===== 处理activity.trades主题（套利检测从trades提取价格）=====
            if (topic === 'activity' && type === 'trades' && this.modules.arbitrage) {
                this.handlePriceChange(message);
            }

            // ===== 处理clob_market.price_change主题（包含ask/bid数据）=====
            if (topic === 'clob_market' && type === 'price_change' && this.modules.arbitrage) {
                this.handleClobPriceChange(message);
            }

            // ===== 处理clob_market.agg_orderbook主题 =====
            if (topic === 'clob_market' && type === 'agg_orderbook') {
                // 用于订单簿失衡检测
                if (this.modules.orderbook) {
                    this.handleOrderbookUpdate(message);
                }
                // 也用于套利检测（提取ask价格）
                if (this.modules.arbitrage) {
                    this.handleClobOrderbook(message);
                }
            }

            // 其他消息只打印不处理

        } catch (error) {
            console.error('❌ 处理消息失败:', error.message);
            this.stats.errors++;
        }
    }

    /**
     * 打印消息（完全复用minimal-client的格式和颜色）
     */
    printMessage(msg) {
        const { topic, type, payload } = msg;

        const shouldLog = this.config.debug?.logAllMessages
            || (topic === 'activity' && type === 'trades')
            || (topic === 'clob_market' && type === 'agg_orderbook');

        if (!shouldLog || !topic || !type) {
            return;
        }

        // 颜色定义（和minimal-client相同）
        const C = {
            reset: '\x1b[0m',
            dim: '\x1b[2m',
            red: '\x1b[31m',
            green: '\x1b[32m',
            yellow: '\x1b[33m',
            blue: '\x1b[34m',
            magenta: '\x1b[35m',
            cyan: '\x1b[36m',
            white: '\x1b[37m',
        };

        // 消息类型配置（和minimal-client相同）
        const types = {
            'comments': { c: C.yellow, i: '💬' },
            'activity': { c: C.green, i: '📊' },
            'crypto_prices': { c: C.magenta, i: '💰' },
            'crypto_prices_chainlink': { c: C.magenta, i: '🔗' },
            'clob_market': { c: C.cyan, i: '📈' },
            'clob_user': { c: C.blue, i: '👤' },
            'rfq': { c: C.white, i: '📝' },
        };

        // 消息计数（和minimal-client相同）
        const key = `${topic}:${type}`;
        if (!this.messageCount) this.messageCount = {};
        this.messageCount[key] = (this.messageCount[key] || 0) + 1;

        // 格式化时间
        const now = new Date();
        const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;

        // 提取摘要信息（和minimal-client相同）
        let summary = '';
        const safePayload = payload || {};

        switch(topic) {
            case 'comments':
                summary = `评论 ID:${safePayload?.id || 'N/A'}`;
                break;
            case 'activity':
                const act = safePayload?.action || '活动';
                const mkt = safePayload?.market_slug || safePayload?.market || 'N/A';
                summary = `${act} 市场:${mkt}`;
                break;
            case 'crypto_prices':
            case 'crypto_prices_chainlink':
                const sym = (safePayload?.symbol || 'N/A').toUpperCase();
                const price = safePayload?.price || 'N/A';
                const suffix = topic === 'crypto_prices_chainlink' ? ' (Chainlink)' : '';
                summary = `${sym} $${price}${suffix}`;
                break;
            case 'clob_market':
                const m = safePayload?.market || safePayload?.slug || safePayload?.id || 'N/A';
                summary = `${type || '更新'} 市场:${m}`;
                break;
            case 'clob_user':
                const ord = safePayload?.order_id || safePayload?.id || 'N/A';
                summary = `订单 ID:${ord}`;
                break;
            case 'rfq':
                const rfq = safePayload?.rfq_id || safePayload?.id || 'N/A';
                summary = `报价 ID:${rfq}`;
                break;
            default:
                summary = `${type || '消息'}`;
        }

        // 获取配置（和minimal-client相同）
        const cfg = types[topic] || { c: C.blue, i: '📡' };

        // 计数器显示（和minimal-client相同）
        const counter = this.messageCount[key] > 1 ? ` ${C.dim}#${this.messageCount[key]}${C.reset}` : '';

        // 打印（和minimal-client完全相同的格式）
        console.log(`${C.dim}${time}${C.reset} ${cfg.c}[${topic}]${C.reset} ${cfg.i} ${summary}${counter}`);
    }

    /**
     * 处理价格变化消息
     */
    handlePriceChange(message) {
        if (!this.modules.arbitrage) return;

        // 检查套利模块是否全局启用
        if (!this.config.arbitrage.enabled) return;

        // 从 activity.trades 提取 slug 到共享缓存
        const payload = message?.payload;
        if (payload) {
            const marketKeys = new Set([
                payload.conditionId,
                payload.condition_id,
                payload.market
            ].filter(Boolean));
            const marketSlug = payload.slug || payload.marketSlug || payload.market_slug || null;
            const eventSlug = payload.eventSlug || payload.event_slug || null;
            const title = payload.title || payload.question || null;
            if (marketKeys.size > 0 && (eventSlug || marketSlug)) {
                this.cacheSlug(Array.from(marketKeys), {
                    eventSlug: eventSlug || marketSlug,
                    marketSlug,
                    title
                });
            }
        }

        // 收集活跃市场的token ID（用于订单簿订阅）
        const tokenId = this.extractTokenId(payload);
        if (tokenId && this.modules.orderbook) {
            const sizeBefore = this.activeTokens.size;
            this.activeTokens.add(tokenId);

            // 当收集到新token时，更新订单簿订阅
            if (this.activeTokens.size > sizeBefore) {
                this.scheduleOrderbookRefresh();
            }
        }

        const signal = this.modules.arbitrage.processPrice(message);

        if (signal) {
            this.stats.byModule.arbitrage.detected++;
            this.sendSignal('arbitrage', signal);
        }

        // 大额交易检测
        if (this.config.largeTrade?.enabled && this.largeTradeDetector) {
            const tradeSignal = this.largeTradeDetector.process({
                assetId: payload?.asset_id || payload?.asset,
                price: parseFloat(payload?.price || 0),
                side: payload?.side,
                size: parseFloat(payload?.size || 0),
                timestamp: Date.now()
            }, {
                conditionId: payload?.conditionId || payload?.condition_id || payload?.market,
                slug: payload?.slug || payload?.marketSlug || payload?.market_slug,
                eventSlug: payload?.eventSlug || payload?.event_slug,
                question: payload?.title || payload?.question
            });

            if (tradeSignal) {
                this.stats.byModule.largeTrade = this.stats.byModule.largeTrade || { detected: 0, sent: 0 };
                this.stats.byModule.largeTrade.detected++;
                this.sendSignal('largeTrade', tradeSignal);
            }
        }
    }

    /**
     * 缓存 slug（供所有模块使用）
     */
    cacheSlug(markets, data) {
        if (!data || (!data.eventSlug && !data.marketSlug)) return;
        const keys = Array.isArray(markets) ? markets : [markets];
        const timestamp = Date.now();
        const entry = {
            eventSlug: data.eventSlug || data.marketSlug,
            marketSlug: data.marketSlug || null,
            title: data.title || null,
            timestamp
        };

        for (const market of keys) {
            if (!market) continue;
            // 容量限制（严格 LRU：先删旧键再插入）
            if (this.slugCache.has(market)) {
                this.slugCache.delete(market);
            }
            while (this.slugCache.size >= this.SLUG_CACHE_MAX) {
                const oldest = this.slugCache.keys().next().value;
                if (!oldest) break;
                this.slugCache.delete(oldest);
            }
            this.slugCache.set(market, entry);
        }
    }

    /**
     * 从共享缓存获取 slug
     */
    getSlugFromCache(market) {
        const cached = this.slugCache.get(market);
        if (!cached) return null;
        if (Date.now() - cached.timestamp > this.SLUG_CACHE_TTL) {
            this.slugCache.delete(market);
            return null;
        }
        // 触发“最近访问”更新（严格 LRU）
        this.slugCache.delete(market);
        this.slugCache.set(market, cached);
        return cached;
    }

    /**
     * slug 缓存自检（仅 DEBUG_SLUG_CACHE=true 时运行）
     */
    runSlugCacheSelfCheck() {
        try {
            const backupCache = this.slugCache;
            const backupMax = this.SLUG_CACHE_MAX;
            const backupTtl = this.SLUG_CACHE_TTL;

            this.slugCache = new Map();
            this.SLUG_CACHE_MAX = 2;
            this.SLUG_CACHE_TTL = 1000;

            this.cacheSlug('A', { eventSlug: 'event-a', marketSlug: 'market-a', title: 'A' });
            this.cacheSlug('B', { eventSlug: 'event-b', marketSlug: 'market-b', title: 'B' });
            this.getSlugFromCache('A'); // 访问A，使其变为最近使用
            this.cacheSlug('C', { eventSlug: 'event-c', marketSlug: 'market-c', title: 'C' });

            const hasA = this.slugCache.has('A');
            const hasB = this.slugCache.has('B');
            const hasC = this.slugCache.has('C');

            if (!hasA || hasB || !hasC) {
                console.warn('⚠️ [SlugCache] LRU 自检失败：期待淘汰 B，保留 A/C');
            } else {
                console.log('✅ [SlugCache] LRU 自检通过');
            }
            this.slugCache.clear();

            this.slugCache = backupCache;
            this.SLUG_CACHE_MAX = backupMax;
            this.SLUG_CACHE_TTL = backupTtl;
        } catch (error) {
            console.warn('⚠️ [SlugCache] 自检失败:', error.message);
        }
    }

    /**
     * 处理clob_market.price_change消息（包含ask/bid数据）
     */
    handleClobPriceChange(message) {
        if (!this.modules.arbitrage) return;

        // 检查套利模块是否全局启用
        if (!this.config.arbitrage.enabled) return;

        // 使用新的processPriceChange方法处理包含ask数据的消息
        const signal = this.modules.arbitrage.processPriceChange(message);

        if (signal) {
            this.stats.byModule.arbitrage.detected++;
            this.sendSignal('arbitrage', signal);
        }
    }

    /**
     * 处理clob_market.agg_orderbook消息（用于套利检测）
     */
    handleClobOrderbook(message) {
        if (!this.modules.arbitrage) return;

        // 检查套利模块是否全局启用
        if (!this.config.arbitrage.enabled) return;

        // 收集活跃市场的token ID（用于订单簿订阅）
        const tokenId = message?.payload?.asset_id;
        if (tokenId && this.modules.orderbook) {
            const sizeBefore = this.activeTokens.size;
            this.activeTokens.add(tokenId);

            // 当收集到新token时，更新订单簿订阅
            if (this.activeTokens.size > sizeBefore) {
                this.scheduleOrderbookRefresh();
            }
        }

        // 使用新的processOrderbook方法处理订单簿消息
        const signal = this.modules.arbitrage.processOrderbook(message);

        if (signal) {
            this.stats.byModule.arbitrage.detected++;
            this.sendSignal('arbitrage', signal);
        }
    }

    /**
     * 提取订单簿订阅所需的 tokenId
     */
    extractTokenId(payload) {
        if (!payload) {
            return null;
        }

        const candidates = [
            payload.asset,
            payload.token_id,
            payload.tokenId,
            payload?.token?.id,
            payload?.token?.token_id
        ];

        const candidate = candidates.find((value) => {
            if (typeof value === 'string') {
                return value.trim().length > 0;
            }
            return typeof value === 'number';
        });

        if (typeof candidate === 'number') {
            return String(candidate);
        }

        return typeof candidate === 'string' ? candidate.trim() : null;
    }

    /**
     * 防抖刷新订单簿订阅
     */
    scheduleOrderbookRefresh(options = {}) {
        const { force = false } = options;

        if (force) {
            this.subscribeOrderbook({ force: true });
            return;
        }

        if (this.orderbookRefreshTimer) {
            clearTimeout(this.orderbookRefreshTimer);
        }

        this.orderbookRefreshTimer = setTimeout(() => {
            this.orderbookRefreshTimer = null;
            this.subscribeOrderbook();
        }, this.orderbookSubscriptionDebounceMs);
    }

    /**
     * 订阅订单簿数据
     */
    subscribeOrderbook(options = {}) {
        if (!this.wsClient || !this.modules.orderbook) {
            return;
        }

        const { force = false } = options;
        const tokenIds = Array.from(this.activeTokens).filter(Boolean);

        if (tokenIds.length === 0) {
            if (this.orderbookSubscribed && this.lastOrderbookFilters.length > 0) {
                this.lastOrderbookFilters.forEach((filters) => {
                    try {
                        this.wsClient.unsubscribe({
                            subscriptions: [{
                                topic: "clob_market",
                                type: "agg_orderbook",
                                filters
                            }]
                        });
                    } catch (error) {
                        console.warn('⚠️ 订单簿退订失败:', error.message);
                    }
                });
            }

            this.lastOrderbookFilters = [];
            this.orderbookSubscribed = false;
            return;
        }

        const normalizedIds = Array.from(new Set(tokenIds)).sort();
        const chunkSize = Math.max(1, this.orderbookSubscriptionChunkSize);
        const newFilters = [];

        for (let i = 0; i < normalizedIds.length; i += chunkSize) {
            newFilters.push(normalizedIds.slice(i, i + chunkSize));
        }

        const isSameGroup = (a, b) => Array.isArray(a)
            && Array.isArray(b)
            && a.length === b.length
            && a.every((v, idx) => v === b[idx]);

        const filtersUnchanged = !force
            && this.lastOrderbookFilters.length === newFilters.length
            && this.lastOrderbookFilters.every((value, index) => isSameGroup(value, newFilters[index]));

        if (filtersUnchanged) {
            return;
        }

        if (this.lastOrderbookFilters.length > 0) {
            if (this.orderbookSubscribed) {
                this.lastOrderbookFilters.forEach((filters) => {
                    try {
                        this.wsClient.unsubscribe({
                            subscriptions: [{
                                topic: "clob_market",
                                type: "agg_orderbook",
                                filters
                            }]
                        });
                    } catch (error) {
                        console.warn('⚠️ 订单簿退订失败:', error.message);
                    }
                });
            }
        }

        try {
            newFilters.forEach((filters) => {
                this.wsClient.subscribe({
                    subscriptions: [{
                        topic: "clob_market",
                        type: "agg_orderbook",
                        filters
                    }]
                });
            });

            this.orderbookSubscribed = true;
            this.lastOrderbookFilters = newFilters.map((group) => group.slice());
            console.log(`✅ 订单簿订阅刷新: ${normalizedIds.length} 个 token，${newFilters.length} 条消息`);
        } catch (error) {
            console.error('❌ 订单簿订阅失败:', error.message);
        }
    }

    /**
     * 处理订单簿更新消息
     */
    handleOrderbookUpdate(message) {
        if (!this.modules.orderbook) return;

        // 检查订单簿模块是否全局启用
        if (!this.config.orderbook.enabled) return;

        const signal = this.modules.orderbook.processOrderbook(message);

        if (signal) {
            // 如果signal.marketName是conditionId，尝试从套利缓存中获取真实市场名称
            if (!signal.marketName || signal.marketName === signal.market) {
                const cachedData = this.tryGetMarketDataFromArbitrageCache(signal.market);
                if (cachedData) {
                    signal.marketName = cachedData.title || signal.marketName;
                    console.log(`✅ [订单簿] 从套利缓存获取市场名称: ${signal.marketName}`);
                }
            }

            this.stats.byModule.orderbook.detected++;
            this.sendSignal('orderbook', signal);
        }
    }

    /**
     * 从套利检测器缓存中尝试获取slug
     * @param {string} market - 市场ID
     * @returns {string|null} - slug或null
     */
    tryGetSlugFromArbitrageCache(market) {
        try {
            if (!this.modules.arbitrage || !this.modules.arbitrage.priceCache) {
                return null;
            }

            // 遍历价格缓存，查找匹配的市场
            for (const [tokenId, data] of this.modules.arbitrage.priceCache.entries()) {
                if (data.market === market && data.slug) {
                    return data.slug;
                }
            }

            return null;
        } catch (error) {
            console.error('❌ 从套利缓存获取slug失败:', error.message);
            return null;
        }
    }

    /**
     * 从套利检测器缓存中尝试获取完整市场数据
     * @param {string} market - 市场ID
     * @returns {Object|null} - 市场数据或null
     */
    tryGetMarketDataFromArbitrageCache(market) {
        try {
            if (!this.modules.arbitrage || !this.modules.arbitrage.priceCache) {
                return null;
            }

            // 遍历价格缓存，查找匹配的市场
            for (const [tokenId, data] of this.modules.arbitrage.priceCache.entries()) {
                if (data.market === market) {
                    return {
                        slug: data.slug || data.eventSlug,
                        title: data.title,
                        eventSlug: data.eventSlug,
                        marketSlug: data.marketSlug
                    };
                }
            }

            return null;
        } catch (error) {
            console.error('❌ 从套利缓存获取市场数据失败:', error.message);
            return null;
        }
    }

    async enrichClosingSignal(signal) {
        if (!signal || !Array.isArray(signal.markets) || !signal.markets.length) {
            return;
        }

        const enrichTasks = signal.markets.map(async (market) => {
            const marketKey = market.conditionId || market.marketId;
            if (!marketKey) {
                return;
            }

            if (market.marketSlug && market.eventSlug && market.question && market.question !== 'Unknown market') {
                return;
            }

            try {
                const cached = this.tryGetMarketDataFromArbitrageCache(marketKey);
                if (cached) {
                    market.marketSlug = market.marketSlug || cached.slug || cached.marketSlug || null;
                    market.eventSlug = market.eventSlug || cached.eventSlug || null;
                    if ((!market.question || market.question === 'Unknown market') && cached.title) {
                        market.question = cached.title;
                    }
                    if (market.marketSlug && market.eventSlug && market.question && market.question !== 'Unknown market') {
                        return;
                    }
                }

                const needSlug = !market.marketSlug;
                const needEventSlug = !market.eventSlug;
                const needName = !market.question || market.question === 'Unknown market';

                if (!needSlug && !needEventSlug && !needName) {
                    return;
                }

                const promises = [];
                if (needSlug) {
                    promises.push(marketDataFetcher.getMarketSlug(marketKey));
                } else {
                    promises.push(Promise.resolve(market.marketSlug));
                }

                if (needEventSlug) {
                    promises.push(marketDataFetcher.getEventSlug(marketKey));
                } else {
                    promises.push(Promise.resolve(market.eventSlug));
                }

                if (needName) {
                    promises.push(marketDataFetcher.getMarketName(marketKey));
                } else {
                    promises.push(Promise.resolve(market.question));
                }

                const [marketSlug, eventSlug, marketName] = await Promise.all(promises);

                if (needSlug && marketSlug) {
                    market.marketSlug = marketSlug;
                }

                if (needEventSlug && eventSlug) {
                    market.eventSlug = eventSlug;
                }

                if (needName && marketName) {
                    market.question = marketName;
                }
            } catch (error) {
                console.error('⚠️ [closing] 市场元数据补充失败:', error.message);
            }
        });

        await Promise.allSettled(enrichTasks);
    }

    /**
     * 发送信号
     */
    async sendSignal(moduleName, signal) {
        const totalTimer = metrics.startTimer('sendSignal');
        try {
            if (moduleName !== 'closing' && signal.market && !signal.marketSlug) {
                const enrichTimer = metrics.startTimer('enrichMeta');
                metrics.increment('cache.total');
                
                // 策略0: 共享 slug 缓存（最快，从 activity.trades 提取）
                const sharedCache = this.getSlugFromCache(signal.market);
                if (sharedCache) {
                    signal.eventSlug = sharedCache.eventSlug || signal.eventSlug || null;
                    signal.marketSlug = sharedCache.marketSlug || signal.marketSlug || null;
                    if (!signal.marketName && sharedCache.title) {
                        signal.marketName = sharedCache.title;
                    }
                    metrics.increment('cache.hit');
                }

                const nameMissingOrId = !signal.marketName || signal.marketName === signal.market;
                const slugMissing = !(signal.marketSlug || signal.eventSlug);

                if (!sharedCache || nameMissingOrId || slugMissing) {
                    // 策略1: 检查套利检测器的缓存
                    if (this.modules.arbitrage) {
                        const cached = this.tryGetMarketDataFromArbitrageCache(signal.market);
                        if (cached) {
                            if (!signal.eventSlug && (cached.eventSlug || cached.slug)) {
                                signal.eventSlug = cached.eventSlug || cached.slug;
                            }
                            if (!signal.marketSlug && cached.marketSlug) {
                                signal.marketSlug = cached.marketSlug;
                            }
                            if (!signal.marketName && cached.title) {
                                signal.marketName = cached.title;
                            }
                            metrics.increment('cache.hit');
                        }
                    }

                    // 策略2: CLOB API 备用（200-500ms）
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
                }

                metrics.endTimer(enrichTimer);

                // 策略3: 直接使用 market ID（总是可用）
                if (!signal.marketSlug) {
                    console.log(`⚠️ [${moduleName}] 未找到 slug，将使用 market ID: ${signal.market.substring(0, 12)}...`);
                }
            }

            // 格式化消息
            const formatTimer = metrics.startTimer('format');
            
            // 按语言分组格式化（延迟到发送时）
            const formatForLang = (lang) => {
                const options = { lang };
                if (moduleName === 'arbitrage') {
                    return formatArbitrageSignal(signal, this.config.arbitrage.messageVariant, options);
                } else if (moduleName === 'orderbook') {
                    return formatOrderbookSignal(signal, this.config.orderbook.messageVariant, options);
                } else if (moduleName === 'closing') {
                    return formatClosingSignal(signal, this.config.closing?.messageVariant || 'list', options);
                } else if (moduleName === 'largeTrade') {
                    return formatLargeTradeSignal(signal, options);
                } else if (moduleName === 'newMarket') {
                    return formatNewMarketSignal(signal, options);
                } else if (moduleName === 'smartMoney') {
                    return formatSmartMoneySignal(signal, options);
                }
                return null;
            };
            
            // 默认格式化（用于控制台输出）
            let formatted = formatForLang('zh-CN');
            
            if (!formatted) {
                console.warn(`⚠️ 未知的模块: ${moduleName}`);
                return;
            }
            
            if (moduleName === 'closing') {
                await this.enrichClosingSignal(signal);
                formatted = formatForLang('zh-CN');
                this.lastSignals.closing = {
                    signal,
                    variant: this.config.closing?.messageVariant || 'list',
                    timestamp: Date.now()
                };
            }
            
            metrics.endTimer(formatTimer);

            // 打印到控制台
            console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log(`🎯 [${moduleName.toUpperCase()}] 检测到信号！`);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log(formatted.text);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

            // 发送Telegram消息到所有订阅用户
            if (this.telegramBot && !this.config.debug.dryRun) {
                const subscribedUsers = this.userManager.getSubscribedUsers();

                if (subscribedUsers.length === 0) {
                    console.log('⚠️ 没有订阅用户，跳过发送');
                } else {
                    console.log(`📤 发送到 ${subscribedUsers.length} 个订阅用户...`);

                    let successCount = 0;
                    let failCount = 0;
                    let skippedCount = 0;

                    // 筛选符合条件的用户，按显示模式分组
                    const detailedRecipients = [];
                    const compactRecipients = [];
                    for (const chatId of subscribedUsers) {
                        if (!this.userManager.isNotificationEnabled(chatId, moduleName)) {
                            skippedCount++;
                            continue;
                        }

                        const userThreshold = this.userManager.getThreshold(chatId, moduleName);
                        const passThreshold = this.userManager.checkSignalThreshold(signal, moduleName, userThreshold);
                        if (!passThreshold) {
                            skippedCount++;
                            continue;
                        }
                        
                        const displayMode = this.userManager.getDisplayMode(chatId);
                        if (displayMode === 'compact') {
                            compactRecipients.push(chatId);
                        } else {
                            detailedRecipients.push(chatId);
                        }
                    }
                    const recipients = detailedRecipients;

                    // 颗秒版用户：发送信号历史面板
                    for (const chatId of compactRecipients) {
                        try {
                            await this.commandHandler.renderAlertPanel(chatId);
                            successCount++;
                        } catch (err) {
                            failCount++;
                        }
                    }

                    // 缓存不同语言的格式化结果
                    const formattedCache = {};
                    const getFormattedForUser = (chatId) => {
                        const lang = this.userManager.getLang(chatId);
                        if (!formattedCache[lang]) {
                            formattedCache[lang] = formatForLang(lang);
                        }
                        return formattedCache[lang];
                    };

                    // 详细版用户：发送原始格式
                    const sendToUser = async (chatId) => {
                        try {
                            const userFormatted = getFormattedForUser(chatId);
                            const sentMessage = await this.telegramBot.sendMessage(
                                chatId,
                                userFormatted.text,
                                {
                                    parse_mode: this.config.telegram.parseMode,
                                    reply_markup: userFormatted.keyboard,
                                    disable_notification: this.config.telegram.disableNotification
                                }
                            );
                            successCount++;

                            // 异步添加翻译任务（不阻塞）- 仅中文用户需要翻译
                            const userLang = this.userManager.getLang(chatId);
                            if (this.translationService && userLang === 'zh-CN') {
                                const messageState = {
                                    text: userFormatted.text,
                                    keyboard: userFormatted.keyboard,
                                    signalType: moduleName
                                };
                                if (moduleName === 'closing' && Array.isArray(userFormatted.translationTargets) && userFormatted.translationTargets.length > 0) {
                                    const batchInfo = this.createTranslationBatchInfo(userFormatted.translationTargets);
                                    if (batchInfo) {
                                        messageState.translationBatchInfo = batchInfo;
                                        batchInfo.entries.forEach(({ original }) => {
                                            this.addTranslationTask(original, chatId, sentMessage.message_id, moduleName, messageState);
                                        });
                                    }
                                } else if (signal.marketName) {
                                    this.addTranslationTask(signal.marketName, chatId, sentMessage.message_id, moduleName, messageState);
                                } else if (Array.isArray(userFormatted.translationTargets)) {
                                    userFormatted.translationTargets
                                        .map(t => typeof t === 'string' ? t : t?.text)
                                        .filter(t => t?.trim())
                                        .forEach(t => this.addTranslationTask(t, chatId, sentMessage.message_id, moduleName, messageState));
                                }
                            }
                        } catch (error) {
                            console.error(`❌ 发送到用户 ${chatId} 失败:`, error.message);
                            failCount++;
                        }
                    };

                    // 全并发发送
                    const sendTimer = metrics.startTimer('send');
                    await Promise.all(recipients.map(sendToUser));
                    metrics.endTimer(sendTimer);

                    this.stats.signalsSent++;
                    this.stats.byModule[moduleName].sent++;

                    if (this.commandHandler) {
                        this.commandHandler.incrementSignalCount();
                    }

                    console.log(`✅ 消息发送完成: ${successCount} 成功, ${failCount} 失败, ${skippedCount} 跳过（已关闭通知）`);
                }
            } else if (this.config.debug.dryRun) {
                console.log('🧪 [DRY RUN] 模拟发送（未实际发送）');
            }

        } catch (error) {
            console.error('❌ 发送信号失败:', error.message);
            this.stats.errors++;
        } finally {
            const duration = metrics.endTimer(totalTimer);
            metrics.increment(`signal.${moduleName}`);
            console.log(`📊 [Metrics] sendSignal(${moduleName}) 耗时: ${duration}ms`);
            metrics.logReport();
        }
    }

    /**
     * 添加翻译任务到队列
     * @param {string} marketName - 市场名称（英文）
     * @param {number} chatId - Telegram 聊天ID
     * @param {number} messageId - Telegram 消息ID
     * @param {string} signalType - 信号类型 (arbitrage/orderbook/closing)
     * @param {Object} messageState - 当前消息状态（独立维护文本/键盘）
     */
    async addTranslationTask(marketName, chatId, messageId, signalType, messageState) {
        try {
            const normalizedName = marketName.trim();
            if (!normalizedName) {
                return;
            }

            const messageKey = `${chatId}:${messageId}`;
            let appliedSet = this.translationApplied.get(messageKey);
            if (!appliedSet) {
                appliedSet = new Set();
                this.translationApplied.set(messageKey, appliedSet);
            }

            if (appliedSet.has(normalizedName)) {
                return;
            }

            appliedSet.add(normalizedName);

            const batchInfo = signalType === 'closing' ? messageState.translationBatchInfo : null;

            // 添加任务到队列（非阻塞）
            const translationPromise = this.translationQueue
                ? this.translationQueue.addTask({
                    text: normalizedName,
                    chatId,
                    messageId,
                    signalType
                })
                : this.translateImmediately({
                    text: normalizedName,
                    chatId,
                    messageId,
                    signalType
                });

            translationPromise.then((result) => {
                if (!this.messageUpdater || !result.translation) {
                    return;
                }

                const key = `${result.chatId}:${result.messageId}`;

                if (batchInfo) {
                    batchInfo.completed = (batchInfo.completed || 0) + 1;
                    const original = batchInfo.lookup.get(result.text) || result.text;
                    batchInfo.results.set(result.text, {
                        original,
                        translation: result.translation
                    });
                    if (!batchInfo.firstResultAt) {
                        batchInfo.firstResultAt = Date.now();
                    }

                    this.maybeFlushTranslationBatchPartial(
                        messageKey,
                        result.chatId,
                        result.messageId,
                        messageState,
                        appliedSet
                    );
                    this.tryFinalizeTranslationBatch(messageKey, result.chatId, result.messageId, messageState, appliedSet);
                    return;
                }

                if (this.config.debug?.enabled) {
                    console.log(`🔍 [Translation] 准备更新 ${result.signalType} (${result.chatId}:${result.messageId}) -> "${result.translation.substring(0, 40)}${result.translation.length > 40 ? '…' : ''}"`);
                }

                const attemptUpdate = (attempt = 1) => {
                    const previous = this.translationUpdateQueue.get(key) || Promise.resolve();

                    const updatePromise = previous.catch(() => {}).then(async () => {
                        const messageObject = {
                            text: messageState.text,
                            reply_markup: messageState.keyboard
                        };

                        try {
                            const updatedText = await this.messageUpdater.updateWithTranslation(
                                result.chatId,
                                result.messageId,
                                result.text,
                                result.translation,
                                result.signalType,
                                messageObject
                            );

                            if (updatedText) {
                                messageState.text = updatedText;
                                if (this.config.debug?.enabled) {
                                    console.log(`✅ [Translation] 已更新 ${result.signalType} 消息 ${result.chatId}:${result.messageId}`);
                                }
                            }
                        } catch (err) {
                            if (err.code === 'RATE_LIMIT') {
                                if (attempt >= 5) {
                                    console.error(`❌ [Translation] 限频重试超过上限 (chat=${result.chatId})，放弃本条翻译`);
                                    if (appliedSet.has(normalizedName)) {
                                        appliedSet.delete(normalizedName);
                                    }
                                    return;
                                }

                                const retryDelay = (err.retryAfterMs || 1000) + 1000;
                                console.warn(`⚠️ [Translation] 限频 (chat=${result.chatId})，${Math.ceil(retryDelay / 1000)} 秒后重试 (#${attempt})`);
                                const timerKey = `translation:${result.chatId}:${result.messageId}:${normalizedName}`;
                                this.scheduleTranslationRetry(timerKey, retryDelay, () => attemptUpdate(attempt + 1));
                                return;
                            }

                            throw err;
                        }
                    }).catch((err) => {
                        console.error(`❌ [Translation] 更新消息失败: ${err.message}`);
                        if (appliedSet.has(normalizedName)) {
                            appliedSet.delete(normalizedName);
                        }
                    });

                    this.translationUpdateQueue.set(
                        key,
                        updatePromise.finally(() => {
                            if (this.translationUpdateQueue.get(key) === updatePromise) {
                                this.translationUpdateQueue.delete(key);
                            }
                            if (appliedSet.size === 0) {
                                this.translationApplied.delete(messageKey);
                            }
                        })
                    );
                };

                attemptUpdate();
            }).catch((error) => {
                // 翻译失败，不影响主流程
                console.warn(`⚠️ [Translation] 翻译失败: ${marketName.substring(0, 30)}... - ${error.message}`);
                if (batchInfo) {
                    batchInfo.failures = (batchInfo.failures || 0) + 1;
                    this.tryFinalizeTranslationBatch(messageKey, chatId, messageId, messageState, appliedSet);
                }
                if (appliedSet.has(normalizedName)) {
                    appliedSet.delete(normalizedName);
                }
            });
        } catch (error) {
            console.error('❌ [Translation] 添加翻译任务失败:', error.message);
        }
    }

    translateImmediately({ text, chatId, messageId, signalType }) {
        if (!this.translationService) {
            return Promise.reject(new Error('翻译服务不可用'));
        }

        const timer = metrics.startTimer('translate');
        return this.translationService.translate(text).then((translation) => {
            metrics.endTimer(timer);
            metrics.increment('translate.success');
            return { text, translation, chatId, messageId, signalType };
        }).catch((err) => {
            metrics.endTimer(timer);
            metrics.increment('translate.fail');
            throw err;
        });
    }

    createTranslationBatchInfo(translationTargets = []) {
        if (!Array.isArray(translationTargets) || translationTargets.length === 0) {
            return null;
        }

        const entries = [];
        const lookup = new Map();

        translationTargets.forEach((target) => {
            const original = typeof target === 'string' ? target : target?.text;
            if (!original) {
                return;
            }
            const normalized = original.trim();
            if (!normalized || lookup.has(normalized)) {
                return;
            }
            lookup.set(normalized, original);
            entries.push({ original, normalized });
        });

        if (entries.length === 0) {
            return null;
        }

        return {
            expected: entries.length,
            entries,
            lookup,
            results: new Map(),
            completed: 0,
            failures: 0,
            finalizing: false,
            applied: false,
            waitingRetry: false,
            appliedEntries: new Set(),
            createdAt: Date.now(),
            firstResultAt: 0,
            lastFlushAt: 0,
            partialTimer: null,
            partialInFlight: false
        };
    }

    scheduleTranslationRetry(key, delayMs, fn) {
        const safeDelay = Math.max(delayMs || 0, 1000);

        if (this.translationRetryTimers.has(key)) {
            clearTimeout(this.translationRetryTimers.get(key));
        }

        const timer = setTimeout(async () => {
            this.translationRetryTimers.delete(key);
            try {
                await fn();
            } catch (error) {
                const description = error?.response?.body?.description || error.message;
                console.error(`❌ [Translation] 限频重试执行失败 (${key}): ${description}`);
            }
        }, safeDelay);

        this.translationRetryTimers.set(key, timer);
    }

    maybeFlushTranslationBatchPartial(messageKey, chatId, messageId, messageState, appliedSet) {
        const batchInfo = messageState.translationBatchInfo;
        if (!batchInfo || this.translationBatchPartialFlushMs <= 0) {
            return;
        }

        if (batchInfo.applied || batchInfo.finalizing || batchInfo.waitingRetry || batchInfo.partialInFlight) {
            return;
        }

        const available = [];
        batchInfo.entries.forEach(({ original, normalized }) => {
            if (batchInfo.appliedEntries.has(normalized)) {
                return;
            }
            const stored = batchInfo.results.get(normalized);
            if (stored && stored.translation) {
                available.push({
                    original,
                    translation: stored.translation,
                    normalized
                });
            }
        });

        if (available.length === 0) {
            return;
        }

        const now = Date.now();
        const sinceFirst = batchInfo.firstResultAt ? now - batchInfo.firstResultAt : 0;
        const sinceLastFlush = batchInfo.lastFlushAt ? now - batchInfo.lastFlushAt : Number.POSITIVE_INFINITY;

        const minCountMet = available.length >= this.translationBatchPartialFlushMin;
        const timeMet = sinceLastFlush >= this.translationBatchPartialFlushMs
            || (!batchInfo.lastFlushAt && sinceFirst >= this.translationBatchPartialFlushMs);

        if (!minCountMet && !timeMet) {
            if (!batchInfo.partialTimer) {
                const elapsed = batchInfo.lastFlushAt ? sinceLastFlush : sinceFirst;
                const waitMs = Math.max(0, this.translationBatchPartialFlushMs - elapsed) || this.translationBatchPartialFlushMs;
                batchInfo.partialTimer = setTimeout(() => {
                    batchInfo.partialTimer = null;
                    this.maybeFlushTranslationBatchPartial(messageKey, chatId, messageId, messageState, appliedSet);
                }, waitMs);
            }
            return;
        }

        if (batchInfo.partialTimer) {
            clearTimeout(batchInfo.partialTimer);
            batchInfo.partialTimer = null;
        }

        batchInfo.partialInFlight = true;

        this.queueBatchTranslationUpdate({
            messageKey,
            chatId,
            messageId,
            messageState,
            appliedSet,
            batchInfo,
            updates: available,
            isFinal: false
        });
    }

    queueBatchTranslationUpdate({
        messageKey,
        chatId,
        messageId,
        messageState,
        appliedSet,
        batchInfo,
        updates,
        isFinal
    }) {
        if (!this.messageUpdater || !Array.isArray(updates) || updates.length === 0) {
            return;
        }

        const key = `${chatId}:${messageId}`;

        const runUpdate = (attempt = 1) => {
            batchInfo.waitingRetry = false;
            const previous = this.translationUpdateQueue.get(key) || Promise.resolve();

            const updatePromise = previous.catch(() => {}).then(async () => {
                const messageObject = {
                    text: messageState.text,
                    reply_markup: messageState.keyboard
                };

                const cleanedUpdates = updates.map(({ original, translation }) => ({
                    original,
                    translation
                }));

                try {
                    const updatedText = await this.messageUpdater.updateWithTranslationsBatch(
                        chatId,
                        messageId,
                        cleanedUpdates,
                        messageState.signalType || 'closing',
                        messageObject
                    );

                    if (updatedText) {
                        messageState.text = updatedText;
                    }

                    const now = Date.now();
                    batchInfo.lastFlushAt = now;

                    updates.forEach(({ normalized, original }) => {
                        const keyNormalized = normalized || (original ? original.trim() : '');
                        if (keyNormalized) {
                            batchInfo.appliedEntries.add(keyNormalized);
                        }
                    });

                    if (batchInfo.partialTimer) {
                        clearTimeout(batchInfo.partialTimer);
                        batchInfo.partialTimer = null;
                    }

                    if (!isFinal) {
                        batchInfo.partialInFlight = false;
                        this.tryFinalizeTranslationBatch(messageKey, chatId, messageId, messageState, appliedSet);
                    }

                    if (isFinal) {
                        batchInfo.applied = true;
                        batchInfo.finalizing = false;
                        appliedSet.clear();
                        if (this.translationApplied.has(messageKey)) {
                            this.translationApplied.delete(messageKey);
                        }
                        messageState.translationBatchInfo = null;
                    } else if (this.config.debug?.enabled) {
                        console.log(`✅ [Translation] 局部更新完成 ${messageState.signalType || 'closing'} ${chatId}:${messageId} (${updates.length} 条)`);
                    }
                } catch (err) {
                    if (err.code === 'RATE_LIMIT') {
                        if (attempt >= 5) {
                            console.error(`❌ [Translation] ${isFinal ? '批量' : '局部'}限频重试超过上限 (chat=${chatId})，放弃此次翻译更新`);
                            if (isFinal) {
                                batchInfo.applied = true;
                                batchInfo.finalizing = false;
                                appliedSet.clear();
                                if (this.translationApplied.has(messageKey)) {
                                    this.translationApplied.delete(messageKey);
                                }
                                messageState.translationBatchInfo = null;
                            } else {
                                batchInfo.partialInFlight = false;
                                this.tryFinalizeTranslationBatch(messageKey, chatId, messageId, messageState, appliedSet);
                            }
                            return;
                        }

                        const retryDelay = (err.retryAfterMs || 1000) + 1000;
                        batchInfo.waitingRetry = true;
                        const timerKey = `translationBatch:${chatId}:${messageId}${isFinal ? ':final' : ':partial'}`;
                        const label = isFinal ? '批量' : '局部';
                        console.warn(`⚠️ [Translation] ${label}限频 (chat=${chatId})，${Math.ceil(retryDelay / 1000)} 秒后重试 (#${attempt})`);
                        this.scheduleTranslationRetry(timerKey, retryDelay, () => {
                            batchInfo.waitingRetry = false;
                            runUpdate(attempt + 1);
                        });
                        return;
                    }

                    throw err;
                }
            }).catch((err) => {
                if (err && err.code === 'RATE_LIMIT') {
                    return;
                }
                console.error(`❌ [Translation] ${isFinal ? '批量' : '局部'}更新消息失败: ${err.message}`);
                if (!isFinal) {
                    batchInfo.partialInFlight = false;
                    this.tryFinalizeTranslationBatch(messageKey, chatId, messageId, messageState, appliedSet);
                }
                if (isFinal) {
                    batchInfo.finalizing = false;
                    appliedSet.clear();
                    if (this.translationApplied.has(messageKey)) {
                        this.translationApplied.delete(messageKey);
                    }
                    messageState.translationBatchInfo = null;
                }
            }).finally(() => {
                if (!isFinal && !batchInfo.waitingRetry && !batchInfo.applied) {
                    batchInfo.partialInFlight = false;
                }
                if (this.translationUpdateQueue.get(key) === updatePromise) {
                    this.translationUpdateQueue.delete(key);
                }

                if (!isFinal && appliedSet.size === 0 && !batchInfo.applied && !this.translationApplied.has(messageKey)) {
                    this.translationApplied.delete(messageKey);
                }
            });

            this.translationUpdateQueue.set(key, updatePromise);
        };

        runUpdate();
    }

    tryFinalizeTranslationBatch(messageKey, chatId, messageId, messageState, appliedSet) {
        const batchInfo = messageState.translationBatchInfo;
        if (!batchInfo) {
            return;
        }

        if (batchInfo.partialInFlight) {
            return;
        }

        const processed = (batchInfo.completed || 0) + (batchInfo.failures || 0);
        if (batchInfo.applied || batchInfo.finalizing || processed < batchInfo.expected) {
            return;
        }

        const updates = batchInfo.entries
            .map(({ original, normalized }) => {
                const stored = batchInfo.results.get(normalized);
                if (!stored || !stored.translation) {
                    return null;
                }
                if (batchInfo.appliedEntries.has(normalized)) {
                    return null;
                }
                return {
                    original,
                    translation: stored.translation,
                    normalized
                };
            })
            .filter(Boolean);

        if (updates.length === 0) {
            batchInfo.applied = true;
            batchInfo.finalizing = false;
            appliedSet.clear();
            this.translationApplied.delete(messageKey);
            messageState.translationBatchInfo = null;
            if (batchInfo.partialTimer) {
                clearTimeout(batchInfo.partialTimer);
                batchInfo.partialTimer = null;
            }
            return;
        }

        batchInfo.finalizing = true;
        batchInfo.waitingRetry = false;

        this.queueBatchTranslationUpdate({
            messageKey,
            chatId,
            messageId,
            messageState,
            appliedSet,
            batchInfo,
            updates,
            isFinal: true
        });
    }

    /**
     * 更新扫尾盘消息的分页
     * @param {Object} context
     * @param {number} context.chatId
     * @param {number} context.messageId
     * @param {number} context.page
     * @returns {Promise<boolean>}
     */
    async updateClosingMessagePage({ chatId, messageId, page } = {}) {
        try {
            if (!this.modules.closing || !this.config.closing?.enabled) {
                return false;
            }

            const record = this.lastSignals.closing;
            if (!record?.signal) {
                return false;
            }

            const variant = record.variant || this.config.closing?.messageVariant || 'list';
            const pageSize = this.config.closing?.pageSize || 5;

            // 传递翻译缓存给formatter,这样可以直接使用已有的翻译
            const userLang = this.userManager.getLang(chatId);
            const formatterOptions = {
                page,
                pageSize,
                lang: userLang,
                translationCache: userLang === 'zh-CN' ? (this.translationService?.cache || null) : null
            };
            const formatted = formatClosingSignal(record.signal, variant, formatterOptions);

            await this.telegramBot.editMessageText(formatted.text, {
                chat_id: chatId,
                message_id: messageId,
                parse_mode: this.config.telegram.parseMode,
                reply_markup: formatted.keyboard,
                disable_web_page_preview: true

            });
            // 如果有未翻译的项目(translationTargets不为空),添加翻译任务
            if (this.translationService && Array.isArray(formatted.translationTargets) && formatted.translationTargets.length > 0) {
                const messageKey = `${chatId}:${messageId}`;
                const messageState = {
                    text: formatted.text,
                    keyboard: formatted.keyboard,
                    signalType: 'closing'
                };

                const batchInfo = this.createTranslationBatchInfo(formatted.translationTargets);
                if (batchInfo) {
                    messageState.translationBatchInfo = batchInfo;
                    batchInfo.entries.forEach(({ original }) => {
                        this.addTranslationTask(
                            original,
                            chatId,
                            messageId,
                            'closing',
                            messageState
                        );
                    });
                }
            }

            return true;
        } catch (error) {
            console.error('❌ 更新扫尾盘分页失败:', error.message);
            return false;
        }
    }

    /**
     * 向指定聊天发送最近一次扫尾盘列表
     * @param {Object} context
     * @param {number} context.chatId
     * @param {number} [context.replyTo]
     * @param {number} [context.page]
     * @returns {Promise<boolean>}
     */
    async sendLatestClosingMessage({ chatId, replyTo, page = 1 } = {}) {
        const userLang = this.userManager.getLang(chatId);
        const i18nMsg = userLang === 'en' 
            ? { disabled: '⚠️ Closing module is disabled.', noCache: '📭 No closing data cached. Try again later.' }
            : { disabled: '⚠️ 扫尾盘模块未启用。', noCache: '📭 暂无扫尾盘缓存，稍后再试。' };
        
        try {
            if (!this.modules.closing || !this.config.closing?.enabled) {
                await this.telegramBot.sendMessage(chatId, i18nMsg.disabled, {
                    reply_to_message_id: replyTo
                });
                return false;
            }

            const record = this.lastSignals.closing;
            if (!record?.signal) {
                await this.telegramBot.sendMessage(chatId, i18nMsg.noCache, {
                    reply_to_message_id: replyTo
                });
                return false;
            }

            const variant = record.variant || this.config.closing?.messageVariant || 'list';
            const pageSize = this.config.closing?.pageSize || 5;
            const formatted = formatClosingSignal(record.signal, variant, { 
                page, 
                pageSize, 
                lang: userLang,
                translationCache: userLang === 'zh-CN' ? (this.translationService?.cache || null) : null
            });

            const sentMessage = await this.telegramBot.sendMessage(chatId, formatted.text, {
                parse_mode: this.config.telegram.parseMode,
                reply_markup: formatted.keyboard,
                reply_to_message_id: replyTo,
                disable_notification: this.config.telegram.disableNotification
                });

            const messageState = {
                text: formatted.text,
                keyboard: formatted.keyboard,
                signalType: 'closing'
            };

            if (this.translationService && userLang === 'zh-CN' && Array.isArray(formatted.translationTargets)) {
                const batchInfo = this.createTranslationBatchInfo(formatted.translationTargets);
                if (batchInfo) {
                    messageState.translationBatchInfo = batchInfo;
                    batchInfo.entries.forEach(({ original }) => {
                        this.addTranslationTask(
                            original,
                            chatId,
                            sentMessage.message_id,
                            'closing',
                            messageState
                        );
                    });
                } else {
                    formatted.translationTargets
                        .map((target) => typeof target === 'string' ? target : target?.text)
                        .filter((target) => target && target.trim())
                        .forEach((targetText) => {
                            this.addTranslationTask(
                                targetText,
                                chatId,
                                sentMessage.message_id,
                                'closing',
                                messageState
                            );
                        });
                }
            }

            return true;
        } catch (error) {
            console.error('❌ 发送扫尾盘缓存失败:', error.message);
            await this.telegramBot.sendMessage(chatId, '❌ 发送扫尾盘缓存失败，请稍后重试。', {
                reply_to_message_id: replyTo
            });
            return false;
        }
    }

    /**
     * 启动定时任务
     */
    startScheduledTasks() {
        // 定期打印统计信息
        const statsInterval = setInterval(() => {
            this.printStats();
        }, this.config.performance.statsInterval);
        this.intervals.push(statsInterval);

        // 定期清理过期数据
        const cleanupInterval = setInterval(() => {
            this.cleanup();
        }, this.config.performance.cleanupInterval);
        this.intervals.push(cleanupInterval);

        // 日志文件清理任务（每小时检查，超过50MB则截断）
        const logCleanupInterval = setInterval(() => {
            this.cleanupLogFile();
        }, 3600000);  // 1小时
        this.intervals.push(logCleanupInterval);

        // 性能指标报告（每5分钟）
        const metricsInterval = setInterval(() => {
            metrics.logReportWithOptions({ force: true });
        }, 300000);  // 5分钟
        this.intervals.push(metricsInterval);

        // 内存监控任务（每10分钟检查一次）
        const memoryCheckInterval = setInterval(() => {
            this.checkMemoryUsage();
        }, 600000);  // 10分钟
        this.intervals.push(memoryCheckInterval);

        // 翻译缓存保存任务（每30分钟保存一次）
        if (this.translationService) {
            const cacheSaveInterval = setInterval(() => {
                this.translationService.saveCache().catch(err => {
                    console.error('❌ 保存翻译缓存失败:', err.message);
                });
            }, 1800000);  // 30分钟
            this.intervals.push(cacheSaveInterval);
        }

        if (this.modules.closing && this.config.closing?.enabled) {
            const runClosingScan = async () => {
                try {
                    const signal = await this.modules.closing.scan();
                    if (signal) {
                        const marketCount = Array.isArray(signal.markets) ? signal.markets.length : 1;
                        this.stats.byModule.closing.detected += marketCount;
                        await this.sendSignal('closing', signal);
                    }
                } catch (error) {
                    console.error('❌ 扫尾盘扫描失败:', error.message);
                    if (this.config.debug?.enabled) {
                        console.error(error);
                    }
                }
            };

            runClosingScan();

            const intervalMs = Math.max(60_000, this.config.closing.refreshIntervalMs || 300_000);
            const closingInterval = setInterval(runClosingScan, intervalMs);
            this.intervals.push(closingInterval);
            this.closingScanInterval = closingInterval;
        }

        // 新市场扫描
        if (this.config.newMarket?.enabled) {
            this.newMarketDetector = new NewMarketDetector({
                maxAge: 3600000,
                disableRateLimit: true
            });
            this.newMarketBaselineLoaded = false;  // 基线标记
            
            const runNewMarketScan = async () => {
                const isBaseline = !this.newMarketBaselineLoaded;
                try {
                    const fetch = require('node-fetch');
                    const response = await fetch(`${this.config.newMarket.gammaApi}/markets?active=true&closed=false&limit=${this.config.newMarket.limit}&order=createdAt&ascending=false`);
                    if (!response.ok) return;
                    
                    const markets = await response.json();
                    for (const market of markets) {
                        if (isBaseline) {
                            // 基线加载：只记录不推送
                            this.newMarketDetector.seenMarkets.set(market.conditionId, Date.now());
                        } else {
                            const signal = this.newMarketDetector.process(market);
                            if (signal) {
                                this.stats.byModule.newMarket = this.stats.byModule.newMarket || { detected: 0, sent: 0 };
                                this.stats.byModule.newMarket.detected++;
                                await this.sendSignal('newMarket', signal);
                            }
                        }
                    }
                    
                    if (isBaseline) {
                        this.newMarketBaselineLoaded = true;
                        console.log(`✅ 新市场基线加载完成: ${this.newMarketDetector.seenMarkets.size} 个市场`);
                    }
                } catch (error) {
                    console.error('❌ 新市场扫描失败:', error.message);
                }
            };

            // 首次扫描加载基线
            setTimeout(runNewMarketScan, 5000);
            const newMarketInterval = setInterval(runNewMarketScan, this.config.newMarket.scanIntervalMs);
            this.intervals.push(newMarketInterval);
        }

        // 聪明钱扫描
        if (this.config.smartMoney?.enabled) {
            this.smartMoneySnapshot = new Map();
            this.smartMoneyBaselineLoaded = false;
            
            const runSmartMoneyScan = async () => {
                const isBaseline = !this.smartMoneyBaselineLoaded;
                try {
                    const fetch = require('node-fetch');
                    const response = await fetch(`${this.config.smartMoney.dataApi}/v1/leaderboard?limit=${this.config.smartMoney.trackTopN}`);
                    if (!response.ok) return;
                    
                    const data = await response.json();
                    const traders = Array.isArray(data) ? data : (data.leaderboard || []);
                    
                    for (const trader of traders) {
                        const address = trader.proxyWallet || trader.address;
                        if (!address) continue;
                        
                        const posResponse = await fetch(`${this.config.smartMoney.dataApi}/positions?user=${address}&limit=50`);
                        if (!posResponse.ok) continue;
                        
                        const positions = await posResponse.json();
                        const oldSnapshot = this.smartMoneySnapshot.get(address) || new Map();
                        const newSnapshot = new Map();
                        
                        for (const pos of (positions || [])) {
                            const value = (pos.size || 0) * (pos.curPrice || 0);
                            if (value < this.config.smartMoney.minPositionValue) continue;
                            
                            const key = pos.conditionId || pos.asset;
                            newSnapshot.set(key, {
                                size: pos.size || 0,
                                side: pos.outcome || pos.side,
                                value,
                                title: pos.title || pos.question,
                                curPrice: pos.curPrice,
                                eventSlug: pos.eventSlug || pos.slug
                            });
                            
                            if (!isBaseline) {
                                const old = oldSnapshot.get(key);
                                // 获取市场详情（流动性、成交量）
                                const details = pos.conditionId ? await marketDataFetcher.getMarketDetails(pos.conditionId) : null;
                                
                                if (!old) {
                                    // 新建仓
                                    this.stats.byModule.smartMoney = this.stats.byModule.smartMoney || { detected: 0, sent: 0 };
                                    this.stats.byModule.smartMoney.detected++;
                                    await this.sendSignal('smartMoney', {
                                        subtype: 'new_position',
                                        traderRank: trader.rank,
                                        traderAddress: address,
                                        outcome: pos.outcome || 'YES',
                                        value,
                                        price: pos.curPrice,
                                        avgPrice: pos.avgPrice,
                                        percentPnl: pos.percentPnl,
                                        endDate: pos.endDate,
                                        marketName: pos.title || pos.question,
                                        conditionId: pos.conditionId,
                                        eventSlug: pos.eventSlug || pos.slug,
                                    });
                                } else if (value > old.value * 1.5) {
                                    // 加仓 >50%
                                    this.stats.byModule.smartMoney = this.stats.byModule.smartMoney || { detected: 0, sent: 0 };
                                    this.stats.byModule.smartMoney.detected++;
                                    await this.sendSignal('smartMoney', {
                                        subtype: 'add_position',
                                        traderRank: trader.rank,
                                        traderAddress: address,
                                        outcome: pos.outcome || 'YES',
                                        value,
                                        previousSize: old.size,
                                        currentSize: pos.size,
                                        price: pos.curPrice,
                                        avgPrice: pos.avgPrice,
                                        percentPnl: pos.percentPnl,
                                        endDate: pos.endDate,
                                        marketName: pos.title || pos.question,
                                        conditionId: pos.conditionId,
                                        eventSlug: pos.eventSlug || pos.slug,
                                    });
                                }
                            }
                        }
                        
                        // 检测清仓
                        if (!isBaseline) {
                            for (const [key, old] of oldSnapshot) {
                                if (!newSnapshot.has(key) && old.value > 500) {
                                    this.stats.byModule.smartMoney = this.stats.byModule.smartMoney || { detected: 0, sent: 0 };
                                    this.stats.byModule.smartMoney.detected++;
                                    await this.sendSignal('smartMoney', {
                                        subtype: 'close_position',
                                        traderRank: trader.rank,
                                        traderAddress: address,
                                        outcome: old.side || 'YES',
                                        value: old.value,
                                        marketName: old.title,
                                        conditionId: key,
                                        eventSlug: old.eventSlug
                                    });
                                }
                            }
                        }
                        
                        this.smartMoneySnapshot.set(address, newSnapshot);
                    }
                    
                    if (isBaseline) {
                        this.smartMoneyBaselineLoaded = true;
                        console.log(`✅ 聪明钱基线加载完成，跟踪 ${this.smartMoneySnapshot.size} 个地址`);
                    }
                } catch (error) {
                    console.error('❌ 聪明钱扫描失败:', error.message);
                }
            };

            setTimeout(runSmartMoneyScan, 10000);
            const smartMoneyInterval = setInterval(runSmartMoneyScan, this.config.smartMoney.scanIntervalMs);
            this.intervals.push(smartMoneyInterval);
        }
    }

    /**
     * 检查内存使用并主动清理
     */
    checkMemoryUsage() {
        const memUsage = process.memoryUsage();
        const heapUsedMB = memUsage.heapUsed / 1024 / 1024;

        console.log(`💾 内存检查: Heap ${heapUsedMB.toFixed(2)} MB`);

        // 如果内存使用超过300MB，主动清理
        if (heapUsedMB > 300) {
            console.log(`⚠️ 内存使用较高 (${heapUsedMB.toFixed(2)} MB)，触发主动清理...`);
            this.cleanup();

            // 强制垃圾回收（如果可用）
            if (global.gc) {
                console.log('🧹 执行垃圾回收...');
                global.gc();
                const afterGC = process.memoryUsage().heapUsed / 1024 / 1024;
                console.log(`✅ 垃圾回收完成: ${afterGC.toFixed(2)} MB (释放 ${(heapUsedMB - afterGC).toFixed(2)} MB)`);
            } else {
                console.log('💡 提示: 使用 node --expose-gc 启动以启用手动垃圾回收');
            }
        }

        // 如果内存使用超过500MB，发出严重警告
        if (heapUsedMB > 500) {
            console.error(`🚨 内存使用过高 (${heapUsedMB.toFixed(2)} MB)，强烈建议重启Bot！`);

            // 如果有 Telegram Bot，发送警告给管理员
            if (this.telegramBot && this.config.telegram.chatId) {
                this.telegramBot.sendMessage(
                    this.config.telegram.chatId,
                    `🚨 *内存警告*\n\n当前内存使用: ${heapUsedMB.toFixed(2)} MB\n强烈建议重启Bot！`,
                    { parse_mode: 'Markdown' }
                ).catch(err => console.error('发送内存警告失败:', err.message));
            }
        }
    }

    /**
     * 打印配置信息
     */
    printConfig() {
        console.log('📋 配置信息:');
        console.log(`   WebSocket: ${this.config.polymarket.host}`);
        console.log(`   Telegram: ${this.config.telegram.chatId ? '已配置' : '未配置'}`);
        console.log('\n📊 启用的模块:');

        if (this.config.arbitrage.enabled) {
            console.log('   ✅ 套利检测');
            console.log(`      - 最低利润: ${(this.config.arbitrage.minProfit * 100).toFixed(1)}%`);
            console.log(`      - 冷却时间: ${this.config.arbitrage.cooldown / 1000}秒`);
        }

        if (this.config.orderbook.enabled) {
            console.log('   ✅ 订单簿失衡检测');
            console.log(`      - 最低失衡: ${this.config.orderbook.minImbalance}倍`);
            console.log(`      - 冷却时间: ${this.config.orderbook.cooldown / 1000}秒`);
        }

        if (this.config.closing?.enabled) {
            console.log('   ✅ 扫尾盘扫描');
            console.log(`      - 时间窗口: ${this.config.closing.timeWindowHours}小时`);
            console.log(`      - 刷新频率: ${(this.config.closing.refreshIntervalMs / 60000).toFixed(1)}分钟`);
        }

        console.log('');
    }

    /**
     * 打印统计信息
     */
    printStats() {
        const uptime = Math.floor((Date.now() - this.stats.startTime) / 1000);
        const hours = Math.floor(uptime / 3600);
        const minutes = Math.floor((uptime % 3600) / 60);

        // 获取内存使用情况
        const memUsage = process.memoryUsage();
        const heapUsedMB = (memUsage.heapUsed / 1024 / 1024).toFixed(2);
        const heapTotalMB = (memUsage.heapTotal / 1024 / 1024).toFixed(2);
        const rssMB = (memUsage.rss / 1024 / 1024).toFixed(2);

        console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('📊 运行统计');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log(`运行时间: ${hours}小时 ${minutes}分钟`);
        console.log(`处理消息: ${this.stats.messagesProcessed}`);
        console.log(`发送信号: ${this.stats.signalsSent}`);
        console.log(`错误次数: ${this.stats.errors}`);
        console.log(`\n💾 内存使用:`);
        console.log(`  Heap: ${heapUsedMB} MB / ${heapTotalMB} MB`);
        console.log(`  RSS: ${rssMB} MB`);
        console.log(`  活跃Token: ${this.activeTokens.size}`);
        console.log(`  消息类型: ${Object.keys(this.messageCount || {}).length} 个`);

        if (this.modules.arbitrage) {
            const arbStats = this.modules.arbitrage.getStats();
            console.log(`\n💰 套利检测:`);
            console.log(`  检测到: ${arbStats.detected}`);
            console.log(`  已发送: ${arbStats.sent}`);
            console.log(`  跳过: ${arbStats.skipped}`);
            console.log(`  缓存大小: ${arbStats.cacheSize}`);
        }

        if (this.modules.orderbook) {
            const obStats = this.modules.orderbook.getStats();
            console.log(`\n📚 订单簿失衡:`);
            console.log(`  检测到: ${obStats.detected}`);
            console.log(`  已发送: ${obStats.sent}`);
            console.log(`  跳过: ${obStats.skipped}`);
            console.log(`  追踪市场: ${obStats.marketsTracked}`);
        }

        if (this.modules.closing) {
            const closingStats = this.modules.closing.getStats();
            console.log(`\n⏰ 扫尾盘扫描:`);
            console.log(`  扫描次数: ${closingStats.scans}`);
            console.log(`  触发信号: ${closingStats.emissions}`);
            console.log(`  上次信号市场数: ${closingStats.marketsLastSignal}`);
            console.log(`  上次更新时间: ${closingStats.lastSignalAt ? closingStats.lastSignalAt.toISOString() : '无'}`);
        }

        // 翻译统计
        if (this.translationService) {
            const translationStats = this.translationService.getStats();
            console.log(`\n🌐 Google 翻译:`);
            console.log(`  API调用: ${translationStats.apiCalls} (${translationStats.successRate})`);
            console.log(`  翻译字符: ${translationStats.totalChars}`);
            console.log(`  缓存命中率: ${translationStats.cache.hitRate}`);
            console.log(`  缓存大小: ${translationStats.cache.size}/${translationStats.cache.maxSize}`);
            console.log(`  服务状态: ${translationStats.isDisabled ? '🔴 已禁用' : '🟢 正常'}`);
        }

        if (this.translationQueue) {
            const queueStatus = this.translationQueue.getStatus();
            console.log(`\n📦 翻译队列:`);
            console.log(`  队列长度: ${queueStatus.queueLength}`);
            console.log(`  处理中: ${queueStatus.processingCount}`);
            console.log(`  已完成: ${queueStatus.stats.tasksProcessed}`);
            console.log(`  已失败: ${queueStatus.stats.tasksFailed}`);
        }

        if (this.messageUpdater) {
            const updaterStats = this.messageUpdater.getStats();
            console.log(`\n✏️ 消息更新:`);
            console.log(`  总更新: ${updaterStats.updates}`);
            console.log(`  成功率: ${updaterStats.successRate}`);
        }

        // 内存警告
        if (heapUsedMB > 500) {
            console.log(`\n⚠️ 内存使用过高 (${heapUsedMB} MB)，建议重启！`);
        }

        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    }

    /**
     * 清理日志文件（超过50MB则截断保留最后10MB）
     */
    cleanupLogFile() {
        const fs = require('fs');
        const logPath = path.join(__dirname, 'logs/bot.log');
        try {
            const stats = fs.statSync(logPath);
            const sizeMB = stats.size / (1024 * 1024);
            if (sizeMB > 50) {
                const content = fs.readFileSync(logPath, 'utf8');
                const keepBytes = 10 * 1024 * 1024; // 保留最后10MB
                const truncated = content.slice(-keepBytes);
                fs.writeFileSync(logPath, truncated);
                console.log(`🧹 日志文件已截断: ${sizeMB.toFixed(1)}MB -> ${(truncated.length / 1024 / 1024).toFixed(1)}MB`);
            }
        } catch (err) {
            // 忽略错误
        }
    }

    /**
     * 清理过期数据
     */
    cleanup() {
        console.log('🧹 清理过期数据...');

        // 清理检测器缓存
        if (this.modules.arbitrage) {
            this.modules.arbitrage.cleanupCache();
        }

        if (this.modules.orderbook) {
            this.modules.orderbook.cleanup();
        }

        // 清理 activeTokens Set（限制最大数量）
        if (this.activeTokens.size > 100) {
            console.log(`🧹 activeTokens 过大 (${this.activeTokens.size})，重置...`);
            // 保留最近订阅的 20 个
            const recent = Array.from(this.activeTokens).slice(-20);
            this.activeTokens = new Set(recent);
            this.lastOrderbookFilters = [];
            this.orderbookSubscribed = false;
            this.scheduleOrderbookRefresh({ force: true });
        }

        // 清理 messageCount 对象（定期重置）
        if (this.messageCount && Object.keys(this.messageCount).length > 1000) {
            console.log(`🧹 messageCount 过大 (${Object.keys(this.messageCount).length} 个键)，重置...`);
            this.messageCount = {};
        }

        // 清理翻译相关 Map（防止内存泄漏）
        if (this.translationUpdateQueue?.size > 500) {
            this.translationUpdateQueue.clear();
        }
        if (this.translationApplied?.size > 500) {
            this.translationApplied.clear();
        }
        if (this.translationRetryTimers?.size > 100) {
            for (const timer of this.translationRetryTimers.values()) {
                clearTimeout(timer);
            }
            this.translationRetryTimers.clear();
        }

        // 清理冷却时间缓存
        if (this.modules.arbitrage && this.modules.arbitrage.lastSignals) {
            const now = Date.now();
            const cooldown = this.modules.arbitrage.COOLDOWN;
            for (const [market, time] of this.modules.arbitrage.lastSignals.entries()) {
                if (now - time > cooldown * 10) {  // 清理10倍冷却时间之前的记录
                    this.modules.arbitrage.lastSignals.delete(market);
                }
            }
        }

        if (this.modules.orderbook && this.modules.orderbook.lastSignals) {
            const now = Date.now();
            const cooldown = this.modules.orderbook.COOLDOWN;
            for (const [market, time] of this.modules.orderbook.lastSignals.entries()) {
                if (now - time > cooldown * 10) {
                    this.modules.orderbook.lastSignals.delete(market);
                }
            }
        }

        console.log(`✅ 清理完成: activeTokens=${this.activeTokens.size}, messageCount=${Object.keys(this.messageCount || {}).length} 个键`);
    }

    /**
     * 停止Bot
     */
    async stop() {
        console.log('\n🛑 停止Bot...');

        // 清理定时任务
        this.intervals.forEach(interval => clearInterval(interval));
        if (this.orderbookRefreshTimer) {
            clearTimeout(this.orderbookRefreshTimer);
            this.orderbookRefreshTimer = null;
        }

        // 断开WebSocket
        if (this.wsClient) {
            this.wsClient.disconnect();
        }

        // 保存翻译缓存
        if (this.translationService) {
            console.log('💾 保存翻译缓存...');
            try {
                await this.translationService.saveCache();
                console.log('✅ 翻译缓存已保存');
            } catch (error) {
                console.error('❌ 保存翻译缓存失败:', error.message);
            }
        }

        if (this.userManager && typeof this.userManager.flushPendingWrites === 'function') {
            await this.userManager.flushPendingWrites();
        }

        // 打印最终统计
        this.printStats();

        console.log('✅ Bot已停止');
    }
}

// ==================== 主程序入口 ====================

if (require.main === module) {
    // 创建Bot实例
    const bot = new PolymarketSignalBot(config);

    // 启动Bot
    bot.start().catch(error => {
        console.error('❌ 启动失败:', error);
        process.exit(1);
    });

    // 优雅退出
    let shuttingDown = false;

    const gracefulExit = (code) => {
        if (shuttingDown) {
            return;
        }
        shuttingDown = true;
        bot.stop().finally(() => process.exit(code));
    };

    process.on('SIGINT', () => {
        console.log('\n\n收到退出信号...');
        gracefulExit(0);
    });

    process.on('SIGTERM', () => {
        console.log('\n\n收到终止信号...');
        gracefulExit(0);
    });

    // 未捕获异常处理
    process.on('uncaughtException', (error) => {
        console.error('❌ 未捕获的异常:', error);
        gracefulExit(1);
    });

    process.on('unhandledRejection', (reason, promise) => {
        console.error('❌ 未处理的Promise拒绝:', reason);
    });
}

module.exports = PolymarketSignalBot;
