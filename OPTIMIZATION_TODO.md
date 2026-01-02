# TradeCat 优化清单

> 更新时间: 2026-01-03 06:02
> 状态: 核实完成

---

## 📊 总览

| 状态 | 数量 | 说明 |
|:---:|:---:|:---|
| ✅ 已完成 | 9 | 代码/配置已修复 |
| ❌ 无需修改 | 6 | 设计合理或已存在 |
| ⏸️ 长期规划 | 2 | 按需添加 |
| **合计** | **17** | |

---

## ✅ 已完成 (9项)

| # | 问题 | 修复内容 | 提交 |
|:---:|:---|:---|:---|
| 1 | 硬编码绝对路径 | `.env.example` 改为留空，代码用 `PROJECT_ROOT` 相对路径 | `f6ea1bc` |
| 2 | 依赖版本未锁定 | 生成 `requirements.lock.txt` | `8042290` |
| 3 | BOT_TOKEN 别名冗余 | 删除 `TELEGRAM_BOT_TOKEN` 别名，统一用 `BOT_TOKEN` | `055b925` |
| 4 | 裸 except 异常 | 改为 `except Exception as e:` + 日志 | `adcdc0a` |
| 5 | 硬编码屏蔽币种 | 移至 `BLOCKED_SYMBOLS` 环境变量 | `3511c3a` |
| 6 | SQLite 频繁开关连接 | 单例连接复用 + WAL 模式 | `f020cf1` |
| 7 | 脚本硬编码路径 | `export_timescaledb.sh`、`upload_kaggle.sh` 改用相对路径 | `54c7871` |
| 8 | signals/engine.py 硬编码 | 改用环境变量 + 相对路径 fallback | `54c7871` |
| 9 | 文档硬编码路径 | `SETUP_PROMPT.md` 改用 `$HOME` | `ada67ac` |

---

## ❌ 无需修改 (6项)

| 问题 | 原因 |
|:---|:---|
| 数据库缺索引 | 已有 `idx_candles_1m_symbol_ts (symbol, bucket_ts DESC)` |
| 缺健康检查 | telegram-service 已有 `/ping` 命令 |
| SQLite 并发风险 | 已启用 WAL 模式 |
| 虚拟环境过大 (574MB) | 4 个独立服务，正常范围 |
| 配置分散 | 「全局 + 私有」设计合理 |
| SQLite 303MB | 38 表 × ~63K 行，正常 |

---

## ⏸️ 长期规划 (2项)

| 问题 | 说明 | 优先级 |
|:---|:---|:---:|
| 单元测试 | 按需为核心模块添加 pytest | 低 |
| 日志统一 | `simple_scheduler.py` 的 `print` 可改为 `logging` | 低 |

---

## 📋 验收清单

### 代码质量
- [x] 无硬编码绝对路径
- [x] 依赖版本已锁定
- [x] 环境变量命名统一
- [x] 异常处理有日志
- [x] 配置项可外部化

### 数据库
- [x] TimescaleDB 有复合索引
- [x] SQLite 启用 WAL 模式
- [x] SQLite 连接复用

### 文档
- [x] README.md 目录结构更新
- [x] AGENTS.md 项目结构更新
- [x] SETUP_PROMPT.md 无硬编码

### 安全
- [x] .env 权限 600
- [x] 启动脚本权限检查
- [x] 代理检测重试机制

---

*最后更新: 2026-01-03 06:02*
