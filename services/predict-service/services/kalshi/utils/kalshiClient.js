/**
 * Kalshi API 客户端
 * 
 * 封装 REST API 和 WebSocket 连接
 * 文档: https://docs.kalshi.com
 */

const crypto = require('crypto');
const fs = require('fs');
const fetch = require('node-fetch');
const WebSocket = require('ws');
const config = require('../config/settings');

class KalshiClient {
  constructor() {
    this.baseUrl = config.kalshi.baseUrl;
    this.wsUrl = config.kalshi.wsUrl + '/trade-api/ws/v2';
    this.apiKeyId = config.kalshi.apiKeyId;
    this.privateKey = this._loadPrivateKey();
    this.ws = null;
    this.subscriptions = new Map();
    this.messageId = 0;
    this.listeners = new Map();
    this.orderbooks = new Map(); // 本地订单簿缓存
    this.reconnectAttempts = 0;
  }

  // 加载私钥
  _loadPrivateKey() {
    const keyPath = config.kalshi.privateKeyPath;
    if (!keyPath || !fs.existsSync(keyPath)) {
      console.warn('[KalshiClient] 私钥文件未配置，WebSocket 认证功能受限');
      return null;
    }
    try {
      return fs.readFileSync(keyPath, 'utf8');
    } catch (e) {
      console.error('[KalshiClient] 读取私钥失败:', e.message);
      return null;
    }
  }

  // RSA-PSS 签名
  _sign(timestamp, method, path, body = '') {
    if (!this.privateKey) return '';
    const message = `${timestamp}${method}${path}${body}`;
    try {
      const sign = crypto.createSign('RSA-SHA256');
      sign.update(message);
      return sign.sign({ 
        key: this.privateKey, 
        padding: crypto.constants.RSA_PKCS1_PSS_PADDING,
        saltLength: crypto.constants.RSA_PSS_SALTLEN_DIGEST
      }, 'base64');
    } catch (e) {
      console.error('[KalshiClient] 签名失败:', e.message);
      return '';
    }
  }

  // 构建请求头
  _buildHeaders(method, path, body = '') {
    const timestamp = Date.now().toString();
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
    
    if (this.apiKeyId && this.privateKey) {
      headers['KALSHI-ACCESS-KEY'] = this.apiKeyId;
      headers['KALSHI-ACCESS-TIMESTAMP'] = timestamp;
      headers['KALSHI-ACCESS-SIGNATURE'] = this._sign(timestamp, method, path, body);
    }
    
    return headers;
  }

  // REST API 请求
  async request(method, endpoint, params = {}, body = null) {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    if (method === 'GET' && Object.keys(params).length > 0) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) url.searchParams.append(k, v);
      });
    }
    
    const path = '/trade-api/v2' + endpoint + (url.search || '');
    const bodyStr = body ? JSON.stringify(body) : '';
    
    const response = await fetch(url.toString(), {
      method,
      headers: this._buildHeaders(method, path, bodyStr),
      body: body ? bodyStr : undefined,
      timeout: config.kalshi.requestTimeout
    });
    
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Kalshi API Error: ${response.status} - ${error}`);
    }
    
    return response.json();
  }

  // ==================== REST API 方法 ====================

  async getExchangeStatus() {
    return this.request('GET', '/exchange/status');
  }

  async getMarkets(params = {}) {
    return this.request('GET', '/markets', {
      limit: params.limit || 100,
      cursor: params.cursor,
      status: params.status || 'open',
      series_ticker: params.seriesTicker,
      event_ticker: params.eventTicker,
      tickers: params.tickers,
      min_close_ts: params.minCloseTs,
      max_close_ts: params.maxCloseTs,
      ...params
    });
  }

  async getMarket(ticker) {
    return this.request('GET', `/markets/${ticker}`);
  }

  async getOrderbook(ticker, depth = 10) {
    return this.request('GET', `/markets/${ticker}/orderbook`, { depth });
  }

  async getTrades(params = {}) {
    return this.request('GET', '/markets/trades', {
      limit: params.limit || 100,
      cursor: params.cursor,
      ticker: params.ticker,
      min_ts: params.minTs,
      max_ts: params.maxTs
    });
  }

  async getEvents(params = {}) {
    return this.request('GET', '/events', {
      limit: params.limit || 100,
      cursor: params.cursor,
      status: params.status,
      series_ticker: params.seriesTicker
    });
  }

  // ==================== WebSocket 方法 ====================

  async connectWs() {
    return new Promise((resolve, reject) => {
      console.log(`[KalshiClient] 连接 WebSocket: ${this.wsUrl}`);
      
      // 构建认证头
      const timestamp = Date.now().toString();
      const path = '/trade-api/ws/v2';
      const headers = {};
      
      if (this.apiKeyId && this.privateKey) {
        headers['KALSHI-ACCESS-KEY'] = this.apiKeyId;
        headers['KALSHI-ACCESS-TIMESTAMP'] = timestamp;
        headers['KALSHI-ACCESS-SIGNATURE'] = this._sign(timestamp, 'GET', path, '');
      }
      
      this.ws = new WebSocket(this.wsUrl, { headers });
      
      this.ws.on('open', () => {
        console.log('[KalshiClient] WebSocket 已连接');
        this.reconnectAttempts = 0;
        resolve();
      });
      
      this.ws.on('message', (data) => {
        try {
          const msg = JSON.parse(data.toString());
          this._handleMessage(msg);
        } catch (e) {
          // 可能是 ping/pong 帧
        }
      });
      
      this.ws.on('ping', (data) => {
        // 自动回复 pong（ws 库默认处理）
      });
      
      this.ws.on('close', (code, reason) => {
        console.log(`[KalshiClient] WebSocket 断开: ${code} ${reason}`);
        this._handleReconnect();
      });
      
      this.ws.on('error', (err) => {
        console.error('[KalshiClient] WebSocket 错误:', err.message);
        reject(err);
      });
    });
  }

  // 重连逻辑
  _handleReconnect() {
    if (!config.kalshi.autoReconnect) return;
    
    const maxAttempts = config.kalshi.maxReconnectAttempts;
    if (maxAttempts > 0 && this.reconnectAttempts >= maxAttempts) {
      console.error('[KalshiClient] 达到最大重连次数');
      return;
    }
    
    this.reconnectAttempts++;
    const delay = Math.min(
      config.kalshi.reconnectDelayMs * Math.pow(2, this.reconnectAttempts - 1),
      config.kalshi.reconnectDelayMaxMs
    );
    
    console.log(`[KalshiClient] ${delay}ms 后重连 (第 ${this.reconnectAttempts} 次)`);
    setTimeout(() => {
      this.connectWs().then(() => {
        // 重新订阅
        this._resubscribe();
      }).catch(() => {});
    }, delay);
  }

  // 重新订阅
  _resubscribe() {
    for (const [sid, sub] of this.subscriptions) {
      console.log(`[KalshiClient] 重新订阅: ${sub.channels.join(',')}`);
      this.subscribe(sub.channels, sub.marketTickers);
    }
  }

  // 发送消息
  _send(cmd, params = {}) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[KalshiClient] WebSocket 未连接');
      return null;
    }
    const id = ++this.messageId;
    const msg = { id, cmd, params };
    this.ws.send(JSON.stringify(msg));
    return id;
  }

  // 订阅频道
  // channels: ['ticker', 'trade', 'orderbook_delta']
  // marketTickers: 可选，指定市场
  subscribe(channels, marketTickers = null) {
    const params = { channels };
    if (marketTickers) {
      if (Array.isArray(marketTickers)) {
        params.market_tickers = marketTickers;
      } else {
        params.market_ticker = marketTickers;
      }
    }
    const id = this._send('subscribe', params);
    
    // 记录订阅
    if (id) {
      this.subscriptions.set(id, { channels, marketTickers });
    }
    return id;
  }

  // 取消订阅
  unsubscribe(sids) {
    const arr = Array.isArray(sids) ? sids : [sids];
    arr.forEach(sid => this.subscriptions.delete(sid));
    return this._send('unsubscribe', { sids: arr });
  }

  // 处理消息
  _handleMessage(msg) {
    const { type, msg: data, sid, seq } = msg;
    
    switch (type) {
      case 'subscribed':
        console.log(`[KalshiClient] 订阅成功: ${data.channel} (sid: ${data.sid})`);
        break;
        
      case 'unsubscribed':
        console.log(`[KalshiClient] 取消订阅: sid ${sid}`);
        break;
        
      case 'error':
        console.error(`[KalshiClient] 错误: ${data?.code} - ${data?.msg}`);
        this.emit('error', data);
        break;
        
      case 'ticker':
        // 市场行情更新
        this.emit('ticker', data);
        break;
        
      case 'trade':
        // 公开交易
        this.emit('trade', data);
        break;
        
      case 'orderbook_snapshot':
        // 订单簿快照
        this._updateOrderbook(data.market_ticker, data, true);
        this.emit('orderbook_snapshot', data);
        break;
        
      case 'orderbook_delta':
        // 订单簿增量更新
        this._applyOrderbookDelta(data);
        this.emit('orderbook_delta', data);
        break;
        
      case 'fill':
        // 用户成交（需认证）
        this.emit('fill', data);
        break;
    }
  }

  // 更新本地订单簿
  _updateOrderbook(ticker, data, isSnapshot = false) {
    if (isSnapshot) {
      this.orderbooks.set(ticker, {
        yes: new Map(data.yes?.map(([p, q]) => [p, q]) || []),
        no: new Map(data.no?.map(([p, q]) => [p, q]) || []),
        seq: data.seq || 0
      });
    }
  }

  // 应用订单簿增量
  _applyOrderbookDelta(delta) {
    const { market_ticker, price, delta: qty, side } = delta;
    const book = this.orderbooks.get(market_ticker);
    if (!book) return;
    
    const sideBook = side === 'yes' ? book.yes : book.no;
    if (qty === 0) {
      sideBook.delete(price);
    } else {
      const current = sideBook.get(price) || 0;
      const newQty = current + qty;
      if (newQty <= 0) {
        sideBook.delete(price);
      } else {
        sideBook.set(price, newQty);
      }
    }
  }

  // 获取本地订单簿
  getLocalOrderbook(ticker) {
    return this.orderbooks.get(ticker);
  }

  // 事件监听
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const idx = callbacks.indexOf(callback);
      if (idx >= 0) callbacks.splice(idx, 1);
    }
  }

  emit(event, data) {
    const callbacks = this.listeners.get(event) || [];
    callbacks.forEach(cb => {
      try {
        cb(data);
      } catch (e) {
        console.error(`[KalshiClient] 事件处理错误 (${event}):`, e.message);
      }
    });
  }

  // 关闭连接
  close() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.subscriptions.clear();
    this.orderbooks.clear();
  }
}

module.exports = KalshiClient;
