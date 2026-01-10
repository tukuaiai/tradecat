# 规范与安全双重审计 - PG/SQLite 信号集成

## 0. 范围
- 代码：signals/pg_engine.py, pg_formatter.py, history.py, ui.py, engine_v2.py, signals/__init__.py, bot/app.py。
- 配置/IaC/部署：未提供，按最坏情况推断。
- 方向变量：未提供，规范合规性仅做客观风险陈述。

## 1. 结论
- 规范合规：⚠️ 无法裁决（缺少方向变量）。
- 安全风险：中。
- Risk Scorecard：Critical 0 / High 1 / Medium 2 / Low 1。
- 需立即关注：PG 查询注入面；PG 推送跨线程事件循环。

## 2. 关键发现
1) **SQL 注入面**（High，S3）
   - 位置：pg_engine.py 查询字符串直接拼接 symbols。
   - 风险：SYMBOLS_GROUPS 可控时可执行任意 SQL；影响 TimescaleDB。
   - 修复：参数化 IN（psycopg2.sql 或 =ANY(%s)），并对白名单正则校验符号。

2) **推送并发模型不安全**（Medium，S2）
   - 位置：bot/app.py on_pg_signal 为每条信号创建新事件循环并跨线程 send_message。
   - 风险：高频信号可耗尽线程/loop，导致推送丢失或 DoS。
   - 修复：复用主事件循环，使用 asyncio.run_coroutine_threadsafe；加速率限制。

3) **历史库默认写入+无权限/清理**（Medium，S2）
   - 位置：history.py 导入即创建 signal_history.db，未设权限、路径不可配置。
   - 风险：文件 0644 泄露用户信号；无限增长占满磁盘。
   - 修复：创建时 chmod 600，路径配置化（如 SIGNAL_HISTORY_DB_PATH），启动定期 cleanup。

4) **异常分支未关连接**（Low，S1）
   - 位置：history.py save 异常直接返回 -1，连接未显式关闭。
   - 风险：潜在锁/句柄泄漏，导致写入失败。
   - 修复：使用 context manager / finally 关闭；可加重试。

## 3. 建议行动
- 24h：修复 SQL 参数化 + 符号白名单（Action A）。
- 1–2 周：
  - PG 推送改主 loop 投递并加速率限制（Action B）。
  - 历史库路径配置化、默认 600、启动清理任务（Action C）。
  - save 异常关闭连接并重试（Action D）。
- 1–2 月：在 CI 加 SAST/限流/指标监控，覆盖信号链路（Action E）。

## 4. 必测用例
- SQL 注入拒绝：符号含引号应被拒绝/转义。
- 高频信号 1000/min：推送完整率与线程/loop 数保持常量。
- 历史写入故障：磁盘满/权限拒绝不应阻断推送。
- 历史清理：插入 40 天数据后 cleanup 删除过期记录。

## 5. 待补充信息
- P0：生产 SYMBOLS_GROUPS 来源及可控性；TimescaleDB 账号权限。
- P1：Bot 主事件循环获取方式、Telegram 速率限制配置。
- P2：运行节点 umask/文件权限策略；历史数据保留/容量上限。
