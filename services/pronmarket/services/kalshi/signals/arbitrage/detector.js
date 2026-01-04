/**
 * 套利检测模块
 * 
 * Kalshi 是二元市场，YES + NO 理论上 = $1
 * 但由于 bid/ask 价差，可能存在套利空间
 * 
 * 套利条件: yes_ask + no_ask < 100 (买入成本 < $1)
 * 或: yes_bid + no_bid > 100 (卖出收益 > $1)
 */

const config = require('../../config/settings');

class ArbitrageDetector {
  constructor(kalshiClient) {
    this.client = kalshiClient;
    this.cooldowns = new Map();
    this.onSignal = null;
  }

  // 检测单个市场
  detectMarket(market) {
    const { ticker, yes_bid, yes_ask, no_bid, no_ask } = market;
    
    // 冷却检查
    if (this._isInCooldown(ticker)) return null;
    
    // 价格有效性检查
    if (!yes_bid || !yes_ask || !no_bid || !no_ask) return null;
    
    // 计算套利空间
    // 买入套利: 买 YES + 买 NO < 100
    const buyTotal = yes_ask + no_ask;
    const buyProfit = (100 - buyTotal) / 100;
    
    // 卖出套利: 卖 YES + 卖 NO > 100
    const sellTotal = yes_bid + no_bid;
    const sellProfit = (sellTotal - 100) / 100;
    
    // 扣除费用后的净利润
    const fee = config.arbitrage.tradingFee;
    const netBuyProfit = buyProfit - fee * 2;  // 买入两边
    const netSellProfit = sellProfit - fee * 2;
    
    let signal = null;
    
    if (netBuyProfit >= config.arbitrage.minProfit) {
      signal = {
        type: 'arbitrage',
        subType: 'buy',
        ticker,
        yesAsk: yes_ask / 100,
        noAsk: no_ask / 100,
        totalCost: buyTotal / 100,
        grossProfit: buyProfit,
        netProfit: netBuyProfit,
        timestamp: Date.now()
      };
    } else if (netSellProfit >= config.arbitrage.minProfit) {
      signal = {
        type: 'arbitrage',
        subType: 'sell',
        ticker,
        yesBid: yes_bid / 100,
        noBid: no_bid / 100,
        totalRevenue: sellTotal / 100,
        grossProfit: sellProfit,
        netProfit: netSellProfit,
        timestamp: Date.now()
      };
    }
    
    if (signal) {
      this._setCooldown(ticker);
      if (this.onSignal) {
        this.onSignal(signal);
      }
    }
    
    return signal;
  }

  // 从 ticker 数据检测
  detectFromTicker(data) {
    return this.detectMarket({
      ticker: data.market_ticker,
      yes_bid: data.yes_bid,
      yes_ask: data.yes_ask,
      no_bid: 100 - data.yes_ask,  // 推算
      no_ask: 100 - data.yes_bid   // 推算
    });
  }

  // 批量扫描
  async scan() {
    const signals = [];
    
    try {
      const { markets } = await this.client.getMarkets({ limit: 500, status: 'open' });
      
      for (const market of markets) {
        const signal = this.detectMarket(market);
        if (signal) signals.push(signal);
      }
      
      if (signals.length > 0) {
        console.log(`[Arbitrage] 发现 ${signals.length} 个套利机会`);
      }
    } catch (err) {
      console.error('[Arbitrage] 扫描失败:', err.message);
    }
    
    return signals;
  }

  // 冷却管理
  _isInCooldown(ticker) {
    const last = this.cooldowns.get(ticker);
    return last && Date.now() - last < config.arbitrage.cooldown;
  }

  _setCooldown(ticker) {
    this.cooldowns.set(ticker, Date.now());
  }

  // 启动定时扫描
  start() {
    if (!config.arbitrage.enabled) {
      console.log('[Arbitrage] 模块已禁用');
      return;
    }

    console.log('[Arbitrage] 模块已启动');
    
    // 首次扫描
    this.scan();
    
    // 定时扫描（30秒）
    this.timer = setInterval(() => this.scan(), 30000);
  }

  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }
}

module.exports = ArbitrageDetector;
