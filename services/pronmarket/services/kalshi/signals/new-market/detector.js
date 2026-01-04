/**
 * 新市场检测模块
 * 
 * 定期扫描 Kalshi 新上线的市场
 */

const config = require('../../config/settings');

class NewMarketDetector {
  constructor(kalshiClient) {
    this.client = kalshiClient;
    this.knownMarkets = new Set();
    this.initialized = false;
    this.onSignal = null;
  }

  // 初始化：加载现有市场
  async init() {
    console.log('[NewMarket] 初始化，加载现有市场...');
    try {
      let cursor = null;
      do {
        const { markets, cursor: nextCursor } = await this.client.getMarkets({
          limit: 1000,
          status: 'open',
          cursor
        });
        markets.forEach(m => this.knownMarkets.add(m.ticker));
        cursor = nextCursor;
      } while (cursor);
      
      console.log(`[NewMarket] 已加载 ${this.knownMarkets.size} 个市场`);
      this.initialized = true;
    } catch (err) {
      console.error('[NewMarket] 初始化失败:', err.message);
    }
  }

  // 扫描新市场
  async scan() {
    if (!this.initialized) return [];
    
    const newMarkets = [];
    try {
      const { markets } = await this.client.getMarkets({
        limit: config.newMarket.limit,
        status: 'open'
      });
      
      for (const market of markets) {
        if (!this.knownMarkets.has(market.ticker)) {
          this.knownMarkets.add(market.ticker);
          newMarkets.push(market);
          
          if (this.onSignal) {
            this.onSignal({
              type: 'new-market',
              market,
              timestamp: Date.now()
            });
          }
        }
      }
      
      if (newMarkets.length > 0) {
        console.log(`[NewMarket] 发现 ${newMarkets.length} 个新市场`);
      }
    } catch (err) {
      console.error('[NewMarket] 扫描失败:', err.message);
    }
    
    return newMarkets;
  }

  // 启动定时扫描
  start() {
    if (!config.newMarket.enabled) {
      console.log('[NewMarket] 模块已禁用');
      return;
    }
    
    this.init().then(() => {
      this.timer = setInterval(() => this.scan(), config.newMarket.scanIntervalMs);
      console.log(`[NewMarket] 已启动，扫描间隔 ${config.newMarket.scanIntervalMs / 1000}s`);
    });
  }

  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }
}

module.exports = NewMarketDetector;
