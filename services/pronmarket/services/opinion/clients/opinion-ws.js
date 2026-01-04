/**
 * Opinion WebSocket 客户端
 * 
 * 实时数据源：价格、订单簿、成交
 */

const WebSocket = require('ws');
const EventEmitter = require('events');

class OpinionWebSocket extends EventEmitter {
    constructor(options = {}) {
        super();
        this.apiKey = options.apiKey || process.env.OPINION_API_KEY;
        this.wsUrl = `wss://ws.opinion.trade?apikey=${this.apiKey}`;
        
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 0; // 0 = 无限
        this.reconnectDelay = options.reconnectDelay || 3000;
        this.heartbeatInterval = options.heartbeatInterval || 25000; // 25秒
        this.heartbeatTimer = null;
        
        // 订阅管理
        this.subscriptions = new Set();
        this.marketIds = new Set();
    }

    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }

        console.log('[OpinionWS] 正在连接...');
        
        this.ws = new WebSocket(this.wsUrl);

        this.ws.on('open', () => {
            console.log('[OpinionWS] ✅ 已连接');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this._startHeartbeat();
            this._resubscribe();
            this.emit('connected');
        });

        this.ws.on('message', (data) => {
            try {
                const msg = JSON.parse(data.toString());
                this._handleMessage(msg);
            } catch (e) {
                // 忽略解析错误
            }
        });

        this.ws.on('close', () => {
            console.log('[OpinionWS] 连接关闭');
            this.isConnected = false;
            this._stopHeartbeat();
            this._reconnect();
        });

        this.ws.on('error', (err) => {
            console.error('[OpinionWS] 错误:', err.message);
            this.emit('error', err);
        });
    }

    _handleMessage(msg) {
        const { msgType } = msg;
        
        // 调试日志
        if (process.env.DEBUG === 'true') {
            console.log('[WS] 收到:', msgType, JSON.stringify(msg).substring(0, 100));
        }
        
        switch (msgType) {
            case 'market.last.price':
                // 价格更新
                this.emit('price', {
                    type: 'price_change',
                    marketId: msg.marketId,
                    tokenId: msg.tokenId,
                    price: parseFloat(msg.price),
                    outcomeSide: msg.outcomeSide, // 1=YES, 2=NO
                    timestamp: Date.now()
                });
                break;
                
            case 'market.depth.diff':
                // 订单簿变化
                this.emit('orderbook', {
                    type: 'book',
                    marketId: msg.marketId,
                    tokenId: msg.tokenId,
                    side: msg.side, // 'bids' or 'asks'
                    price: msg.price,
                    size: msg.size,
                    outcomeSide: msg.outcomeSide,
                    timestamp: Date.now()
                });
                break;
                
            case 'market.last.trade':
                // 成交记录
                this.emit('trade', {
                    type: 'last_trade',
                    marketId: msg.marketId,
                    tokenId: msg.tokenId,
                    side: msg.side, // 'Buy' or 'Sell'
                    price: parseFloat(msg.price),
                    shares: parseFloat(msg.shares),
                    amount: parseFloat(msg.amount),
                    outcomeSide: msg.outcomeSide,
                    timestamp: Date.now()
                });
                break;
                
            case 'trade.order.update':
                this.emit('order_update', msg);
                break;
                
            case 'trade.record.new':
                this.emit('trade_confirmed', msg);
                break;
        }
    }

    _startHeartbeat() {
        this._stopHeartbeat();
        this.heartbeatTimer = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ action: 'HEARTBEAT' }));
            }
        }, this.heartbeatInterval);
    }

    _stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    _reconnect() {
        if (this.maxReconnectAttempts > 0 && this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('[OpinionWS] 达到最大重连次数');
            this.emit('max_reconnect');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectDelay * this.reconnectAttempts, 30000);
        console.log(`[OpinionWS] ${delay/1000}秒后重连 (第${this.reconnectAttempts}次)`);
        
        setTimeout(() => this.connect(), delay);
    }

    _resubscribe() {
        // 重新订阅所有频道
        for (const sub of this.subscriptions) {
            this._send(sub);
        }
    }

    _send(msg) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(msg));
        }
    }

    /**
     * 订阅市场
     */
    subscribeMarket(marketId) {
        if (this.marketIds.has(marketId)) return;
        this.marketIds.add(marketId);

        // 订阅三个频道
        const channels = ['market.last.price', 'market.depth.diff', 'market.last.trade'];
        
        for (const channel of channels) {
            const sub = { action: 'SUBSCRIBE', channel, marketId };
            this.subscriptions.add(sub);
            this._send(sub);
        }
        
        console.log(`[OpinionWS] 订阅市场 #${marketId}`);
    }

    /**
     * 批量订阅
     */
    subscribeMarkets(marketIds) {
        for (const id of marketIds) {
            this.subscribeMarket(id);
        }
    }

    /**
     * 取消订阅
     */
    unsubscribeMarket(marketId) {
        if (!this.marketIds.has(marketId)) return;
        this.marketIds.delete(marketId);

        const channels = ['market.last.price', 'market.depth.diff', 'market.last.trade'];
        
        for (const channel of channels) {
            const unsub = { action: 'UNSUBSCRIBE', channel, marketId };
            this._send(unsub);
        }
    }

    disconnect() {
        this._stopHeartbeat();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.isConnected = false;
        this.subscriptions.clear();
        this.marketIds.clear();
        console.log('[OpinionWS] 已断开');
    }
}

module.exports = OpinionWebSocket;
