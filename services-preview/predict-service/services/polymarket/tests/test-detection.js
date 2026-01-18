/**
 * 订阅请求体格式回归测试（离线）
 *
 * 验证订单簿订阅的 filters 以数组形式发送，避免字符串化导致的
 * "Invalid request body"（Issue #18）。
 */

const assert = require('assert');
const PolymarketSignalBot = require('../bot');
const config = require('../config/settings');

// 构造干净的 Bot 实例，不调用 start() 避免网络依赖
const bot = new PolymarketSignalBot(config);

// 注入最小可用的订单簿模块与 WebSocket 客户端桩
bot.modules.orderbook = {};  // 只需存在即可通过订阅分支

const sentSubscriptions = [];
bot.wsClient = {
    subscribe: (msg) => sentSubscriptions.push(msg),
    unsubscribe: () => {}
};

// 准备激活的 token 集合
bot.activeTokens.add('101');
bot.activeTokens.add('202');

// 触发订阅（强制刷新以覆盖无订阅场景）
bot.subscribeOrderbook({ force: true });

// 断言 filters 为数组而非字符串
assert(Array.isArray(bot.lastOrderbookFilters[0]), 'filters 应为数组');
assert.strictEqual(
    typeof bot.lastOrderbookFilters[0],
    'object',
    'filters 不应序列化为字符串'
);

// 断言发送的订阅消息与缓存一致
assert(sentSubscriptions.length > 0, '应发送至少一条订阅消息');
const firstFilters = sentSubscriptions[0].subscriptions[0].filters;
assert(Array.isArray(firstFilters), '发送到 WS 的 filters 必须是数组');
assert.deepStrictEqual(
    new Set(firstFilters),
    new Set(bot.lastOrderbookFilters.flat()),
    '发送的 filters 与缓存不一致'
);

console.log('✅ filters 数组格式测试通过');
