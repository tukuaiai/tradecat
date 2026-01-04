/**
 * 订单簿失衡检测模块
 * 
 * 检测 YES/NO 买盘深度严重失衡的市场
 */

const config = require('../../config/settings');

class OrderbookDetector {
  constructor(kalshiClient) {
    this.client = kalshiClient;
    this.cooldowns = new Map();
    this.onSignal = null;
  }

  // 计算订单簿深度
  _calcDepth(orders) {
    if (!orders || !Array.isArray(orders)) return 0;
    // Kalshi 订单簿格式: [[price, quantity], ...]
    return orders.reduce((sum, [price, qty]) => sum + (qty * price / 100), 0);
  }

  // 检测单个市场
  async detectMarket(ticker) {
    // 冷却检查
    const lastSignal = this.cooldowns.get(ticker);
    if (lastSignal && Date.now() - lastSignal < config.orderbook.cooldown) {
      return null;
    }

    try {
      const { orderbook } = await this.client.getOrderbook(ticker, config.orderbook.depthLevels);
      
      const yesDepth = this._calcDepth(orderbook.yes_dollars || orderbook.yes);
      const noDepth = this._calcDepth(orderbook.no_dollars || orderbook.no);
      
      // 深度过低跳过
      if (yesDepth < config.orderbook.minDepth && noDepth < config.orderbook.minDepth) {
        return null;
      }
      
      // 计算失衡比例
      const imbalance = yesDepth > noDepth 
        ? yesDepth / (noDepth || 1) 
        : noDepth / (yesDepth || 1);
      
      if (imbalance >= config.orderbook.minImbalance) {
        this.cooldowns.set(ticker, Date.now());
        
        const signal = {
          type: 'orderbook-imbalance',
          ticker,
          yesDepth,
          noDepth,
          imbalance,
          direction: yesDepth > noDepth ? 'YES' : 'NO',
          timestamp: Date.now()
        };
        
        if (this.onSignal) {
          this.onSignal(signal);
        }
        
        return signal;
      }
    } catch (err) {
      // 静默处理单个市场错误
    }
    
    return null;
  }

  // 批量扫描
  async scan(tickers) {
    const signals = [];
    for (const ticker of tickers) {
      const signal = await this.detectMarket(ticker);
      if (signal) signals.push(signal);
      // 避免请求过快
      await new Promise(r => setTimeout(r, 100));
    }
    return signals;
  }

  // 启动定时扫描
  async start() {
    if (!config.orderbook.enabled) {
      console.log('[Orderbook] 模块已禁用');
      return;
    }

    console.log('[Orderbook] 模块已启动');
    
    const scanAll = async () => {
      try {
        const { markets } = await this.client.getMarkets({ limit: 200, status: 'open' });
        const tickers = markets.map(m => m.ticker);
        const signals = await this.scan(tickers);
        if (signals.length > 0) {
          console.log(`[Orderbook] 发现 ${signals.length} 个失衡信号`);
        }
      } catch (err) {
        console.error('[Orderbook] 扫描失败:', err.message);
      }
    };

    // 首次扫描
    await scanAll();
    
    // 定时扫描
    this.timer = setInterval(scanAll, config.orderbook.scanIntervalMs);
  }

  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }
}

module.exports = OrderbookDetector;
