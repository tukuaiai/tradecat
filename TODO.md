# TradeCat TODO 清单

> 更新时间：2026-01-18
> 
> 优先级说明：🔴 紧急 | 🟠 重要 | 🟡 一般 | 🟢 低优先级

---

## 🔴 紧急修复（灾难性故障）

### Bot 响应问题
- [x] **全局 bot 即时响应未生效** - 2026-01-18 已修复  
  - 动作：放宽群聊命令/按钮放行，保留普通文本白名单；修正 `_t` 调用顺序；重启服务
  - 症状：消息发送后无即时反馈
  - 影响：用户体验极差，以为 bot 挂了
  - 排查方向：`telegram-service/src/bot/app.py` 消息处理链路
  
- [x] **币种查询功能问题** - 2026-01-18 修复对齐与触发
  - `BTC!` / `BTC!!` / `BTC@` 触发无反馈
  - 检查 `single_token_snapshot.py`、`single_token_txt.py`

### 群聊安全
- [x] **tgbot 群聊消息回调触发白名单** - 2026-01-18 调整为“命令/按钮放行，普通文本仍需白名单+@”
  - 已实现：命令前缀过滤（`/`、`!` 或 bot_command 实体即放行）
  - 已实现：普通文本仍需白名单且需 @bot（防刷屏）

---

## 🟠 重要功能（核心体验）

### i18n 国际化残留
- [ ] **卡片中文字段与表头中英文问题**
  - 涉及 39 张卡片（basic/advanced/futures）
  - 字段名硬编码中文，需改用 i18n key
  - 表头翻译不完整
  - 参考：`services/telegram-service/src/cards/i18n.py`

### 数据面板可用性
- [ ] **行情情绪/涨跌榜缓存为空**  
  - 原因：`telegram-service/src/bot/app.py` 硬编码 `BINANCE_API_DISABLED=True`，跳过 Binance 拉取，`ticker_24hr_data` / `funding_rate_data` 始终为空  
  - 方向：决定是否恢复外部拉取或改用 TimescaleDB/SQLite 本地数据源；否则保持禁用仅会有告警

### 数据架构优化
- [ ] **SQLite 数据迁移到统一 PG 库**（重要但不紧急）
  - 当前：`libs/database/services/telegram-service/market_data.db`
  - 目标：统一到 TimescaleDB (5434)
  - 好处：数据一致性、查询性能、运维简化
  
- [ ] **数据库全市场适配**（重要但不紧急）
  - 当前仅支持币安永续合约
  - 目标：支持美股/A股/宏观数据
  - 涉及：markets-service 数据写入、trading-service 指标计算

### 内部通讯与数据消费
- [ ] **内部 API 通讯层**
  - 服务间 HTTP/gRPC 调用标准化
  - 数据消费方法抽象
  - 考虑发布 PyPI 包供外部使用

---

## 🟡 功能增强

### AI 与策略
- [ ] **成熟策略组供 AI 使用**
  - 整理现有指标组合为策略模板
  - 策略：趋势跟踪、均值回归、动量突破、期货情绪
  - AI 可根据市场状态选择策略

- [ ] **接入执行模块**
  - 复用现有开源 AI 项目轮子
  - 接入统计数据源
  - 复用 AI 功能消费的数据作为新增字段

### 信号服务增强
- [ ] **信号规则扩展**（当前 129 条）
  - core: 20 条
  - momentum: 27 条
  - trend: 19 条
  - volatility: 15 条
  - volume: 13 条
  - futures: 11 条
  - pattern: 16 条
  - misc: 8 条
  - 目标：补充跨周期信号、组合信号

### 可视化增强
- [ ] **vis-service 功能完善**
  - K线图渲染优化
  - 指标叠加显示
  - VPVR 成交量分布图
  - 端口：8087

---

## 🟢 技术债务

### 代码质量
- [ ] 统一日志格式（部分服务日志格式不一致）
- [ ] 补充单元测试（当前覆盖率低）
- [ ] 类型注解完善（关键函数缺少类型）

### 文档同步
- [ ] README.md / README_EN.md / AGENTS.md 保持同步
- [ ] API 文档自动生成（api-service）

### 配置管理
- [ ] 端口统一（5433 vs 5434 混用问题）
- [ ] 环境变量校验（启动时检查必填项）
- [ ] PG 实时信号服务导入失败告警  
  - 现象：`signals.pg_engine` 导入失败，PG 实时信号未启动  
  - 方向：调整 telegram-service 的导入路径或在 signal-service 侧提供可导入入口，并确保 psycopg/PG 配置就绪

---

## 📊 项目现状统计

| 模块 | 数量 | 状态 |
|:---|:---:|:---|
| 稳定版服务 | 5 | data/trading/telegram/ai/signal |
| 预览版服务 | 6 | api/markets/vis/order/predict/fate |
| 排行榜卡片 | 39 | basic(9)/advanced(10)/futures(20) |
| 技术指标 | 32 | batch(22)/incremental(10) |
| 信号规则 | 129 | 8 个分类 |
| 数据规模 | 3.73亿 | K线 + 9457万期货指标 |

---

## 📝 备忘

### 服务端口
- TimescaleDB: 5433 (旧) / 5434 (新)
- api-service: 8000
- vis-service: 8087
- fate-service: 8001

### 关键路径
- 全局配置：`config/.env`
- SQLite 数据：`libs/database/services/telegram-service/market_data.db`
- 冷却持久化：`libs/database/services/signal-service/cooldown.db`

### 验证命令
```bash
./scripts/verify.sh          # 代码验证
./scripts/check_env.sh       # 环境检查
./scripts/start.sh status    # 服务状态
```
