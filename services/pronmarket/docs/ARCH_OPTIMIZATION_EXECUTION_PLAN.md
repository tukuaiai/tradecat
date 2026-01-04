# Polymarket 信号系统最优化架构：执行落地方案

> 目标：将“采集→检测→解释→发送→翻译/更新”改造为异步流水线，降低延迟、提升吞吐、减少重复请求，并保证可回滚与可观测。

## 0. 约束与假设
- 不变更业务策略（阈值、打分规则、信号类型保持原样）。
- 允许消息“先发简版、后补全更新”；允许翻译异步追加。
- 保留回退开关，可一键切回“串行单步路径”。

## 1. 总体架构（目标态）
```
采集 → 检测 → 规范化 → 解释(简版) → 发送 → 异步补全 → 翻译/更新
               |---------------------- 主链路 -----------------------|
                                  |----------- 异步补全链路 ----------|
```
核心组件：
- SignalPipeline：流水线调度器，负责阶段编排与失败回退。
- MarketMetadataService：singleflight + LRU 缓存，合并重复请求。
- MessageUpdateQueue：统一消息更新队列，避免 editMessageText 乱序。
- TranslationSingleflight：同文本只翻译一次，多消息复用结果。

## 2. 分阶段执行计划

### 阶段 0：基线指标与埋点（不改行为）
**是什么**：对关键耗时与命中率埋点。  
**为什么**：为重构前后性能对比提供真实基线。  
**怎么做**：
- 在 sendSignal 入口、format、sendMessage、editMessageText、翻译队列插入耗时统计。
- 输出：阶段耗时、缓存命中率、singleflight 命中率、队列长度。

**涉及文件/函数**
- `services/polymarket/bot.js`
- `services/polymarket/translation/batch-queue.js`

**验证**：日志可看到“阶段耗时/命中率”字段。

---

### 阶段 1：引入 SignalPipeline（结构先落地）
**是什么**：将 sendSignal 拆解为流水线阶段（normalize→enrich→format→send→postUpdate）。  
**为什么**：让“解释、补全、翻译、更新”与发送解耦，天然支持并行与回退。  
**怎么做**：
- 新建目录 `services/polymarket/pipeline/`：
  - `signal-pipeline.js`：流水线调度器
  - `stages/normalize.js`
  - `stages/enrich.js`
  - `stages/format.js`
  - `stages/send.js`
  - `stages/post-update.js`
- `bot.js: sendSignal()` 改为 pipeline 调用。

**涉及文件/函数**
- `services/polymarket/bot.js#sendSignal`
- `services/polymarket/signals/*/formatter.js`

**验证**：功能不变，日志可显示阶段耗时。

---

### 阶段 2：元数据 singleflight + 统一缓存
**是什么**：合并同一 marketId 的并发请求。  
**为什么**：避免重复请求与等待；减少 API 压力。  
**怎么做**：
- 新建 `services/polymarket/services/market-metadata.js`
  - `getMarketMeta(marketId)`：Promise singleflight
  - 内置 LRU 缓存（复用已有缓存逻辑）
- 替换 `getMarketSlug/getMarketName/getEventSlug` 直接调用。

**涉及文件/函数**
- `services/polymarket/bot.js`（sendSignal / enrichClosingSignal）

**验证**：高并发时相同 market 只触发一次 API。

---

### 阶段 3：先发简版，后补全更新
**是什么**：主链路不等待元数据补全；先发送简版，后 editMessageText 补全。  
**为什么**：降低延迟，保证“先有信号”。  
**怎么做**：
- formatter 支持 `variant: 'lite' | 'full'`。
- send 阶段使用 lite；post-update 阶段异步拉全量元数据后更新消息。
- 引入 MessageUpdateQueue 防乱序。

**涉及文件/函数**
- `services/polymarket/signals/*/formatter.js`
- `services/polymarket/bot.js`（发送与更新逻辑）

**验证**：发送后可见“简版→完整版”更新。

---

### 阶段 4：翻译去重与多消息复用
**是什么**：同文本只翻译一次，结果批量分发。  
**为什么**：当前同文本对每个用户重复翻译，浪费并发和限额。  
**怎么做**：
- 新增 TranslationSingleflight：`text → Promise`
- 翻译结果缓存：`text → translation`
- 批量更新多个 messageId（与 MessageUpdateQueue 结合）

**涉及文件/函数**
- `services/polymarket/translation/batch-queue.js`
- `services/polymarket/bot.js#addTranslationTask`

**验证**：同一市场标题只触发一次翻译 API。

---

### 阶段 5：closing 补全预算与分片
**是什么**：给 enrichClosingSignal 加时间预算，超时先发部分结果，后补全。  
**为什么**：避免大列表等待过长。  
**怎么做**：
- `enrichClosingSignal(signal, { budgetMs })`
- 超时则返回已补全部分；剩余进入 post-update。

**涉及文件/函数**
- `services/polymarket/bot.js#enrichClosingSignal`
- `services/polymarket/signals/closing/formatter.js`

**验证**：大窗口也能快速出首屏。

---

### 阶段 6：统一并发调度器
**是什么**：所有网络请求、翻译、消息更新统一调度与限流。  
**为什么**：避免各自并发策略冲突、可统一回退。  
**怎么做**：
- 新增 `services/polymarket/utils/async-scheduler.js`
- 所有外部 IO 通过调度器执行（含超时、重试、排队）

**涉及文件/函数**
- market metadata
- telegram send/edit
- translation batch

**验证**：压测无突发限流。

---

### 阶段 7：文档同步（强制）
**是什么**：更新 `AGENTS.md` 与目录树。  
**为什么**：架构变更需同步文档，防止系统失忆。  
**怎么做**：
- 更新模块职责、依赖边界、变更日志。

---

---

## 3. 风险分析与补充（审计追加）

### 3.1 已识别漏洞

#### 漏洞 1：消息更新竞态与补全失败降级（阶段3 关键）
**问题**：lite 消息发送后，如果 full 更新失败或超时，用户永远看到残缺消息。
**补充措施**：
- 补全失败重试上限：3次
- 最终失败后保持 lite 版本不变，记录失败 messageId 供排查
- 可选：追加"详情加载中..."提示

#### 漏洞 2：MessageUpdateQueue 版本覆盖
**问题**：同一消息的 lite→full→translation 三次更新，如果 translation 先完成会覆盖 full 内容。
**补充措施**：
- 定义消息状态机：`lite(0) → full(1) → translated(2)`
- 每次更新携带版本号，低版本不覆盖高版本
- translation 基于 full 内容追加，而非替换

#### 漏洞 3：singleflight 内存泄漏
**问题**：pending Promise Map 如果请求永不返回，会一直占用内存。
**补充措施**：
- singleflight 加超时自动清理（30s）
- 超时后允许新请求重新发起

#### 漏洞 4：回滚开关粒度不足
**问题**：只有两个开关，无法细粒度回滚单个功能。
**补充措施**：
- 每阶段独立开关：`enableSingleflight`、`enableLiteFirst`、`enableTranslationDedup`
- 配置热加载（不重启生效）

#### 漏洞 5：closing 分片边界条件
**问题**：budgetMs 超时后"已补全部分"定义不清；post-update 也超时怎么办？
**补充措施**：
- 定义最大重试轮次（如2轮）
- 超过轮次后放弃补全，记录日志

### 3.2 遗漏的潜在问题

#### 问题 6：Telegram 429 限流未纳入调度器
**背景**：参考 `TELEGRAM_PERFORMANCE_FIX.md`，Telegram 有严格限流。
**补充措施**：
- 阶段6调度器需区分 sendMessage 和 editMessageText 限流策略
- 同一 chat 的消息更新需串行（避免乱序）
- 全局 QPS 上限

#### 问题 7：翻译时机与消息更新一致性
**场景**：
1. 用户A收到 lite 消息，触发翻译
2. 翻译完成，更新消息
3. full 补全完成，再次更新（覆盖翻译）
4. 需要重新翻译 full 内容

**补充措施**：翻译应在 full 补全之后触发，而非 lite 阶段

#### 问题 8：错误传播与监控告警
**缺失**：方案只提到埋点，缺少告警机制。
**补充措施**：
- 错误率阈值告警（补全失败率 > 5%）
- 延迟 P99 告警
- 队列积压告警

#### 问题 9：冷启动缓存击穿
**场景**：bot 重启后缓存全空，大量信号同时触发，singleflight 还没建立，瞬间打爆 API。
**补充措施**：
- 启动时预热关键缓存（可选）
- 或启动后短暂限流（如前30s降低并发）

#### 问题 10：阶段依赖关系
**依赖图**：
```
阶段0.5 ← 阶段1 ← 阶段3 ← 阶段4
              ↑
阶段2 ← 阶段5
              ↓
         阶段6
```
- 阶段3（先发简版）依赖阶段1（pipeline）
- 阶段4（翻译去重）依赖阶段3（MessageUpdateQueue）
- 阶段5（closing分片）依赖阶段2（singleflight）

---

## 4. 修订后的阶段顺序

```
0   → 埋点基线
0.5 → 抽象现有代码（新增：先拆函数，不改行为）
1   → pipeline 结构
2   → singleflight + 缓存
3   → lite/full 分离 + MessageUpdateQueue（含状态机）
4   → 翻译去重（依赖3的队列）
5   → closing 分片（依赖2的 singleflight）
6   → 统一调度器（整合 Telegram 限流）
7   → 文档
```

### 阶段 0.5：抽象现有代码（新增）
**是什么**：在阶段1之前，先把 `sendSignal` 现有逻辑抽成独立函数，不改行为。
**为什么**：降低阶段1风险，让 pipeline 只是"换调度方式"。
**怎么做**：
```javascript
// 现在是一坨，先拆成：
async function normalizeSignal(signal) { ... }
async function enrichSignal(signal) { ... }
async function formatSignal(signal, user) { ... }
async function sendToUser(formatted, user) { ... }
```
**验证**：功能完全不变，只是代码结构调整。

---

## 5. 回滚与安全策略
- 每阶段保留独立开关：
  - `enablePipeline`
  - `enableSingleflight`
  - `enableLiteFirst`
  - `enableTranslationDedup`
  - `enableAsyncScheduler`
- 配置支持热加载（不重启生效）
- 任意阶段失败可回退到旧路径

---

## 6. 交付验收标准（量化）

| 指标 | 目标值 | 备注 |
|------|--------|------|
| P50 延迟 | < 500ms | 以阶段0基线为准 |
| P99 延迟 | < 2s | |
| 补全成功率 | > 99% | |
| 翻译 API 调用 | 减少 > 50% | |
| 元数据请求 | 减少 > 70% | singleflight 效果 |
| 发送成功率 | 不下降 | |

---

## 7. 灰度发布策略

### 方案 A：按用户灰度
- 按用户 ID 尾号灰度（如先 10% 用户走新链路）

### 方案 B：按信号类型灰度
- 先 orderbook → 再 arbitrage → 最后 closing
- closing 风险最高（涉及批量补全），最后上线

---

## 8. 文件改动清单（预期）
- `services/polymarket/bot.js`：信号处理改为 pipeline 调度
- `services/polymarket/pipeline/*`：新增流水线阶段
- `services/polymarket/services/market-metadata.js`：singleflight + 缓存
- `services/polymarket/utils/async-scheduler.js`：统一并发调度
- `services/polymarket/translation/*`：翻译去重与批量更新
- `services/polymarket/config/settings.js`：新增功能开关
- `services/polymarket/AGENTS.md`：架构文档同步

---

## 9. 下一步
按阶段 0 → 0.5 → 1 → 2 顺序开始落地，每阶段完成后给出：
- 变更文件列表
- 核心逻辑解释
- 运行验证步骤
