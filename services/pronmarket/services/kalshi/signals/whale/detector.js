/**
 * 大额交易检测模块
 * 
 * 监控大额交易（巨鲸）
 */

const config = require('../../config/settings');

class WhaleDetector {
  constructor(kalshiClient) {
    this.client = kalshiClient;
    this.lastTradeId = null;
    this.cooldowns = new Map();
    this.onSignal = null;
  }

  // 扫描最新交易
  async scan() {
    try {
      const { trades } = await this.client.getTrades({ limit: 100 });
      
      const signals = [];
      
      for (const trade of trades) {
        // 跳过已处理的交易
        if (this.lastTradeId && trade.trade_id <= this.lastTradeId) break;
        
        // 计算交易金额（count * price / 100）
        const value = trade.count * (trade.yes_price || trade.price) / 100;
        
        if (value >= config.largeTrade.minValue) {
          // 冷却检查
          const key = `${trade.ticker}-${trade.taker_side}`;
          const lastSignal = this.cooldowns.get(key);
          if (lastSignal && Date.now() - lastSignal < config.largeTrade.cooldown) {
            continue;
          }
          this.cooldowns.set(key, Date.now());
          
          const signal = {
            type: 'whale',
            trade,
            value,
            ticker: trade.ticker,
            side: trade.taker_side,
            price: (trade.yes_price || trade.price) / 100,
            timestamp: Date.now()
          };
          
          signals.push(signal);
          
          if (this.onSignal) {
            this.onSignal(signal);
          }
        }
      }
      
      // 更新最后处理的交易 ID
      if (trades.length > 0) {
        this.lastTradeId = trades[0].trade_id;
      }
      
      if (signals.length > 0) {
        console.log(`[Whale] 发现 ${signals.length} 笔大额交易`);
      }
      
      return signals;
    } catch (err) {
      console.error('[Whale] 扫描失败:', err.message);
      return [];
    }
  }

  // 启动定时扫描
  start() {
    if (!config.largeTrade.enabled) {
      console.log('[Whale] 模块已禁用');
      return;
    }

    console.log('[Whale] 模块已启动');
    
    // 首次扫描（只记录最新 ID，不发信号）
    this.client.getTrades({ limit: 1 }).then(({ trades }) => {
      if (trades.length > 0) {
        this.lastTradeId = trades[0].trade_id;
      }
    });
    
    // 定时扫描
    this.timer = setInterval(() => this.scan(), 10000); // 10秒扫描一次
  }

  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }
}

module.exports = WhaleDetector;
