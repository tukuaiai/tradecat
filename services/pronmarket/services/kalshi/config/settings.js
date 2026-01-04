/**
 * Kalshi Bot 配置文件
 * 
 * 包含所有模块的配置选项
 */

const path = require('path');
const dotenvPath = process.env.DOTENV_CONFIG_PATH || path.join(__dirname, '../.env');
require('dotenv').config({ path: dotenvPath });

module.exports = {
  // ==================== Kalshi API ====================
  kalshi: {
    // REST API
    baseUrl: process.env.KALSHI_API_URL || 'https://api.elections.kalshi.com/trade-api/v2',
    
    // WebSocket
    wsUrl: process.env.KALSHI_WS_URL || 'wss://api.elections.kalshi.com',
    
    // 认证
    apiKeyId: process.env.KALSHI_API_KEY_ID || '',
    privateKeyPath: process.env.KALSHI_PRIVATE_KEY_PATH || '',
    
    // 连接配置
    pingInterval: 30000,
    autoReconnect: true,
    maxReconnectAttempts: 0,  // 0 = 无限重试
    reconnectDelayMs: 1000,
    reconnectDelayMaxMs: 30000,
    
    // 请求配置
    requestTimeout: 15000,
    retryAttempts: 3,
    retryDelay: 1000
  },

  // ==================== Telegram Bot ====================
  telegram: {
    token: process.env.TELEGRAM_BOT_TOKEN || '',
    chatId: process.env.TELEGRAM_CHAT_ID || '',
    parseMode: 'Markdown',
    disableNotification: false
  },

  // ==================== 模块1：价格套利检测 ====================
  // Kalshi 是二元市场，YES + NO = $1，套利空间较小
  arbitrage: {
    enabled: true,
    minProfit: 0.005,           // 最低净利润 0.5%（Kalshi 费率较高）
    tradingFee: 0.07,           // 交易费 7%（Kalshi 标准费率）
    minDepth: 50,               // 最小深度 $50
    cooldown: 60000,
    maxSignalsPerHour: 100
  },

  // ==================== 模块2：订单簿失衡检测 ====================
  orderbook: {
    enabled: true,
    minImbalance: 1.5,          // 最低失衡比例 1.5x
    minDepth: 20,               // 最小深度 $20
    depthLevels: 5,             // 计算前5档
    cooldown: 60000,
    maxSignalsPerHour: 100,
    scanIntervalMs: 30000       // 30秒扫描一次
  },

  // ==================== 模块3：扫尾盘信号 ====================
  closing: {
    enabled: true,
    timeWindowHours: 168,       // 7天窗口
    highConfidenceHours: 2,
    mediumConfidenceHours: 12,
    minVolume: 5000,            // 最低成交量 $5k
    minLiquidity: 2000,
    maxMarkets: 50,
    pageSize: 10,
    refreshIntervalMs: 300000   // 5分钟刷新
  },

  // ==================== 模块4：大额交易检测 ====================
  largeTrade: {
    enabled: true,
    minValue: 1000,             // 最低金额 $1000（Kalshi 单笔较小）
    cooldown: 30000,
    thresholds: {
      1: 500,
      2: 1000,
      3: 5000
    }
  },

  // ==================== 模块5：新市场检测 ====================
  newMarket: {
    enabled: true,
    scanIntervalMs: 60000,
    limit: 200
  },

  // ==================== 模块6：价格突变检测 ====================
  priceSpike: {
    enabled: true,
    minChange: 0.10,            // 最小变化 10%
    timeWindowMs: 300000,       // 5分钟窗口
    cooldown: 60000
  },

  // ==================== 日志配置 ====================
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    enableColors: true,
    logToFile: false
  },

  // ==================== 性能配置 ====================
  performance: {
    cleanupInterval: 3600000,
    maxCacheSize: 5000,
    statsInterval: 300000
  },

  // ==================== 调试选项 ====================
  debug: {
    enabled: process.env.DEBUG === 'true',
    logAllMessages: false,
    dryRun: false
  },

  // ==================== 翻译配置 ====================
  translation: {
    enabled: true,
    google: {
      projectId: process.env.GOOGLE_CLOUD_PROJECT,
      keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS,
      timeout: 20000
    },
    sourceLang: 'en',
    targetLang: 'zh-CN',
    cache: {
      enabled: true,
      maxSize: 5000,
      persistToDisk: true,
      filePath: './data/translation-cache.json'
    }
  }
};
