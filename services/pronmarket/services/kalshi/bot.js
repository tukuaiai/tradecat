/**
 * Kalshi 信号检测 Bot 主程序
 * 
 * 实时监控 Kalshi 预测市场，通过 Telegram 推送信号
 * 
 * 数据源:
 * - REST API: 定时扫描市场、订单簿、交易
 * - WebSocket: 实时 ticker、trade、orderbook_delta
 */

const TelegramBot = require('node-telegram-bot-api');
const config = require('./config/settings');
const KalshiClient = require('./utils/kalshiClient');
const RealtimeMonitor = require('./utils/realtimeMonitor');

// 信号检测模块
const NewMarketDetector = require('./signals/new-market/detector');
const OrderbookDetector = require('./signals/orderbook/detector');
const ClosingDetector = require('./signals/closing/detector');
const WhaleDetector = require('./signals/whale/detector');
const PriceSpikeDetector = require('./signals/price-spike/detector');
const ArbitrageDetector = require('./signals/arbitrage/detector');

// 格式化模块
const newMarketFormatter = require('./signals/new-market/formatter');
const orderbookFormatter = require('./signals/orderbook/formatter');
const closingFormatter = require('./signals/closing/formatter');
const whaleFormatter = require('./signals/whale/formatter');
const priceSpikeFormatter = require('./signals/price-spike/formatter');
const arbitrageFormatter = require('./signals/arbitrage/formatter');

class KalshiBot {
  constructor() {
    // Kalshi 客户端
    this.kalshi = new KalshiClient();
    
    // Telegram Bot
    this.telegram = new TelegramBot(config.telegram.token, { polling: true });
    this.chatId = config.telegram.chatId;
    
    // 市场缓存
    this.marketCache = new Map();
    
    // 实时监控器
    this.realtimeMonitor = new RealtimeMonitor(this.kalshi);
    
    // REST 轮询检测器
    this.detectors = {
      newMarket: new NewMarketDetector(this.kalshi),
      orderbook: new OrderbookDetector(this.kalshi),
      closing: new ClosingDetector(this.kalshi),
      whale: new WhaleDetector(this.kalshi),
      priceSpike: new PriceSpikeDetector(this.kalshi),
      arbitrage: new ArbitrageDetector(this.kalshi)
    };
    
    this._bindSignalHandlers();
    this._bindCommands();
  }

  // 绑定信号处理
  _bindSignalHandlers() {
    // REST 检测器信号
    this.detectors.newMarket.onSignal = (signal) => {
      const msg = newMarketFormatter.format(signal);
      this.sendMessage(msg);
    };
    
    this.detectors.orderbook.onSignal = async (signal) => {
      const market = await this._getMarket(signal.ticker);
      const msg = orderbookFormatter.format(signal, market);
      this.sendMessage(msg);
    };
    
    this.detectors.whale.onSignal = async (signal) => {
      const market = await this._getMarket(signal.ticker);
      const msg = whaleFormatter.format(signal, market);
      this.sendMessage(msg);
    };
    
    this.detectors.priceSpike.onSignal = (signal) => {
      const msg = priceSpikeFormatter.format(signal);
      this.sendMessage(msg);
    };
    
    this.detectors.arbitrage.onSignal = async (signal) => {
      const market = await this._getMarket(signal.ticker);
      const msg = arbitrageFormatter.format(signal, market);
      this.sendMessage(msg);
    };
    
    // 实时监控器信号
    this.realtimeMonitor.onSignal = async (signal) => {
      let msg;
      const market = await this._getMarket(signal.ticker);
      
      switch (signal.type) {
        case 'whale':
          msg = whaleFormatter.format(signal, market);
          break;
        case 'price-spike':
          signal.market = market;
          msg = priceSpikeFormatter.format(signal);
          break;
        case 'orderbook-imbalance':
          msg = orderbookFormatter.format(signal, market);
          break;
        default:
          return;
      }
      
      if (msg) this.sendMessage(msg);
    };
  }

  // 绑定 Telegram 命令
  _bindCommands() {
    // /start
    this.telegram.onText(/\/start/, (msg) => {
      this.telegram.sendMessage(msg.chat.id, 
        `🎯 *Kalshi 信号 Bot*\n\n` +
        `实时监控 Kalshi 预测市场\n\n` +
        `📊 可用命令:\n` +
        `/status - 交易所状态\n` +
        `/closing - 扫尾盘列表\n` +
        `/markets - 热门市场\n` +
        `/arb - 套利扫描\n` +
        `/help - 帮助`,
        { parse_mode: 'Markdown' }
      );
    });
    
    // /status
    this.telegram.onText(/\/status/, async (msg) => {
      try {
        const status = await this.kalshi.getExchangeStatus();
        const wsStatus = this.kalshi.ws?.readyState === 1 ? '✅ 已连接' : '❌ 未连接';
        
        this.telegram.sendMessage(msg.chat.id,
          `📊 *Kalshi 状态*\n\n` +
          `交易所: ${status.exchange_active ? '✅ 运行中' : '❌ 维护中'}\n` +
          `交易: ${status.trading_active ? '✅ 开放' : '❌ 暂停'}\n` +
          `WebSocket: ${wsStatus}\n` +
          `订阅数: ${this.kalshi.subscriptions.size}`,
          { parse_mode: 'Markdown' }
        );
      } catch (err) {
        this.telegram.sendMessage(msg.chat.id, `❌ 获取状态失败: ${err.message}`);
      }
    });
    
    // /closing
    this.telegram.onText(/\/closing/, async (msg) => {
      try {
        const signals = await this.detectors.closing.scan();
        const text = closingFormatter.formatList(signals);
        this.telegram.sendMessage(msg.chat.id, text, { parse_mode: 'Markdown' });
      } catch (err) {
        this.telegram.sendMessage(msg.chat.id, `❌ 获取失败: ${err.message}`);
      }
    });
    
    // /markets
    this.telegram.onText(/\/markets/, async (msg) => {
      try {
        const { markets } = await this.kalshi.getMarkets({ limit: 10, status: 'open' });
        let text = `📈 *热门市场*\n\n`;
        markets.forEach((m, i) => {
          const price = m.last_price ? (m.last_price / 100).toFixed(2) : '-';
          const vol = m.volume_24h || 0;
          text += `${i + 1}. ${m.title.slice(0, 35)}...\n`;
          text += `   $${price} | Vol: $${vol.toLocaleString()}\n\n`;
        });
        this.telegram.sendMessage(msg.chat.id, text, { parse_mode: 'Markdown' });
      } catch (err) {
        this.telegram.sendMessage(msg.chat.id, `❌ 获取失败: ${err.message}`);
      }
    });
    
    // /arb - 套利扫描
    this.telegram.onText(/\/arb/, async (msg) => {
      try {
        this.telegram.sendMessage(msg.chat.id, '🔍 正在扫描套利机会...');
        const signals = await this.detectors.arbitrage.scan();
        
        if (signals.length === 0) {
          this.telegram.sendMessage(msg.chat.id, '暂无套利机会（Kalshi 费率较高，套利空间有限）');
        } else {
          for (const signal of signals.slice(0, 5)) {
            const market = await this._getMarket(signal.ticker);
            const text = arbitrageFormatter.format(signal, market);
            this.telegram.sendMessage(msg.chat.id, text, { parse_mode: 'Markdown' });
          }
        }
      } catch (err) {
        this.telegram.sendMessage(msg.chat.id, `❌ 扫描失败: ${err.message}`);
      }
    });
    
    // /help
    this.telegram.onText(/\/help/, (msg) => {
      this.telegram.sendMessage(msg.chat.id,
        `📖 *Kalshi 信号 Bot 帮助*\n\n` +
        `*自动推送信号:*\n` +
        `🆕 新市场上线\n` +
        `📚 订单簿失衡\n` +
        `🐋 大额交易 (≥$${config.largeTrade.minValue})\n` +
        `📈 价格突变 (≥${config.priceSpike.minChange * 100}%)\n` +
        `💰 套利机会\n\n` +
        `*手动查询:*\n` +
        `/closing - 扫尾盘机会\n` +
        `/markets - 热门市场\n` +
        `/arb - 套利扫描\n` +
        `/status - 系统状态\n\n` +
        `📚 Kalshi 文档: docs.kalshi.com`,
        { parse_mode: 'Markdown' }
      );
    });
  }

  // 获取市场（带缓存）
  async _getMarket(ticker) {
    if (this.marketCache.has(ticker)) {
      const cached = this.marketCache.get(ticker);
      if (Date.now() - cached.ts < 300000) { // 5分钟缓存
        return cached.data;
      }
    }
    try {
      const { market } = await this.kalshi.getMarket(ticker);
      this.marketCache.set(ticker, { data: market, ts: Date.now() });
      return market;
    } catch {
      return null;
    }
  }

  // 发送消息
  async sendMessage(text) {
    if (config.debug.dryRun) {
      console.log('[DryRun]', text.slice(0, 100) + '...');
      return;
    }
    
    try {
      await this.telegram.sendMessage(this.chatId, text, {
        parse_mode: config.telegram.parseMode,
        disable_notification: config.telegram.disableNotification,
        disable_web_page_preview: true
      });
    } catch (err) {
      console.error('[Telegram] 发送失败:', err.message);
    }
  }

  // 启动
  async start() {
    console.log('========================================');
    console.log('  Kalshi 信号检测 Bot v1.0');
    console.log('========================================\n');
    
    // 检查配置
    if (!config.telegram.token || !config.telegram.chatId) {
      console.error('❌ 请配置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID');
      process.exit(1);
    }
    
    // 测试 API
    try {
      const status = await this.kalshi.getExchangeStatus();
      console.log(`✅ Kalshi API 连接成功`);
      console.log(`   交易所: ${status.exchange_active ? '运行中' : '维护中'}`);
      console.log(`   交易: ${status.trading_active ? '开放' : '暂停'}\n`);
    } catch (err) {
      console.warn('⚠️ Kalshi API 连接失败:', err.message);
      console.log('   继续启动，部分功能可能受限\n');
    }
    
    // 启动检测模块
    console.log('启动检测模块:');
    
    const modules = [
      { name: '新市场检测', detector: this.detectors.newMarket, enabled: config.newMarket.enabled },
      { name: '订单簿失衡', detector: this.detectors.orderbook, enabled: config.orderbook.enabled },
      { name: '扫尾盘检测', detector: this.detectors.closing, enabled: config.closing.enabled },
      { name: '大额交易', detector: this.detectors.whale, enabled: config.largeTrade.enabled },
      { name: '价格突变', detector: this.detectors.priceSpike, enabled: config.priceSpike.enabled },
      { name: '套利检测', detector: this.detectors.arbitrage, enabled: config.arbitrage.enabled }
    ];
    
    for (const m of modules) {
      if (m.enabled) {
        m.detector.start();
        console.log(`  ✅ ${m.name}`);
      } else {
        console.log(`  ⏸️ ${m.name} (已禁用)`);
      }
    }
    
    // 启动实时监控（如果有 API Key）
    if (config.kalshi.apiKeyId && config.kalshi.privateKeyPath) {
      console.log('\n启动实时监控 (WebSocket)...');
      try {
        await this.realtimeMonitor.start();
        console.log('  ✅ WebSocket 实时数据流');
      } catch (err) {
        console.warn('  ⚠️ WebSocket 连接失败:', err.message);
      }
    } else {
      console.log('\n⚠️ 未配置 API Key，跳过 WebSocket 实时监控');
      console.log('   配置 KALSHI_API_KEY_ID 和 KALSHI_PRIVATE_KEY_PATH 启用');
    }
    
    console.log('\n🚀 Bot 已启动，等待信号...\n');
    
    // 启动通知
    this.sendMessage(
      `🚀 *Kalshi 信号 Bot 已启动*\n\n` +
      `发送 /help 查看帮助`
    );
  }

  // 停止
  stop() {
    console.log('\n正在停止...');
    
    Object.values(this.detectors).forEach(d => d.stop?.());
    this.realtimeMonitor.stop();
    this.telegram.stopPolling();
    
    console.log('✅ Bot 已停止');
  }
}

// 主入口
const bot = new KalshiBot();

process.on('SIGINT', () => { bot.stop(); process.exit(0); });
process.on('SIGTERM', () => { bot.stop(); process.exit(0); });

bot.start().catch(err => {
  console.error('启动失败:', err);
  process.exit(1);
});

module.exports = KalshiBot;
