# AGENTS.md - AI Agent 操作手册

本文件面向 AI 编码/自动化 Agent，定义项目约束与执行规范。

---

## 1. Mission & Scope（目标与边界）

### 允许
- 修改 `services/<subservice>/`（polymarket/kalshi/opinion）下的业务代码
- 调整 `config/settings.js` 中的参数
- 新增/修改信号检测模块 `signals/*/`
- 更新文档 `docs/`、`README.md`、`AGENTS.md`

### 禁止
- 修改 `libs/external/` 下的任何文件（只读参考库）
- 直接提交 `.env` 或包含密钥的文件
- 删除或重命名 `data/users.json`、`data/translation-cache.json`（运行时数据）
- 未经确认修改 `ecosystem.config.js` 中的内存限制或实例数

---

## 2. Golden Path（推荐执行路径）

```bash
# 1. 拉起环境（以 Polymarket 子服务为例）
cd services/predict-service/services/polymarket
npm install

# 2. 配置（首次）
cp .env.example .env
# 填入 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID

# 3. 运行测试
npm test

# 4. 本地启动验证
npm run dev

# 5. 修改代码后复测
npm test

# 6. 更新文档（如有变更）
# 同步修改 README.md 和 AGENTS.md
```

---

## 3. Must-Run Commands（必须执行的命令）

| 场景 | 命令 | 工作目录 |
|------|------|----------|
| 安装依赖 | `npm install` | `services/predict-service/services/<subservice>/` |
| 启动（生产） | `npm start` | `services/predict-service/services/<subservice>/` |
| 启动（调试） | `npm run dev` | `services/predict-service/services/<subservice>/` |
| 运行测试 | `npm test` | `services/predict-service/services/<subservice>/` |
| PM2 启动 | `pm2 start ecosystem.config.js` | `services/predict-service/services/<subservice>/` |
| PM2 日志 | `pm2 logs <service-name>` | 任意 |
| PM2 重启 | `pm2 restart <service-name>` | 任意 |

---

## 4. Code Change Rules（修改约束）

### 架构原则
- 信号检测模块统一放在 `signals/<module-name>/`，包含 `detector.js` 和 `formatter.js`
- 配置集中在 `config/settings.js`，通过环境变量覆盖
- 翻译服务在 `translation/`，缓存持久化到 `data/translation-cache.json`

### 依赖添加规则
- 新增 npm 依赖需说明用途
- 优先使用已有依赖（如 `node-fetch`、`ws`）
- 禁止引入大型框架（如 Express、NestJS）除非任务明确要求

### 兼容性要求
- Node.js >= 16.0.0
- 保持 CommonJS 模块格式（`require`/`module.exports`）
- WebSocket 消息格式遵循 Polymarket 官方协议

### 禁止行为
- 禁止"顺手重构"或大范围改动，除非任务明确要求
- 禁止删除现有信号模块的核心逻辑
- 禁止修改 `libs/external/` 下的任何文件

---

## 5. Style & Quality（风格与质量）

### 代码风格
- 使用 2 空格缩进
- 字符串使用单引号
- 函数/变量使用 camelCase
- 常量使用 UPPER_SNAKE_CASE

### 注释要求
- 模块顶部需有功能说明注释
- 复杂逻辑需有行内注释
- 配置项需有中文说明

### 错误处理
- WebSocket 断连需自动重连
- API 调用需 try-catch 并记录日志
- 翻译失败需降级为原文

---

## 6. Project Map（项目结构速览）

```
services/polymarket/
├── bot.js                 # 主程序入口
├── launcher.js            # 启动器
├── ecosystem.config.js    # PM2 配置
├── package.json           # 依赖定义
├── .env.example           # 环境变量模板
│
├── config/
│   └── settings.js        # 全局配置
│
├── signals/
│   ├── arbitrage/         # 套利检测 ✅
│   │   ├── detector.js
│   │   ├── formatter.js
│   │   └── markets.js
│   ├── orderbook/         # 订单簿失衡 ✅
│   │   ├── detector.js
│   │   ├── formatter.js
│   │   └── analyzer.js
│   ├── closing/           # 扫尾盘 ✅（仅按时间窗口过滤，无成交量/价格阈值）
│   ├── new-market/        # 新市场（基线+增量）✅
│   ├── price-spike/       # 价格突变（SDK 版）✅
│   ├── whale/             # 大额交易（原巨鲸重写）✅
│   ├── deep-arb/          # 深度套利（镜像价格）✅
│   ├── liquidity-alert/   # 流动性枯竭预警 ✅
│   ├── book-skew/         # 订单簿倾斜突变 ✅
│   └── smart-money/       # 排行榜聪明钱跟踪 ✅
│
├── translation/
│   ├── cache.js           # 翻译缓存
│   ├── google-service.js  # Google 翻译
│   └── batch-queue.js     # 批量队列
│
├── utils/
│   ├── marketData.js      # 市场数据缓存
│   ├── userManager.js     # 用户管理
│   └── proxyAgent.js      # 代理配置
│
├── scripts/
│   ├── bot.sh             # 启动脚本
│   └── deploy-to-server.sh
│
└── data/
    ├── users.json         # 用户数据（运行时）
    └── translation-cache.json  # 翻译缓存（运行时）
```

---

## 7. Common Pitfalls（常见坑与修复）

| 问题 | 原因 | 修复 |
|------|------|------|
| Bot 无消息 | Token/ChatID 错误 | 检查 `.env` 配置 |
| WebSocket 断连 | 网络/代理问题 | 本地需全局代理 9910，服务器无需代理 |
| 翻译失败 | Google API 配额/凭证 | 检查 `GOOGLE_APPLICATION_CREDENTIALS` |
| 内存飙升 | 缓存无上限 | 参考 `docs/CACHE_POLICY_PLAN.md` |
| 信号过多 | 阈值过低 | 调高 `minProfit`/`minImbalance` |

---

## 8. Documentation Sync Rule（文档同步规则）

**强制要求：** 任何以下变更必须同步更新 `README.md` 和 `AGENTS.md`：

- 新增/删除/重命名目录或模块
- 修改 `package.json` 中的 scripts
- 修改 `.env.example` 中的环境变量
- 修改 `config/settings.js` 中的配置项
- 修改部署流程或命令

**不确定的内容用 `TODO` 标注，禁止猜测。**

---

## 9. Reference Docs（参考文档）

| 文档 | 路径 | 用途 |
|------|------|------|
| 缓存策略 | `docs/CACHE_POLICY_PLAN.md` | TTL/容量配置 |
| 性能调优 | `docs/PERFORMANCE_TUNING_REPORT.md` | 内存优化 |
| Telegram 问题 | `docs/TELEGRAM_PERFORMANCE_FIX.md` | 429/EPIPE 排查 |
| 外部库索引 | `libs/external/README.md` | SDK 用法 |

---

## 10. Libraries（外部库）

### poly-sdk（推荐）
路径：`libs/external/poly-sdk-main`

```bash
cd libs/external/poly-sdk-main
pnpm install
pnpm example:basic        # 基础用法
pnpm example:smart-money  # 聪明钱分析
pnpm example:live-arb     # 实时套利扫描
```

**能力：**
- Services: ArbitrageService, WalletService, MarketService, RealtimeService
- Clients: DataApiClient, GammaApiClient, ClobApiClient, TradingClient, CTFClient
- 数据: WebSocket 实时 + REST (positions/trades/leaderboard/trending)

---

*最后更新：2025-12-25*
