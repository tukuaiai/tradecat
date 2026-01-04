/**
 * Market Data Fetcher
 *
 * 从 CLOB API 获取市场元数据（slug等）
 */

const https = require('https');

const REQUEST_TIMEOUT_MS = 3000;
const CACHE_TTL_MS = 30 * 60 * 1000;  // 30分钟
const CACHE_MAX_SIZE = 200000;         // 20万条

class MarketDataFetcher {
    constructor() {
        // 市场数据缓存：conditionId -> {slug, eventSlug, ...}
        this.cache = new Map();

        // 正在请求的promises（避免重复请求）
        this.pending = new Map();

        console.log('✅ 市场数据获取器初始化完成');

        this.requestTimeoutMs = REQUEST_TIMEOUT_MS;
        this.cacheTTL = CACHE_TTL_MS;
        this.cacheMaxSize = CACHE_MAX_SIZE;
    }

    /**
     * 获取市场slug
     * @param {string} conditionId - 市场的conditionId
     * @returns {Promise<string|null>} - 市场slug或null
     */
    async getMarketSlug(conditionId) {
        try {
            const cached = await this.ensureMarketData(conditionId);
            return cached ? cached.slug || null : null;

        } catch (error) {
            console.error(`❌ 获取市场slug失败 (${conditionId.substring(0, 12)}...):`, error.message);
            return null;
        }
    }

    /**
     * 获取市场名称（问题）
     * @param {string} conditionId - 市场的conditionId
     * @returns {Promise<string|null>} - 市场名称或null
     */
    async getMarketName(conditionId) {
        try {
            const cached = await this.ensureMarketData(conditionId);
            return cached ? cached.question || null : null;

        } catch (error) {
            console.error(`❌ 获取市场名称失败 (${conditionId.substring(0, 12)}...):`, error.message);
            return null;
        }
    }

    async ensureMarketData(conditionId) {
        const cached = this.cache.get(conditionId);
        if (cached && Date.now() - cached.fetched < this.cacheTTL) {
            return cached;
        }

        if (!this.pending.has(conditionId)) {
            const fetchPromise = this.fetchMarketData(conditionId);
            this.pending.set(conditionId, fetchPromise);
        }

        try {
            await this.pending.get(conditionId);
        } finally {
            this.pending.delete(conditionId);
        }

        return this.cache.get(conditionId) || null;
    }

    /**
     * 从CLOB API获取市场数据
     * @param {string} conditionId
     * @returns {Promise<Object|null>}
     */
    fetchMarketData(conditionId) {
        return new Promise((resolve, reject) => {
            const url = `https://clob.polymarket.com/markets/${conditionId}`;
            const req = https.get(url, (res) => {
                let data = '';

                res.on('data', (chunk) => {
                    data += chunk;
                });

                res.on('end', () => {
                    try {
                        if (res.statusCode === 200) {
                            const marketData = JSON.parse(data);

                            // 容量限制：超过时清理最旧的 10%
                            if (this.cache.size >= this.cacheMaxSize) {
                                const toDelete = Math.floor(this.cacheMaxSize * 0.1);
                                const keys = Array.from(this.cache.keys()).slice(0, toDelete);
                                keys.forEach(k => this.cache.delete(k));
                            }

                            // 缓存数据（注意：字段名是market_slug，不是slug）
                            this.cache.set(conditionId, {
                                slug: marketData.market_slug,
                                eventSlug: marketData.event_slug,
                                question: marketData.question,
                                description: marketData.description,
                                clob_token_ids: marketData.clob_token_ids,
                                fetched: Date.now()
                            });

                            if (process.env.DEBUG === 'true') {
                                console.debug(`✅ 获取市场数据: ${conditionId.substring(0, 12)}... -> ${marketData.market_slug}`);
                            }
                            resolve(marketData);
                        } else {
                            console.warn(`⚠️ CLOB API返回 ${res.statusCode}: ${conditionId.substring(0, 12)}...`);
                            resolve(null);
                        }
                    } catch (error) {
                        console.error(`❌ 解析市场数据失败:`, error.message);
                        resolve(null);
                    }
                });

                res.on('error', (error) => {
                    reject(error);
                });
            });

            req.setTimeout(this.requestTimeoutMs, () => {
                req.destroy(new Error('Market data request timed out'));
            });

            req.on('error', (error) => {
                console.error(`❌ CLOB API请求失败:`, error.message);
                reject(error);
            });
        });
    }

    /**
     * 获取事件slug（用于构建URL）
     * @param {string} conditionId - 市场的conditionId
     * @returns {Promise<string|null>} - 事件slug或null
     */
    async getEventSlug(conditionId) {
        try {
            const cached = await this.ensureMarketData(conditionId);
            if (!cached) {
                return null;
            }

            return cached.eventSlug || cached.slug || null;

        } catch (error) {
            console.error(`❌ 获取事件slug失败 (${conditionId.substring(0, 12)}...):`, error.message);
            return null;
        }
    }

    /**
     * 构建Polymarket市场URL
     * @param {string} conditionId
     * @returns {Promise<string>}
     */
    async buildMarketUrl(conditionId) {
        // 使用 eventSlug（而不是 market_slug）来构建 URL
        const slug = await this.getEventSlug(conditionId);

        if (slug) {
            return `https://polymarket.com/event/${slug}`;
        }

        // 如果无法获取slug，降级使用conditionId（虽然可能无效）
        return `https://polymarket.com/event/${conditionId}`;
    }

    /**
     * 从 Gamma API 获取市场详情（流动性、成交量等）
     * @param {string} conditionId
     * @returns {Promise<{liquidity: number, volume: number, volume24hr: number}|null>}
     */
    async getMarketDetails(conditionId) {
        const cacheKey = `details_${conditionId}`;
        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.fetched < this.cacheTTL) {
            return cached.details;
        }

        try {
            const fetch = require('node-fetch');
            // 先尝试 condition_id，再尝试 clob_token_ids
            let res = await fetch(`https://gamma-api.polymarket.com/markets?condition_id=${conditionId}`, {
                timeout: this.requestTimeoutMs
            });
            let markets = res.ok ? await res.json() : [];
            
            // 如果没找到，尝试用 clob_token_ids 查询
            if (!markets || !markets.length) {
                res = await fetch(`https://gamma-api.polymarket.com/markets?clob_token_ids=${conditionId}`, {
                    timeout: this.requestTimeoutMs
                });
                markets = res.ok ? await res.json() : [];
            }
            
            if (!markets || !markets.length) return null;
            
            const m = markets[0];
            const details = {
                liquidity: Number(m.liquidity) || 0,
                volume: Number(m.volume) || 0,
                volume24hr: Number(m.volume24hr) || 0
            };
            
            this.cache.set(cacheKey, { details, fetched: Date.now() });
            return details;
        } catch (e) {
            return null;
        }
    }

    /**
     * 获取缓存统计
     */
    getStats() {
        return {
            cached: this.cache.size,
            pending: this.pending.size
        };
    }
}

// 单例
const marketDataFetcher = new MarketDataFetcher();

module.exports = marketDataFetcher;
