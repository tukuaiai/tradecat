/**
 * Opinion API 客户端
 * 
 * 封装 Opinion Open API，提供市场数据、订单簿、价格等接口
 */

const fetch = require('node-fetch');
const EventEmitter = require('events');

class OpinionClient extends EventEmitter {
    constructor(options = {}) {
        super();
        this.host = options.host || process.env.OPINION_HOST || 'https://proxy.opinion.trade:8443';
        this.apiKey = options.apiKey || process.env.OPINION_API_KEY || '';
        this.chainId = options.chainId || Number(process.env.OPINION_CHAIN_ID) || 56;
        
        // 缓存
        this.marketsCache = new Map();
        this.marketsCacheTime = 0;
        this.marketsCacheTTL = options.marketsCacheTTL || 300000; // 5分钟
        
        // 轮询配置
        this.pollInterval = options.pollInterval || 5000; // 5秒
        this.pollTimer = null;
        this.isPolling = false;
        
        // 订阅的 token
        this.subscribedTokens = new Set();
    }

    /**
     * 通用 API 请求
     */
    async request(endpoint, params = {}) {
        const url = new URL(`${this.host}${endpoint}`);
        Object.entries(params).forEach(([k, v]) => {
            if (v !== undefined && v !== null) url.searchParams.append(k, v);
        });

        const response = await fetch(url.toString(), {
            method: 'GET',
            headers: {
                'apikey': this.apiKey,
                'Content-Type': 'application/json'
            },
            timeout: 15000
        });

        if (!response.ok) {
            throw new Error(`Opinion API error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        if (data.code !== 0 && data.errno !== 0) {
            throw new Error(`Opinion API error: ${data.msg || data.errmsg}`);
        }

        return data.result;
    }

    /**
     * 获取所有活跃市场
     */
    async getMarkets(options = {}) {
        const { status = 'activated', sortBy = 5, limit = 100, page = 1, useCache = true } = options;
        
        // 检查缓存
        if (useCache && this.marketsCache.size > 0 && Date.now() - this.marketsCacheTime < this.marketsCacheTTL) {
            return Array.from(this.marketsCache.values());
        }

        const result = await this.request('/openapi/market', { status, sortBy, limit, page });
        const markets = result.list || [];
        
        // 更新缓存
        this.marketsCache.clear();
        markets.forEach(m => this.marketsCache.set(m.marketId, m));
        this.marketsCacheTime = Date.now();
        
        return markets;
    }

    /**
     * 获取单个市场详情
     */
    async getMarket(marketId) {
        const result = await this.request(`/openapi/market/${marketId}`);
        return result.data || result;
    }

    /**
     * 获取订单簿
     */
    async getOrderbook(tokenId) {
        const result = await this.request('/openapi/token/orderbook', { token_id: tokenId });
        return result.data || result;
    }

    /**
     * 获取最新价格
     */
    async getLatestPrice(tokenId) {
        const result = await this.request('/openapi/token/latest-price', { token_id: tokenId });
        return result;
    }

    /**
     * 获取价格历史
     */
    async getPriceHistory(tokenId, interval = '1h') {
        const result = await this.request('/openapi/token/price-history', { token_id: tokenId, interval });
        return result.history || [];
    }

    /**
     * 订阅 token（添加到轮询列表）
     */
    subscribeToken(tokenId) {
        this.subscribedTokens.add(tokenId);
    }

    /**
     * 批量订阅
     */
    subscribeTokens(tokenIds) {
        tokenIds.forEach(id => this.subscribedTokens.add(id));
    }

    /**
     * 取消订阅
     */
    unsubscribeToken(tokenId) {
        this.subscribedTokens.delete(tokenId);
    }

    /**
     * 启动轮询（模拟 WebSocket 实时数据）
     */
    startPolling() {
        if (this.isPolling) return;
        this.isPolling = true;
        
        console.log('[OpinionClient] 开始轮询市场数据...');
        this._poll();
    }

    /**
     * 停止轮询
     */
    stopPolling() {
        this.isPolling = false;
        if (this.pollTimer) {
            clearTimeout(this.pollTimer);
            this.pollTimer = null;
        }
        console.log('[OpinionClient] 停止轮询');
    }

    /**
     * 轮询逻辑
     */
    async _poll() {
        if (!this.isPolling) return;

        try {
            // 获取市场列表
            const markets = await this.getMarkets({ useCache: false });
            
            // 发射市场更新事件
            for (const market of markets) {
                this.emit('market', market);
                
                // 获取 YES/NO token 的订单簿
                if (market.yesTokenId) {
                    try {
                        const yesBook = await this.getOrderbook(market.yesTokenId);
                        this.emit('orderbook', {
                            tokenId: market.yesTokenId,
                            marketId: market.marketId,
                            side: 'YES',
                            ...yesBook
                        });
                    } catch (e) {
                        // 忽略单个订单簿错误
                    }
                }
                
                if (market.noTokenId) {
                    try {
                        const noBook = await this.getOrderbook(market.noTokenId);
                        this.emit('orderbook', {
                            tokenId: market.noTokenId,
                            marketId: market.marketId,
                            side: 'NO',
                            ...noBook
                        });
                    } catch (e) {
                        // 忽略单个订单簿错误
                    }
                }

                // 发射价格更新
                if (market.yesTokenId && market.noTokenId) {
                    this.emit('price', {
                        marketId: market.marketId,
                        marketTitle: market.marketTitle,
                        yesPrice: this._extractBestPrice(market, 'yes'),
                        noPrice: this._extractBestPrice(market, 'no'),
                        volume24h: market.volume24h,
                        timestamp: Date.now()
                    });
                }
            }

            this.emit('poll_complete', { marketsCount: markets.length });

        } catch (error) {
            console.error('[OpinionClient] 轮询错误:', error.message);
            this.emit('error', error);
        }

        // 下一次轮询
        this.pollTimer = setTimeout(() => this._poll(), this.pollInterval);
    }

    /**
     * 从市场数据提取最佳价格
     */
    _extractBestPrice(market, side) {
        // Opinion 市场数据结构可能包含价格信息
        if (side === 'yes') {
            return market.yesPrice || market.lastYesPrice || null;
        }
        return market.noPrice || market.lastNoPrice || null;
    }

    /**
     * 连接（启动轮询）
     */
    connect() {
        this.startPolling();
        this.emit('connected');
    }

    /**
     * 断开连接
     */
    disconnect() {
        this.stopPolling();
        this.emit('disconnected');
    }
}

module.exports = OpinionClient;
