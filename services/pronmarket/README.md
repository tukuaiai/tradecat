# Polymarket 信号检测与交易工具集

实时监控 Polymarket 预测市场的交易机会，通过 Telegram 推送信号。

## 📚 文档真源入口

**所有文档的唯一入口：[docs/index.md](docs/index.md)**

| 分类 | 说明 |
|------|------|
| [需求文档](docs/requirements/) | 功能需求、用户故事 |
| [设计文档](docs/design/) | 架构设计、技术方案 |
| [决策记录](docs/decisions/adr/) | ADR 架构决策 |
| [Prompt 模板](docs/prompts/) | AI 协作提示词 |
| [会话记录](docs/sessions/) | AI 协作会话 |
| [迭代复盘](docs/retros/) | 复盘与改进 |

## 功能特性

- 💰 **价格套利检测** - YES+NO 价格偏离时的无风险套利机会
- 📚 **订单簿失衡检测** - 买卖盘深度严重失衡时的方向性信号
- 🔔 **扫尾盘信号** - 临近结算的高确定性市场
- 🆕 **新市场检测** - 新上线市场的早期机会
- ⚡ **价格突变检测** - 短时间内价格剧烈波动
- 🌐 **中文翻译** - 自动翻译市场标题（Google Cloud Translation）

## 目录结构

```
pronmarket/
├── services/
│   └── polymarket/              # Telegram 信号 Bot（主服务）
│       ├── bot.js               # 主程序入口
│       ├── config/
│       │   └── settings.js      # 配置文件
│       ├── signals/
│       │   ├── arbitrage/       # 价格套利检测 ✅
│       │   ├── orderbook/       # 订单簿失衡检测 ✅
│       │   ├── closing/         # 扫尾盘信号 ✅
│       │   ├── new-market/      # 新市场检测 ✅
│       │   ├── price-spike/     # 价格突变检测 ✅
│       │   └── whale/           # 巨鲸跟踪（待开发）
│       ├── translation/         # 翻译服务
│       ├── utils/               # 工具函数
│       ├── scripts/             # 部署与运维脚本
│       └── data/                # 运行时数据（缓存/用户）
│
├── libs/external/
│   ├── poly-sdk-main/           # 统一 SDK（推荐）
│   ├── clob-client-main/        # 官方 CLOB 客户端
│   ├── real-time-data-client-main/  # WebSocket 客户端
│   └── ...                      # 其他参考实现（只读）
│
└── docs/                        # 设计文档与分析报告
    ├── CACHE_POLICY_PLAN.md     # 缓存策略
    ├── PERFORMANCE_TUNING_REPORT.md  # 性能调优
    └── TELEGRAM_PERFORMANCE_FIX.md   # Telegram 问题排查
```

## 快速开始

### 环境要求

- Node.js >= 16.0.0
- npm 或 pnpm
- Telegram Bot Token（从 @BotFather 获取）
- Google Cloud 服务账号（可选，用于翻译）

### 安装与运行

```bash
# 1. 进入服务目录
cd services/polymarket

# 2. 安装依赖
npm install

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID

# 4. 启动
npm start          # 正常启动
npm run dev        # 调试模式（DEBUG=true）
```

### 代理配置（重要）

| 环境 | 代理要求 |
|------|----------|
| **本地开发** | 必须全局代理，端口 `9910` |
| **服务器部署** | 无需代理 |

本地运行时，确保系统代理已开启，或在 `.env` 中配置：

```env
HTTPS_PROXY=http://127.0.0.1:9910
HTTP_PROXY=http://127.0.0.1:9910
```

### 使用 PM2 部署（推荐）

```bash
cd services/polymarket

# 启动
pm2 start ecosystem.config.js

# 常用命令
pm2 status                    # 查看状态
pm2 logs polymarket-bot       # 查看日志
pm2 restart polymarket-bot    # 重启
pm2 stop polymarket-bot       # 停止

# 开机自启
pm2 startup
pm2 save
```

## 配置说明

### 环境变量（.env）

| 变量 | 必需 | 说明 |
|------|------|------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | ✅ | 接收消息的 Chat ID |
| `GOOGLE_CLOUD_PROJECT` | ❌ | Google Cloud 项目 ID（翻译用） |
| `GOOGLE_APPLICATION_CREDENTIALS` | ❌ | 服务账号密钥路径（翻译用） |
| `LOG_LEVEL` | ❌ | 日志级别：debug/info/warn/error |
| `DEBUG` | ❌ | 调试模式：true/false |
| `HTTPS_PROXY` | ❌ | HTTP 代理地址 |

### 信号模块配置（config/settings.js）

```javascript
// 套利检测
arbitrage: {
    enabled: true,
    minProfit: 0.003,      // 最低净利润 0.3%
    tradingFee: 0.002,     // 交易费 0.2%
    cooldown: 60000        // 冷却时间 60s
}

// 订单簿失衡
orderbook: {
    enabled: true,
    minImbalance: 1.1,     // 最低失衡比例 1.1x
    cooldown: 60000
}

// 扫尾盘
closing: {
    enabled: true,
    timeWindowHours: 168,  // 监控窗口 7 天
    minVolume: 10000       // 最低成交量 $10k
}
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `npm start` | 启动 Bot |
| `npm run dev` | 调试模式启动 |
| `npm test` | 运行检测模块测试 |
| `npm run test:telegram` | 测试 Telegram 消息 |

## poly-sdk 数据能力

| 来源 | 数据 |
|------|------|
| WebSocket | price_update, book, last_trade（实时） |
| Data API | positions, trades, activity, leaderboard |
| Gamma API | trending, volume24hr, priceChange, events |
| CLOB API | orderbook, market metadata |

```bash
# SDK 示例
cd libs/external/poly-sdk-main
pnpm install
pnpm example:basic        # 基础用法
pnpm example:smart-money  # 聪明钱分析
pnpm example:live-arb     # 实时套利扫描
```

## 常见问题

### Bot 没有发送消息？

1. 检查 `TELEGRAM_BOT_TOKEN` 是否正确
2. 检查 `TELEGRAM_CHAT_ID` 是否正确
3. 确认已先给 Bot 发送过消息（激活对话）
4. 检查网络/代理配置

### 发现不了套利机会？

1. 当前市场可能没有套利机会（正常）
2. 尝试降低 `minProfit` 阈值
3. 检查 WebSocket 连接状态（查看日志）

### 内存占用过高？

参考 `docs/CACHE_POLICY_PLAN.md` 调整缓存 TTL 和容量上限。

## 文档

- `docs/CACHE_POLICY_PLAN.md` - 缓存 TTL/容量策略
- `docs/PERFORMANCE_TUNING_REPORT.md` - 性能调优方案
- `docs/TELEGRAM_PERFORMANCE_FIX.md` - Telegram 响应慢问题排查
- `libs/external/README.md` - 外部库索引

## 免责声明

本项目仅供学习和研究使用，不构成投资建议。交易有风险，请自行评估。

## 许可证

MIT License
