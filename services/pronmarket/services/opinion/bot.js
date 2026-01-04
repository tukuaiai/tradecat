/**
 * Opinion 信号检测 Bot - 主程序
 * 
 * 数据源: Opinion WebSocket + REST API
 */

// 强制全局代理
process.env.GLOBAL_AGENT_HTTP_PROXY = 'http://127.0.0.1:9910';
process.env.GLOBAL_AGENT_HTTPS_PROXY = 'http://127.0.0.1:9910';
require('dotenv').config();
const { bootstrap } = require('global-agent');
bootstrap();

const config = require('./config/settings');
const OpinionWebSocket = require('./clients/opinion-ws');
const OpinionRestClient = require('./clients/opinion-rest');
const TelegramBot = require('node-telegram-bot-api');

// 信号检测模块
const ArbitrageDetector = require('./signals/arbitrage/detector');
const OrderbookDetector = require('./signals/orderbook/detector');
const LargeTradeDetector = require('./signals/whale/detector');
const NewMarketDetector = require('./signals/new-market/detector');

// 消息格式化器
const { formatArbitrageSignal } = require('./signals/arbitrage/formatter');
const { formatOrderbookSignal } = require('./signals/orderbook/formatter');
const { formatLargeTradeSignal } = require('./signals/whale/formatter');
const { formatNewMarketSignal } = require('./signals/new-market/formatter');

// 工具
const { getTelegramBotOptions } = require('./utils/proxyAgent');

// 翻译
const GoogleTranslationService = require('./translation/google-service-free');

const delay = (ms) => new Promise(r => setTimeout(r, ms));

class OpinionSignalBot {
    constructor() {
        this.ws = null;
        this.rest = null;
        this.telegram = null;
        this.translation = null;
        
        // 检测器
        this.arbitrageDetector = null;
        this.orderbookDetector = null;
        this.whaleDetector = null;
        this.newMarketDetector = null;
        
        // 市场数据缓存
        this.markets = new Map();        // marketId -> market info
        this.marketsByToken = new Map(); // tokenId -> marketId
        this.orderbooks = new Map();     // tokenId -> {bids, asks}
        this.prices = new Map();         // tokenId -> price
        
        // 统计
        this.stats = {
            startTime: Date.now(),
            messages: 0,
            signals: { arbitrage: 0, orderbook: 0, whale: 0, newMarket: 0 },
            errors: 0
        };
    }

    async start() {
        console.log('========================================');
        console.log('  Opinion 信号检测 Bot');
        console.log('========================================');
        console.log(`启动时间: ${new Date().toLocaleString()}`);
        console.log('');

        // 1. REST 客户端
        this.rest = new OpinionRestClient({
            host: config.opinion.host,
            apiKey: config.opinion.apiKey
        });

        // 2. 加载市场列表
        await this._loadMarkets();

        // 3. WebSocket 客户端
        this.ws = new OpinionWebSocket({
            apiKey: config.opinion.apiKey
        });
        this._bindWsEvents();

        // 4. Telegram Bot
        if (config.telegram.token) {
            this.telegram = new TelegramBot(config.telegram.token, getTelegramBotOptions());
            console.log('[Telegram] ✅ 已初始化');
        }

        // 5. 翻译服务
        if (config.translation.enabled) {
            this.translation = new GoogleTranslationService(config.translation);
            console.log('[翻译] ✅ 已初始化');
        }

        // 6. 信号检测器
        this._initDetectors();

        // 7. 连接 WebSocket
        this.ws.connect();

        // 8. 定时任务
        setInterval(() => this._loadMarkets(), 300000);  // 5分钟刷新市场
        setInterval(() => this._printStats(), 300000);   // 5分钟打印统计

        console.log('\n[Bot] ✅ 已启动\n');
    }

    async _loadMarkets() {
        try {
            const markets = await this.rest.getMarkets({ limit: 100 });
            const newMarketIds = [];

            for (const m of markets) {
                const isNew = !this.markets.has(m.marketId);
                
                this.markets.set(m.marketId, m);
                if (m.yesTokenId) this.marketsByToken.set(m.yesTokenId, m.marketId);
                if (m.noTokenId) this.marketsByToken.set(m.noTokenId, m.marketId);

                // 新市场检测
                if (isNew && this.newMarketDetector) {
                    const signal = this.newMarketDetector.process(m);
                    if (signal) {
                        await this._sendSignal('newMarket', signal, m);
                    }
                }

                newMarketIds.push(m.marketId);
            }

            // 订阅 WebSocket
            if (this.ws && this.ws.isConnected) {
                this.ws.subscribeMarkets(newMarketIds);
            }

            console.log(`[Markets] 加载 ${markets.length} 个市场`);
        } catch (e) {
            console.error('[Markets] 加载失败:', e.message);
        }
    }

    _initDetectors() {
        // 套利检测
        if (config.arbitrage.enabled) {
            this.arbitrageDetector = new ArbitrageDetector(config.arbitrage);
        }

        // 订单簿检测
        if (config.orderbook.enabled) {
            this.orderbookDetector = new OrderbookDetector(config.orderbook);
        }

        // 巨鲸检测
        if (config.largeTrade.enabled) {
            this.whaleDetector = new LargeTradeDetector(config.largeTrade);
        }

        // 新市场检测
        if (config.newMarket.enabled) {
            this.newMarketDetector = new NewMarketDetector(config.newMarket);
        }

        console.log('[检测器] 已初始化');
        console.log(`  套利: ${config.arbitrage.enabled ? '✅' : '❌'}`);
        console.log(`  订单簿: ${config.orderbook.enabled ? '✅' : '❌'}`);
        console.log(`  巨鲸: ${config.largeTrade.enabled ? '✅' : '❌'}`);
        console.log(`  新市场: ${config.newMarket.enabled ? '✅' : '❌'}`);
    }

    _bindWsEvents() {
        // 价格更新
        this.ws.on('price', (data) => {
            this.stats.messages++;
            this._onPrice(data);
        });

        // 订单簿更新
        this.ws.on('orderbook', (data) => {
            this.stats.messages++;
            this._onOrderbook(data);
        });

        // 成交记录
        this.ws.on('trade', (data) => {
            this.stats.messages++;
            this._onTrade(data);
        });

        this.ws.on('connected', () => {
            // 连接后订阅所有市场
            const ids = Array.from(this.markets.keys());
            this.ws.subscribeMarkets(ids);
        });

        this.ws.on('error', (e) => {
            this.stats.errors++;
        });
    }

    _onPrice(data) {
        const { tokenId, price, marketId, outcomeSide } = data;
        this.prices.set(tokenId, price);

        // 套利检测 - 适配 Opinion 格式
        if (this.arbitrageDetector) {
            const market = this.markets.get(marketId || this.marketsByToken.get(tokenId));
            if (!market) return;

            // 构造套利检测器期望的格式
            const message = {
                payload: {
                    asset: tokenId,
                    price: price,
                    // 模拟 price_change 格式
                    pc: [{ a: tokenId, ba: price.toString(), bb: price.toString() }]
                }
            };

            // 更新市场元数据
            this.arbitrageDetector.marketMetadata.set(market.marketId, {
                question: market.marketTitle,
                slug: market.slug
            });

            // 建立 token -> market 映射
            if (market.yesTokenId) {
                this.arbitrageDetector.marketTokenIndex.set(market.yesTokenId, {
                    market: market.marketId,
                    outcome: 'Yes'
                });
            }
            if (market.noTokenId) {
                this.arbitrageDetector.marketTokenIndex.set(market.noTokenId, {
                    market: market.marketId,
                    outcome: 'No'
                });
            }

            const signal = this.arbitrageDetector.processPrice(message);
            if (signal) {
                this._sendSignal('arbitrage', signal, market);
            }
        }
    }

    _onOrderbook(data) {
        const { tokenId, side, price, size, marketId } = data;
        
        // 更新本地订单簿
        if (!this.orderbooks.has(tokenId)) {
            this.orderbooks.set(tokenId, { bids: [], asks: [] });
        }
        const book = this.orderbooks.get(tokenId);
        
        // 更新单个价位
        const arr = side === 'bids' ? book.bids : book.asks;
        const idx = arr.findIndex(o => o.price === price);
        if (parseFloat(size) === 0) {
            if (idx >= 0) arr.splice(idx, 1);
        } else {
            if (idx >= 0) {
                arr[idx].size = size;
            } else {
                arr.push({ price, size });
            }
        }

        // 订单簿检测
        if (this.orderbookDetector && book.bids.length >= 1 && book.asks.length >= 1) {
            const market = this.markets.get(marketId) || 
                           this.markets.get(this.marketsByToken.get(tokenId));
            
            try {
                // 构造检测器期望的消息格式
                const message = {
                    payload: {
                        market: tokenId,
                        asset_id: tokenId,
                        marketName: market?.marketTitle,
                        bids: book.bids.map(b => ({ price: b.price, size: b.size })),
                        asks: book.asks.map(a => ({ price: a.price, size: a.size }))
                    }
                };
                
                const signal = this.orderbookDetector.processOrderbook(message);
                if (signal) {
                    this._sendSignal('orderbook', signal, market);
                }
            } catch (e) {
                // 忽略
            }
        }
    }

    _onTrade(data) {
        const { marketId, tokenId, side, price, shares, amount } = data;
        
        // 巨鲸检测
        if (this.whaleDetector) {
            const market = this.markets.get(marketId || this.marketsByToken.get(tokenId));
            
            const signal = this.whaleDetector.process({
                price: price,
                size: shares,
                side: side.toLowerCase(),
                timestamp: Date.now()
            }, {
                marketId: marketId,
                marketName: market?.marketTitle,
                tokenId: tokenId
            });
            
            if (signal) {
                this._sendSignal('whale', signal, market);
            }
        }
    }

    async _sendSignal(type, signal, market) {
        this.stats.signals[type]++;
        
        let message;
        try {
            switch (type) {
                case 'arbitrage':
                    message = formatArbitrageSignal(signal, config.arbitrage.messageVariant);
                    break;
                case 'orderbook':
                    message = formatOrderbookSignal(signal, config.orderbook.messageVariant);
                    break;
                case 'whale':
                    message = formatLargeTradeSignal(signal);
                    break;
                case 'newMarket':
                    const result = formatNewMarketSignal(signal);
                    message = typeof result === 'string' ? result : result.text;
                    break;
            }
        } catch (e) {
            console.error(`[${type}] 格式化失败:`, e.message);
            return;
        }

        if (!message) return;

        // 翻译
        if (this.translation && market?.marketTitle) {
            try {
                const translated = await this.translation.translate(market.marketTitle);
                if (translated && translated !== market.marketTitle) {
                    message = message.replace(market.marketTitle, `${market.marketTitle}\n📝 ${translated}`);
                }
            } catch (e) {}
        }

        // 发送 Telegram
        await this._sendTelegram(message);
        console.log(`[${type}] 信号已发送`);
    }

    async _sendTelegram(message) {
        if (!this.telegram || !config.telegram.chatId) {
            if (config.debug.enabled) {
                console.log('[TG] (dry-run)', message.substring(0, 80) + '...');
            }
            return;
        }

        try {
            await this.telegram.sendMessage(config.telegram.chatId, message, {
                parse_mode: 'Markdown',
                disable_notification: config.telegram.disableNotification
            });
        } catch (e) {
            if (e.response?.statusCode === 429) {
                const wait = e.response.body?.parameters?.retry_after || 5;
                await delay(wait * 1000);
                await this.telegram.sendMessage(config.telegram.chatId, message, { parse_mode: 'Markdown' });
            } else {
                console.error('[TG] 发送失败:', e.message);
            }
        }
    }

    _printStats() {
        const uptime = Math.floor((Date.now() - this.stats.startTime) / 60000);
        console.log('\n========== 统计 ==========');
        console.log(`运行: ${uptime}分钟 | 消息: ${this.stats.messages} | 错误: ${this.stats.errors}`);
        console.log(`信号: 套利=${this.stats.signals.arbitrage} 订单簿=${this.stats.signals.orderbook} 巨鲸=${this.stats.signals.whale} 新市场=${this.stats.signals.newMarket}`);
        console.log('==========================\n');
    }

    async stop() {
        console.log('[Bot] 正在停止...');
        if (this.ws) this.ws.disconnect();
        if (this.translation?.saveCache) await this.translation.saveCache();
        console.log('[Bot] 已停止');
    }
}

// 主入口
const bot = new OpinionSignalBot();

process.on('SIGINT', async () => { await bot.stop(); process.exit(0); });
process.on('SIGTERM', async () => { await bot.stop(); process.exit(0); });

bot.start().catch(e => {
    console.error('[启动失败]', e);
    process.exit(1);
});

module.exports = OpinionSignalBot;
