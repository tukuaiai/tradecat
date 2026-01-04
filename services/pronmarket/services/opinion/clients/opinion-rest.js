/**
 * Opinion API 客户端 (REST)
 * 
 * 市场列表、订单簿快照、价格历史
 */

const fetch = require('node-fetch');

class OpinionRestClient {
    constructor(options = {}) {
        this.host = options.host || process.env.OPINION_HOST || 'https://proxy.opinion.trade:8443';
        this.apiKey = options.apiKey || process.env.OPINION_API_KEY || '';
        
        // 缓存
        this.marketsCache = null;
        this.marketsCacheTime = 0;
        this.marketsCacheTTL = options.marketsCacheTTL || 60000; // 1分钟
    }

    async request(endpoint, params = {}) {
        const url = new URL(`${this.host}${endpoint}`);
        Object.entries(params).forEach(([k, v]) => {
            if (v !== undefined && v !== null) url.searchParams.append(k, v);
        });

        const response = await fetch(url.toString(), {
            method: 'GET',
            headers: { 'apikey': this.apiKey },
            timeout: 15000
        });

        if (!response.ok) {
            throw new Error(`Opinion API: ${response.status}`);
        }

        const data = await response.json();
        if (data.code !== 0 && data.errno !== 0) {
            throw new Error(data.msg || data.errmsg);
        }

        return data.result;
    }

    /**
     * 获取所有活跃市场
     */
    async getMarkets(options = {}) {
        const { status = 'activated', sortBy = 5, limit = 100, useCache = true } = options;
        
        if (useCache && this.marketsCache && Date.now() - this.marketsCacheTime < this.marketsCacheTTL) {
            return this.marketsCache;
        }

        const result = await this.request('/openapi/market', { status, sortBy, limit });
        const markets = result.list || [];
        
        this.marketsCache = markets;
        this.marketsCacheTime = Date.now();
        
        return markets;
    }

    /**
     * 获取单个市场
     */
    async getMarket(marketId) {
        const result = await this.request(`/openapi/market/${marketId}`);
        return result.data || result;
    }

    /**
     * 获取订单簿快照
     */
    async getOrderbook(tokenId) {
        const result = await this.request('/openapi/token/orderbook', { token_id: tokenId });
        return result.data || result;
    }

    /**
     * 获取最新价格
     */
    async getLatestPrice(tokenId) {
        return await this.request('/openapi/token/latest-price', { token_id: tokenId });
    }

    /**
     * 获取价格历史
     */
    async getPriceHistory(tokenId, interval = '1h') {
        const result = await this.request('/openapi/token/price-history', { token_id: tokenId, interval });
        return result.history || [];
    }
}

module.exports = OpinionRestClient;
