# Kalshi 信号检测 Bot

实时监控 Kalshi 预测市场的交易机会，通过 Telegram 推送信号。

## 功能特性

- 🆕 **新市场检测** - 新上线市场的早期机会
- 📚 **订单簿失衡检测** - 买卖盘深度严重失衡时的方向性信号
- 🔔 **扫尾盘信号** - 临近结算的高确定性市场
- 🐋 **大额交易检测** - 巨鲸交易跟踪
- ⚡ **价格突变检测** - 短时间内价格剧烈波动
- 💰 **套利检测** - YES+NO 价格偏离时的套利机会

## 数据源

| 类型 | 来源 | 用途 |
|------|------|------|
| REST API | 定时轮询 | 市场列表、订单簿、交易记录 |
| WebSocket | 实时推送 | ticker、trade、orderbook_delta |

## 快速开始

### 环境要求

- Node.js >= 16.0.0
- Telegram Bot Token（从 @BotFather 获取）
- Kalshi API Key（从 https://kalshi.com/account/api 获取）

### 安装与运行

```bash
# 1. 进入服务目录
cd services/kalshi

# 2. 安装依赖
npm install

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入配置

# 4. 启动
npm start          # 正常启动
npm run dev        # 调试模式
```

### Kalshi API 认证

Kalshi 使用 RSA-PSS 签名认证：

1. 登录 https://kalshi.com/account/api
2. 创建 API Key，下载私钥文件
3. 配置 `.env`:

```env
KALSHI_API_KEY_ID=your_api_key_id
KALSHI_PRIVATE_KEY_PATH=./kalshi_private_key.pem
```

### 使用 PM2 部署

```bash
# 启动
pm2 start ecosystem.config.js

# 常用命令
pm2 status
pm2 logs kalshi-bot
pm2 restart kalshi-bot
pm2 stop kalshi-bot
```

## 配置说明

### 环境变量（.env）

| 变量 | 必需 | 说明 |
|------|------|------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | ✅ | 接收消息的 Chat ID |
| `KALSHI_API_KEY_ID` | ❌ | Kalshi API Key ID |
| `KALSHI_PRIVATE_KEY_PATH` | ❌ | 私钥文件路径 |
| `LOG_LEVEL` | ❌ | 日志级别 |
| `DEBUG` | ❌ | 调试模式 |

### 信号模块配置（config/settings.js）

```javascript
// 订单簿失衡
orderbook: {
    enabled: true,
    minImbalance: 1.5,     // 最低失衡比例 1.5x
    minDepth: 20,          // 最小深度 $20
    cooldown: 60000
}

// 大额交易
largeTrade: {
    enabled: true,
    minValue: 1000,        // 最低金额 $1000
    cooldown: 30000
}

// 价格突变
priceSpike: {
    enabled: true,
    minChange: 0.10,       // 最小变化 10%
    timeWindowMs: 300000   // 5分钟窗口
}
```

## Telegram 命令

| 命令 | 说明 |
|------|------|
| `/start` | 欢迎消息 |
| `/status` | 交易所状态 + WebSocket 连接状态 |
| `/closing` | 扫尾盘列表 |
| `/markets` | 热门市场 |
| `/arb` | 套利扫描 |
| `/help` | 帮助 |

## 目录结构

```
services/kalshi/
├── bot.js                 # 主程序入口
├── ecosystem.config.js    # PM2 配置
├── package.json
├── .env.example
│
├── config/
│   └── settings.js        # 全局配置
│
├── signals/
│   ├── new-market/        # 新市场检测 ✅
│   ├── orderbook/         # 订单簿失衡 ✅
│   ├── closing/           # 扫尾盘 ✅
│   ├── whale/             # 大额交易 ✅
│   ├── price-spike/       # 价格突变 ✅
│   └── arbitrage/         # 套利检测 ✅
│
├── utils/
│   ├── kalshiClient.js    # Kalshi API 客户端 (REST + WebSocket)
│   ├── realtimeMonitor.js # 实时信号监控器
│   ├── marketData.js      # 市场数据缓存
│   └── proxyAgent.js      # 代理配置
│
└── data/                  # 运行时数据
```

## Kalshi API 参考

- 官方文档: https://docs.kalshi.com
- REST API: `https://api.elections.kalshi.com/trade-api/v2`
- WebSocket: `wss://api.elections.kalshi.com/trade-api/ws/v2`

### REST 端点

| 端点 | 说明 |
|------|------|
| `GET /markets` | 获取市场列表 |
| `GET /markets/{ticker}` | 获取单个市场 |
| `GET /markets/{ticker}/orderbook` | 获取订单簿 |
| `GET /markets/trades` | 获取交易记录 |
| `GET /events` | 获取事件列表 |
| `GET /exchange/status` | 交易所状态 |

### WebSocket 频道

| 频道 | 说明 |
|------|------|
| `ticker` | 市场行情更新 (price, bid, ask, volume) |
| `trade` | 公开交易 (price, count, taker_side) |
| `orderbook_delta` | 订单簿增量更新 |
| `fill` | 用户成交 (需认证) |

## 与 Polymarket 的差异

| 特性 | Kalshi | Polymarket |
|------|--------|------------|
| 监管 | CFTC 监管 | 去中心化 |
| 费率 | 7% | 0.2% |
| 价格单位 | cents (1-99) | 0-1 |
| 认证 | RSA-PSS 签名 | 无需认证 |
| 市场类型 | 二元期权 | 预测市场 |

## 免责声明

本项目仅供学习和研究使用，不构成投资建议。交易有风险，请自行评估。

## 许可证

MIT License
