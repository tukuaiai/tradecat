/**
 * 价格突变检测模块
 * 
 * 检测短时间内价格剧烈波动
 */

const config = require('../../config/settings');

class PriceSpikeDetector {
  constructor(kalshiClient) {
    this.client = kalshiClient;
    this.priceHistory = new Map(); // ticker -> [{price, timestamp}]
    this.cooldowns = new Map();
    this.onSignal = null;
  }

  // 记录价格
  recordPrice(ticker, price) {
    if (!this.priceHistory.has(ticker)) {
      this.priceHistory.set(ticker, []);
    }
    
    const history = this.priceHistory.get(ticker);
    history.push({ price, timestamp: Date.now() });
    
    // 只保留窗口内的数据
    const cutoff = Date.now() - config.priceSpike.timeWindowMs;
    while (history.length > 0 && history[0].timestamp < cutoff) {
      history.shift();
    }
  }

  // 检测价格突变
  detectSpike(ticker, currentPrice) {
    const history = this.priceHistory.get(ticker);
    if (!history || history.length < 2) return null;
    
    // 冷却检查
    const lastSignal = this.cooldowns.get(ticker);
    if (lastSignal && Date.now() - lastSignal < config.priceSpike.cooldown) {
      return null;
    }
    
    // 计算窗口内的价格变化
    const oldestPrice = history[0].price;
    const change = Math.abs(currentPrice - oldestPrice) / oldestPrice;
    
    if (change >= config.priceSpike.minChange) {
      this.cooldowns.set(ticker, Date.now());
      
      return {
        type: 'price-spike',
        ticker,
        oldPrice: oldestPrice,
        newPrice: currentPrice,
        change,
        direction: currentPrice > oldestPrice ? 'up' : 'down',
        timestamp: Date.now()
      };
    }
    
    return null;
  }

  // 扫描所有市场
  async scan() {
    try {
      const { markets } = await this.client.getMarkets({ limit: 200, status: 'open' });
      const signals = [];
      
      for (const market of markets) {
        const price = (market.last_price || market.yes_bid || 0) / 100;
        if (price <= 0) continue;
        
        // 记录价格
        this.recordPrice(market.ticker, price);
        
        // 检测突变
        const signal = this.detectSpike(market.ticker, price);
        if (signal) {
          signal.market = market;
          signals.push(signal);
          
          if (this.onSignal) {
            this.onSignal(signal);
          }
        }
      }
      
      if (signals.length > 0) {
        console.log(`[PriceSpike] 发现 ${signals.length} 个价格突变`);
      }
      
      return signals;
    } catch (err) {
      console.error('[PriceSpike] 扫描失败:', err.message);
      return [];
    }
  }

  // 启动定时扫描
  start() {
    if (!config.priceSpike.enabled) {
      console.log('[PriceSpike] 模块已禁用');
      return;
    }

    console.log('[PriceSpike] 模块已启动');
    
    // 定时扫描（30秒一次）
    this.timer = setInterval(() => this.scan(), 30000);
  }

  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }
}

module.exports = PriceSpikeDetector;
