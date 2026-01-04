/**
 * 实时信号监控器
 * 
 * 基于 WebSocket 实时数据流的信号检测
 * 支持: ticker, trade, orderbook_delta
 */

const config = require('../config/settings');

class RealtimeMonitor {
  constructor(kalshiClient) {
    this.client = kalshiClient;
    this.priceHistory = new Map();  // ticker -> [{price, ts}]
    this.cooldowns = new Map();
    this.onSignal = null;
    this.running = false;
  }

  // 启动实时监控
  async start() {
    if (this.running) return;
    this.running = true;
    
    console.log('[RealtimeMonitor] 启动实时监控...');
    
    try {
      // 连接 WebSocket
      await this.client.connectWs();
      
      // 订阅全局 ticker 和 trade
      this.client.subscribe(['ticker']);
      this.client.subscribe(['trade']);
      
      // 绑定事件处理
      this.client.on('ticker', (data) => this._onTicker(data));
      this.client.on('trade', (data) => this._onTrade(data));
      this.client.on('orderbook_snapshot', (data) => this._onOrderbook(data));
      this.client.on('orderbook_delta', (data) => this._onOrderbookDelta(data));
      
      console.log('[RealtimeMonitor] 已订阅实时数据流');
    } catch (err) {
      console.error('[RealtimeMonitor] 启动失败:', err.message);
      this.running = false;
    }
  }

  // 处理 ticker 更新
  _onTicker(data) {
    const { market_ticker, price, yes_bid, yes_ask, volume, ts } = data;
    
    // 记录价格历史
    this._recordPrice(market_ticker, price / 100, ts);
    
    // 检测价格突变
    this._checkPriceSpike(market_ticker, price / 100);
  }

  // 处理交易
  _onTrade(data) {
    const { market_ticker, yes_price, count, taker_side, ts } = data;
    
    // 计算交易金额
    const value = count * yes_price / 100;
    
    // 检测大额交易
    if (value >= config.largeTrade.minValue) {
      this._emitSignal('whale', {
        ticker: market_ticker,
        value,
        side: taker_side,
        price: yes_price / 100,
        count,
        timestamp: ts * 1000
      });
    }
  }

  // 处理订单簿快照
  _onOrderbook(data) {
    this._checkOrderbookImbalance(data.market_ticker, data);
  }

  // 处理订单簿增量
  _onOrderbookDelta(data) {
    const book = this.client.getLocalOrderbook(data.market_ticker);
    if (book) {
      this._checkOrderbookImbalance(data.market_ticker, {
        yes: Array.from(book.yes.entries()),
        no: Array.from(book.no.entries())
      });
    }
  }

  // 记录价格
  _recordPrice(ticker, price, ts) {
    if (!this.priceHistory.has(ticker)) {
      this.priceHistory.set(ticker, []);
    }
    
    const history = this.priceHistory.get(ticker);
    history.push({ price, ts: ts * 1000 });
    
    // 只保留 5 分钟数据
    const cutoff = Date.now() - 300000;
    while (history.length > 0 && history[0].ts < cutoff) {
      history.shift();
    }
  }

  // 检测价格突变
  _checkPriceSpike(ticker, currentPrice) {
    if (!config.priceSpike.enabled) return;
    if (this._isInCooldown('spike', ticker)) return;
    
    const history = this.priceHistory.get(ticker);
    if (!history || history.length < 2) return;
    
    const oldPrice = history[0].price;
    if (oldPrice <= 0) return;
    
    const change = Math.abs(currentPrice - oldPrice) / oldPrice;
    
    if (change >= config.priceSpike.minChange) {
      this._setCooldown('spike', ticker);
      this._emitSignal('price-spike', {
        ticker,
        oldPrice,
        newPrice: currentPrice,
        change,
        direction: currentPrice > oldPrice ? 'up' : 'down',
        timestamp: Date.now()
      });
    }
  }

  // 检测订单簿失衡
  _checkOrderbookImbalance(ticker, data) {
    if (!config.orderbook.enabled) return;
    if (this._isInCooldown('orderbook', ticker)) return;
    
    const yesDepth = this._calcDepth(data.yes);
    const noDepth = this._calcDepth(data.no);
    
    if (yesDepth < config.orderbook.minDepth && noDepth < config.orderbook.minDepth) {
      return;
    }
    
    const imbalance = yesDepth > noDepth 
      ? yesDepth / (noDepth || 1) 
      : noDepth / (yesDepth || 1);
    
    if (imbalance >= config.orderbook.minImbalance) {
      this._setCooldown('orderbook', ticker);
      this._emitSignal('orderbook-imbalance', {
        ticker,
        yesDepth,
        noDepth,
        imbalance,
        direction: yesDepth > noDepth ? 'YES' : 'NO',
        timestamp: Date.now()
      });
    }
  }

  // 计算深度
  _calcDepth(orders) {
    if (!orders || !Array.isArray(orders)) return 0;
    return orders.reduce((sum, [price, qty]) => {
      const p = typeof price === 'string' ? parseFloat(price) : price / 100;
      return sum + qty * p;
    }, 0);
  }

  // 冷却检查
  _isInCooldown(type, ticker) {
    const key = `${type}:${ticker}`;
    const last = this.cooldowns.get(key);
    const cooldown = type === 'spike' ? config.priceSpike.cooldown : config.orderbook.cooldown;
    return last && Date.now() - last < cooldown;
  }

  _setCooldown(type, ticker) {
    this.cooldowns.set(`${type}:${ticker}`, Date.now());
  }

  // 发送信号
  _emitSignal(type, data) {
    if (this.onSignal) {
      this.onSignal({ type, ...data });
    }
  }

  // 停止
  stop() {
    this.running = false;
    this.client.close();
    console.log('[RealtimeMonitor] 已停止');
  }
}

module.exports = RealtimeMonitor;
