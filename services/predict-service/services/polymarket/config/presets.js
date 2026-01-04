/**
 * 预设配置模板
 *
 * 提供多种检测阈值配置
 */

module.exports = {
    /**
     * 保守模式 - 只捕捉高质量信号
     */
    conservative: {
        arbitrage: {
            minProfit: 0.05,            // 5% 最低利润
            maxSignalsPerHour: 5,       // 每小时5条
            cooldown: 120000            // 2分钟冷却
        },
        orderbook: {
            minImbalance: 15,           // 15倍失衡
            minDepth: 2000,             // $2000 最小深度
            maxSignalsPerHour: 3,       // 每小时3条
            cooldown: 300000            // 5分钟冷却
        }
    },

    /**
     * 平衡模式 - 当前默认配置
     */
    balanced: {
        arbitrage: {
            minProfit: 0.03,            // 3% 最低利润
            maxSignalsPerHour: 10,      // 每小时10条
            cooldown: 60000             // 1分钟冷却
        },
        orderbook: {
            minImbalance: 10,           // 10倍失衡
            minDepth: 1000,             // $1000 最小深度
            maxSignalsPerHour: 15,      // 每小时15条
            cooldown: 120000            // 2分钟冷却
        }
    },

    /**
     * 激进模式 - 更多机会 ⭐ 推荐
     */
    aggressive: {
        arbitrage: {
            minProfit: 0.015,           // 1.5% 最低利润
            maxSignalsPerHour: 50,      // 每小时50条
            cooldown: 30000             // 30秒冷却
        },
        orderbook: {
            minImbalance: 3,            // 3倍失衡
            minDepth: 500,              // $500 最小深度
            maxSignalsPerHour: 100,     // 每小时100条
            cooldown: 60000             // 1分钟冷却
        }
    },

    /**
     * 最大模式 - 捕捉所有可能信号
     */
    maximum: {
        arbitrage: {
            minProfit: 0.005,           // 0.5% 最低利润
            maxSignalsPerHour: 999,     // 不限制
            cooldown: 10000             // 10秒冷却
        },
        orderbook: {
            minImbalance: 2,            // 2倍失衡
            minDepth: 100,              // $100 最小深度
            maxSignalsPerHour: 999,     // 不限制
            cooldown: 10000             // 10秒冷却
        }
    },

    /**
     * 测试模式 - 极低阈值，用于测试
     */
    test: {
        arbitrage: {
            minProfit: 0.001,           // 0.1% 最低利润
            maxSignalsPerHour: 9999,    // 不限制
            cooldown: 1000              // 1秒冷却
        },
        orderbook: {
            minImbalance: 1.1,          // 1.1倍失衡
            minDepth: 10,               // $10 最小深度
            maxSignalsPerHour: 9999,    // 不限制
            cooldown: 1000              // 1秒冷却
        }
    }
};
