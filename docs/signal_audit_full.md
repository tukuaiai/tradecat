# 全面代码与安全审计报告

## 1. 摘要 (Executive Summary)
- 审计输入来源：本地代码（pg_engine.py, pg_formatter.py, history.py, ui.py, engine_v2.py, signals/__init__.py, bot/app.py）；未提供变更说明/配置/IaC。
- 规范审查结论：⚠️ 无法裁决方向合规性（方向变量未提供）。
- 总体安全风险：中（SQL 注入高危面 + 推送并发模型问题）。
- Risk Scorecard：Critical 0 / High 1 / Medium 2 / Low 1。
- 关键发现 Top 5：
  1) PG 查询符号拼接导致 SQL 注入面。
  2) PG 推送跨线程创建事件循环，易 DoS/丢消息。
  3) 历史库默认写入仓库目录且无权限/清理控制。
  4) 历史保存异常分支未关闭连接，潜在锁泄漏。
  5) 其余 8 个审计域未见阻断级风险，但缺少方向变量无法做规范裁决。

## 2. 审计范围、假设与方向变量
### 2.1 审计范围与假设
- 范围：`services/telegram-service/src/signals/pg_engine.py`, `pg_formatter.py`, `history.py`, `ui.py`, `engine_v2.py`, `signals/__init__.py`, `services/telegram-service/src/bot/app.py`。
- 假设：部署未披露；TimescaleDB 用户权限未知；SYMBOLS_GROUPS 可能来自配置/环境可被外部控制；同进程多线程运行。
- 不确定性：无 DB 角色、文件权限、Bot 限速数据 → 结论偏保守。

### 2.2 方向变量与对齐总览
- 未提供方向变量 → 全部“无法判定”，仅给出风险陈述。

## 3. 变更解析与威胁建模
- 结构化变更：新增 PG 格式化/历史模块；双引擎统一保存历史；Bot 同时启动 PG+SQLite；新增历史查询 UI 回调。
- 攻击面：新增 TimescaleDB 读取、历史 SQLite 文件、回调 `sig_hist_*` 与 `signal_history`。
- 权限/数据流：SYMBOLS_GROUPS → PG 查询 → history.save → signal_history.db → Bot 推送。

## 4. 详细审计发现 (按 12 大类)

### 1) 控制流 (Control Flow)
- 无阻断级发现。

### 2) 执行模型 (Execution Model)
**发现 A**
- 规范严重级别：S2；安全严重级别：Medium；置信度：中。
- 位置/证据：`bot/app.py:6788-6816` 每条 PG 信号回调创建新事件循环并在子线程调用 `application.bot.send_message`。
- 反模式：Cross-thread event loop creation；隐式并发。
- 规范对齐：未提供方向变量；多事件循环导致行为分裂（不同线程/loop 调度）。
- 安全影响：高频信号可耗尽线程/loop 造成推送漏发或阻塞，形成 DoS 面。
- 攻击路径：伪造/诱发高频 PG 信号 → 大量 loop 创建 → Bot 被限流/崩溃。
- 修复：复用主事件循环，用 `asyncio.run_coroutine_threadsafe` 投递；添加速率限制与队列；记录推送失败指标。
- 验证：压测 1000 信号/分钟，确认 loop 数不增长、推送完整率 100%；单元测试覆盖线程投递。
- 标准映射：CWE-667, CAPEC-551。
- 追问：生产 Bot 是否暴露主 loop 句柄？Telegram 速率限制参数？

### 3) 状态 (State)
- 未新增共享可变状态竞争；cooldown dict 线程内使用，风险低。

### 4) 时间与顺序 (Time & Ordering)
- 未发现 TOCTOU；发现 A 已涵盖时序阻塞风险。

### 5) 错误与失败 (Error & Failure)
**发现 B**
- 规范严重级别：S1；安全严重级别：Low；置信度：中。
- 位置/证据：`signals/history.py:60-111` 异常时直接 `return -1`，未关闭连接。
- 反模式：资源未清理；隐式失败路径。
- 安全影响：在高频写入/异常下锁泄漏导致 “database is locked”，信号记录缺失。
- 修复：使用 context manager / try-finally 关闭连接；可加重试与错误计数。
- 验证：故障注入（磁盘满/权限错误）并发写入，确认无锁残留。
- 标准映射：CWE-404。

### 6) 输入与前置条件 (Input & Preconditions)
**发现 C**
- 规范严重级别：S3；安全严重级别：High；置信度：高。
- 位置/证据：`pg_engine.py:404-418`, `448-462` 将 `self.symbols` 直接拼接到 SQL IN 子句。
- 反模式：SQL 拼接；配置驱动多世界。
- 规范对齐：未提供方向变量；此实现显著增加语义分裂风险。
- 安全影响：若 SYMBOLS_GROUPS 可被外部控制，可执行任意 SQL（DROP/SELECT 任意表）。
- 攻击路径：控制 env 配置 → 注入 `BTCUSDT');DROP TABLE ...--` → TimescaleDB 被破坏/泄露。
- 修复：参数化 IN（psycopg2.sql 或 `symbol = ANY(%s)`）；符号白名单校验 `^[A-Z0-9_]{2,}$`；限制列表长度。
- 验证：单测注入字符串应被拒绝；集成测试校验查询结果与 SQL 日志。
- 标准映射：CWE-89 / OWASP A03:2021。
- 追问：SYMBOLS_GROUPS 是否来自用户输入？TimescaleDB 账户是否只读？

### 7) 数据建模 (Data Model)
- 单表结构清晰；未见 IDOR/Mass Assignment。

### 8) 依赖与耦合 (Dependency & Coupling)
- 依赖未新增；需确认 requirements 中 psycopg2 版本锁定（未审）。

### 9) 配置与变体 (Configuration & Variability)
**发现 D**
- 规范严重级别：S2；安全严重级别：Medium；置信度：中。
- 位置/证据：`history.py:14-46` 导入即创建 `signal_history.db` 于仓库路径，未设权限/配置。
- 反模式：启动即侧写、不可配置、缺省权限。
- 安全影响：文件可能 0644 暴露用户信号；无限增长耗尽磁盘导致拒绝服务。
- 修复：路径配置化（如 `SIGNAL_HISTORY_DB_PATH`）；创建后 chmod 600；启动定期 cleanup，设置最大保留天数/大小。
- 验证：启动后检查权限；压测写入并触发 cleanup。
- 标准映射：CWE-732, CWE-400。

### 10) 结构与架构 (Structure & Architecture)
- 双引擎并行 + 统一历史库边界清晰；未见信任边界跨越。

### 11) 性能与资源 (Performance & Resources)
- 未见 ReDoS；发现 D 已覆盖磁盘膨胀风险。

### 12) 可观测性与运维 (Observability & Ops)
- PG/历史写入缺少指标与告警；建议暴露 Prometheus 指标并在 Bot 日志中计数失败/限流事件。

## 5. 方向变量冲突与不可满足性
- 方向变量缺失，无法判定冲突。

## 6. 不可判定点与最坏情况推断
- 未提供 DB 权限：最坏假设 DB 账号有写/DDL → 注入可致毁表。
- 未提供 Bot 限速：最坏假设无速率限制 → 高频信号可致推送失败。
- 未提供文件权限策略：最坏假设 umask 022 → signal_history.db 可被同机他人读取。

## 7. 回归风险与安全测试计划
- 回归点：PG 查询链路、推送线程模型、历史写入。
- 必测用例：
  1) SQL 注入拒绝：符号含引号/分号应被拒绝。
  2) 高频信号 1000/min：推送完整率保持 100%，事件循环数量不增长。
  3) 历史写入故障：磁盘满/权限拒绝不阻断推送，错误计数可观测。
  4) 历史清理：40 天数据后 cleanup 删除过期记录。
- 自动化：CI 增 pytest 覆盖上述用例；接入 SAST（SQL 注入规则）；运行时暴露 metrics（signal_save_errors, pg_query_errors）。

## 8. 依赖、配置与基础设施审计
- 依赖：确认 `psycopg2(-binary)` 版本锁定；无新增第三方依赖。
- 配置：新增 `SIGNAL_HISTORY_DB_PATH`（建议）；确保 `DATABASE_URL` 仅可由可信配置写入。
- IaC/CI：未提供，建议验证镜像/容器不打包历史 DB，CI 中增加依赖漏洞扫描。

## 9. 需要补充的信息清单
- P0：SYMBOLS_GROUPS 来源与可控性；TimescaleDB 账号权限（只读/DDL）。
- P1：Bot 主事件循环获取方式；Telegram 速率限制配置。
- P2：运行节点 umask/文件权限；历史数据保留策略/容量上限。

## 10. 行动项 (Action Items)
ID | 发现标题 | 负责人 | 优先级 | 类型 | 工作量
-|-|-|-|-|-
A | PG 查询参数化防注入 | 后端 | 高 | 安全修复 | M
B | 推送复用主 loop + 限流 | 后端 | 中 | 安全修复 | M
C | 历史库路径/权限/清理 | 运维/后端 | 中 | 规范收敛 | M
D | save 异常关连接+重试 | 后端 | 低 | 安全修复 | S
E | CI 加 SAST/指标监控 | 平台/后端 | 中 | 规范收敛 | M

- 立即行动（24h）：A
- 短期（1–2 周）：B, C, D
- 中长期（1–2 月）：E

## 11. 总结与长期建议
- 反模式：SQL 拼接；跨线程事件循环；缺省文件权限/清理。
- 长期改进：
  - 统一 DB 访问层强制参数化与符号白名单。
  - 信号链路增加速率限制、队列、可观测指标。
  - 持久化路径全部配置化并启动权限/容量校验；CI 集成 SAST & 依赖扫描。
