# 🤖 Polymarket 信号 Bot

**自动检测Polymarket预测市场的交易机会，通过Telegram推送信号！**

```
 ╔══════════════════════════════════════════════╗
 ║  💰 价格套利    📚 订单簿失衡    🐋 巨鲸跟踪  ║
 ║  📊 交易量异常  ⚡ 价格突变      😰 情绪反转  ║
 ╚══════════════════════════════════════════════╝
```

---

## 🎯 项目简介

当前支持的实时信号：

| 信号 | 数据源 | 状态 | 说明 |
|------|--------|------|------|
| 💰 价格套利 | CLOB trades/price_change | ✅ | 经典套利 |
| 📚 订单簿失衡 | CLOB agg_orderbook | ✅ | 盘口失衡 |
| 🆕 新市场 | Gamma API | ✅ | 基线+增量扫描 |
| ⚡ 价格突变 | CLOB price_change | ✅ | SDK 版，窗口检测 |
| 🐋 大额交易 | CLOB trade | ✅ | 原 whale 重写 |
| ⚡ 深度套利 | CLOB book | ✅ | 镜像有效价格 |
| 🚨 流动性枯竭 | CLOB book | ✅ | 深度骤降预警 |
| 📊 订单簿倾斜 | CLOB book | ✅ | Bid/Ask 倾斜突变 |
| 🧠 聪明钱 | Data API | ✅ | 排行榜 Top N 持仓变化 |

**扫尾盘（closing）最新规则：** 仅按时间窗口（默认 7 天）过滤，即将结束的市场全部展示，不再有成交量、流动性或价格绝对值阈值。

---

## 🚀 快速开始（10分钟上线）

### 步骤1：安装依赖

```bash
cd services/predict-service/services/polymarket
npm install
```

### 步骤2：获取Telegram Bot Token

1. 打开 Telegram，搜索 `@BotFather`
2. 发送 `/newbot`
3. 按提示创建Bot
4. 复制Token（类似：`123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`）

### 步骤3：获取Chat ID

1. 在Telegram中搜索 `@userinfobot`
2. 点击开始，它会告诉你的Chat ID

### 步骤4：配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
nano .env
```

填入你的信息：

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
LOG_LEVEL=info
```

### 步骤5：测试

```bash
# 内置样例测试（目前仅简单验证）
npm test

# Telegram 消息格式回归
npm run test:telegram
```

### 步骤6：运行！

```bash
# 正常启动
npm start

# 或调试模式
npm run dev
```

**恭喜！Bot开始运行了！** 🎉

---

## 📂 目录结构

```
bot/
├── README.md              ← 你正在看这个
├── package.json
├── .env.example           ← 环境变量示例
├── .env                   ← 你的配置（不提交到git）
│
└── src/
    ├── bot.js             ← 主程序入口
    ├── 目录结构说明.md
    ├── 模块1-价格套利-开发文档.md       ← 详细文档
    ├── 模块2-订单簿失衡-开发文档.md     ← 详细文档
    │
    ├── config/
    │   └── settings.js    ← 配置文件
    │
    └── signals/
        ├── arbitrage/     ← 模块1：价格套利 ✅
        │   ├── detector.js
        │   ├── markets.js
        │   ├── formatter.js
        │   ├── test-detector.js
        │   └── README.md
        │
        ├── orderbook/     ← 模块2：订单簿失衡 ✅
        │   ├── detector.js
        │   ├── analyzer.js
        │   ├── formatter.js
        │   ├── test-detector.js
        │   └── README.md
        │
        ├── whale/         ← 模块3（待开发）
        ├── volume/        ← 模块4（待开发）
        ├── price-shock/   ← 模块5（待开发）
        └── sentiment/     ← 模块6（待开发）
```

---

## 📚 完整文档

- **[目录结构说明](src/目录结构说明.md)** - 项目结构详解
- **[模块1开发文档](src/模块1-价格套利-开发文档.md)** - 价格套利详细实现
- **[模块2开发文档](src/模块2-订单簿失衡-开发文档.md)** - 订单簿失衡详细实现

---

## 💡 使用示例

### 收到的信号长这样：

```
💰 套利机会！

市场：Trump 2024 竞选
━━━━━━━━━━━━━━━━━━
YES 价格：0.48
NO 价格：0.47
总成本：0.95

预期收益：
• 毛利润：5.26%
• 扣除费用：-2%
• 净利润：3.26% ✅

操作步骤：
1. 买入 YES @ 0.48
2. 买入 NO @ 0.47
3. 等待结算，稳赚！

⏰ 时效：10分钟内
⭐ 强度：★★★★★
```

---

## ⚙️ 配置说明

### 调整灵敏度

```javascript
// 更激进（更多信号，但质量可能降低）
arbitrage: {
    minProfit: 0.02,  // 降到2%
    tradingFee: 0.02
}

// 更保守（更少信号，但质量更高）
arbitrage: {
    minProfit: 0.05,  // 提高到5%
    tradingFee: 0.02
}
```

### 开关模块

```javascript
// 只启用套利检测
arbitrage: { enabled: true },
orderbook: { enabled: false }

// 全部启用
arbitrage: { enabled: true },
orderbook: { enabled: true }
```

---

## 🐛 常见问题

### Q1: Bot没有发送消息？

检查：
1. Token是否正确？
2. Chat ID是否正确？
3. 有没有先给Bot发过消息？

### Q2: 发现不了套利机会？

可能原因：
1. 当前市场没有套利机会（正常）
2. minProfit设置太高（降低试试）
3. WebSocket连接有问题（查看日志）

### Q3: 收到太多信号？

解决：
```javascript
// 提高阈值
minProfit: 0.05,      // 从3%提高到5%
minImbalance: 15      // 从10倍提高到15倍
```

---

## 📊 监控和日志

### 查看日志

```bash
# 实时查看
tail -f bot/logs/signal.log

# 查看最近100条
tail -n 100 bot/logs/signal.log

# 搜索错误
grep "ERROR" bot/logs/error.log
```

### 统计信息

Bot每10分钟会打印统计信息：

```
📊 Bot运行统计
━━━━━━━━━━━━━━━━━━
套利检测：12个机会，8条信号
订单簿检测：5个机会，3条信号
运行时间：2小时15分钟
```

---

## 🛠️ 开发计划

### ✅ 第一阶段（已完成）
- [x] 创建项目结构
- [x] 模块1：价格套利
- [x] 模块2：订单簿失衡
- [x] 开发文档

### 🔨 第二阶段（1周后）
- [ ] 添加数据库（SQLite）
- [ ] 模块3：巨鲸跟踪
- [ ] 模块4：交易量异常

### 🚀 第三阶段（1个月后）
- [ ] 模块5：价格突变
- [ ] 模块6：情绪反转
- [ ] Web控制面板

---

## 🤝 贡献

欢迎提Issue和PR！

---

## ⚠️ 免责声明

本项目仅供学习和研究使用。
- 不构成投资建议
- 请自行评估风险
- 交易需谨慎

---

## 📞 联系方式

- GitHub Issues
- Telegram: @your_username

---

## 📄 许可证

MIT License

---

**祝你交易顺利！** 🚀💰
