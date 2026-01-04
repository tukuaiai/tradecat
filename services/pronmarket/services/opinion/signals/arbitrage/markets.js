/**
 * 市场配对管理器
 *
 * 功能：管理 YES/NO token 的对应关系
 */

class MarketPairManager {
    constructor() {
        // 存储 market -> {yes: tokenId, no: tokenId} 映射
        this.pairs = new Map();

        // 存储 tokenId -> market 的反向映射
        this.tokenToMarket = new Map();

        // 存储市场的额外信息
        this.marketInfo = new Map();
    }

    /**
     * 注册市场配对
     * @param {string} market - 市场ID
     * @param {string} yesToken - YES token ID
     * @param {string} noToken - NO token ID
     * @param {Object} info - 市场额外信息（可选）
     */
    registerPair(market, yesToken, noToken, info = {}) {
        this.pairs.set(market, {
            yes: yesToken,
            no: noToken,
            registered: Date.now(),
            complete: !!(yesToken && noToken)
        });

        // 更新反向映射
        if (yesToken) {
            this.tokenToMarket.set(yesToken, { market, outcome: 'YES' });
        }
        if (noToken) {
            this.tokenToMarket.set(noToken, { market, outcome: 'NO' });
        }

        // 存储市场信息
        if (info.name || info.description) {
            this.marketInfo.set(market, {
                ...info,
                updated: Date.now()
            });
        }

        if (yesToken && noToken) {
            console.log(`✅ 注册完整市场配对: ${info.name || market.substring(0, 20)}`);
            console.log(`   YES: ${yesToken.substring(0, 12)}...`);
            console.log(`   NO:  ${noToken.substring(0, 12)}...`);
        }
    }

    /**
     * 获取市场配对
     * @param {string} market - 市场ID
     * @returns {Object|null} - {yes: tokenId, no: tokenId}
     */
    getPair(market) {
        return this.pairs.get(market);
    }

    /**
     * 通过token ID获取市场
     * @param {string} tokenId - Token ID
     * @returns {Object|null} - {market: marketId, outcome: 'YES'|'NO'}
     */
    getMarketByToken(tokenId) {
        return this.tokenToMarket.get(tokenId);
    }

    /**
     * 检查市场配对是否完整
     * @param {string} market - 市场ID
     * @returns {boolean}
     */
    isPairComplete(market) {
        const pair = this.pairs.get(market);
        return !!(pair && pair.yes && pair.no);
    }

    /**
     * 从 WebSocket 消息自动识别配对
     * @param {Object} message - WebSocket 消息
     */
    autoDetectPair(message) {
        try {
            const payload = message.payload;

            // 提取关键信息
            const market = payload.market || payload.condition_id;
            const tokenId = payload.token_id || payload.tokenId;
            const outcome = payload.outcome;

            if (!market || !tokenId) {
                return;
            }

            // 如果市场不存在，创建新记录
            if (!this.pairs.has(market)) {
                this.pairs.set(market, {
                    yes: null,
                    no: null,
                    discovered: Date.now()
                });
            }

            const pair = this.pairs.get(market);

            // 根据outcome更新配对
            if (outcome === 'YES' || outcome === 'yes' || outcome === '1') {
                pair.yes = tokenId;
                this.tokenToMarket.set(tokenId, { market, outcome: 'YES' });
            } else if (outcome === 'NO' || outcome === 'no' || outcome === '0') {
                pair.no = tokenId;
                this.tokenToMarket.set(tokenId, { market, outcome: 'NO' });
            }

            // 如果两个都有了，标记为完整
            if (pair.yes && pair.no && !pair.complete) {
                pair.complete = true;
                pair.completed = Date.now();
                console.log(`🎯 市场配对完整: ${market.substring(0, 20)}...`);
            }

        } catch (error) {
            console.error('❌ 自动识别配对失败:', error.message);
        }
    }

    /**
     * 更新市场信息
     * @param {string} market - 市场ID
     * @param {Object} info - 市场信息 {name, description, ...}
     */
    updateMarketInfo(market, info) {
        const existing = this.marketInfo.get(market) || {};
        this.marketInfo.set(market, {
            ...existing,
            ...info,
            updated: Date.now()
        });
    }

    /**
     * 获取市场信息
     * @param {string} market - 市场ID
     * @returns {Object|null}
     */
    getMarketInfo(market) {
        return this.marketInfo.get(market);
    }

    /**
     * 获取所有完整的配对
     * @returns {Array} - [{market, yes, no, info}]
     */
    getCompletePairs() {
        const result = [];

        for (const [market, pair] of this.pairs.entries()) {
            if (pair.yes && pair.no) {
                const info = this.marketInfo.get(market);
                result.push({
                    market,
                    yesToken: pair.yes,
                    noToken: pair.no,
                    info: info || {},
                    registered: pair.registered,
                    completed: pair.completed
                });
            }
        }

        return result;
    }

    /**
     * 获取所有配对（包括不完整的）
     * @returns {Array}
     */
    getAllPairs() {
        return Array.from(this.pairs.entries()).map(([market, pair]) => {
            const info = this.marketInfo.get(market);
            return {
                market,
                yesToken: pair.yes,
                noToken: pair.no,
                complete: !!(pair.yes && pair.no),
                info: info || {},
                registered: pair.registered
            };
        });
    }

    /**
     * 获取统计信息
     */
    getStats() {
        const completePairs = this.getCompletePairs();
        const allPairs = this.getAllPairs();

        return {
            totalMarkets: this.pairs.size,
            completePairs: completePairs.length,
            incompletePairs: allPairs.length - completePairs.length,
            totalTokens: this.tokenToMarket.size,
            marketsWithInfo: this.marketInfo.size
        };
    }

    /**
     * 清理过期数据
     * @param {number} maxAge - 最大保留时间（毫秒）
     */
    cleanup(maxAge = 86400000) {
        const now = Date.now();
        let removed = 0;

        // 清理不完整且过期的配对
        for (const [market, pair] of this.pairs.entries()) {
            if (!pair.complete && (now - pair.discovered > maxAge)) {
                this.pairs.delete(market);
                this.marketInfo.delete(market);
                removed++;
            }
        }

        if (removed > 0) {
            console.log(`🧹 清理了 ${removed} 个不完整的市场配对`);
        }
    }

    /**
     * 导出配对数据（用于调试或持久化）
     */
    exportPairs() {
        return {
            pairs: Array.from(this.pairs.entries()),
            tokenMapping: Array.from(this.tokenToMarket.entries()),
            marketInfo: Array.from(this.marketInfo.entries()),
            exported: Date.now()
        };
    }

    /**
     * 导入配对数据
     */
    importPairs(data) {
        if (data.pairs) {
            this.pairs = new Map(data.pairs);
        }
        if (data.tokenMapping) {
            this.tokenToMarket = new Map(data.tokenMapping);
        }
        if (data.marketInfo) {
            this.marketInfo = new Map(data.marketInfo);
        }

        console.log(`📥 导入了 ${this.pairs.size} 个市场配对`);
    }
}

module.exports = MarketPairManager;
