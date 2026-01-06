# TradeCat - AI Agent 操作手册

> 本文档面向 AI 编码 Agent，以可执行指令的视角编写，约束与指导 Agent 行为。

---

## 1. Mission & Scope（目标与边界）

### 1.1 允许的操作

- 修改 `services/*/src/` 下的业务代码
- 修改 `config/.env.example` 全局配置模板
- 添加/修改技术指标 (`services/trading-service/src/indicators/`)
- 添加/修改排行榜卡片 (`services/telegram-service/src/cards/`)
- 修改启动脚本 (`services/*/scripts/`, `scripts/`)
- 更新文档 (`README.md`, `AGENTS.md`)

### 1.2 禁止的操作

- **禁止修改** `config/.env` 生产配置文件
- **禁止修改** 数据库 schema（除非明确要求）
- **禁止删除** `libs/database/` 下的数据文件
- **禁止修改** `.gitignore` 中已忽略的敏感文件
- **禁止** 大范围重构，除非任务明确要求
- **禁止** 添加未经验证的第三方依赖

### 1.3 敏感区域

| 路径 | 说明 | 操作限制 |
|:---|:---|:---|
| `config/.env` | 生产配置（含密钥） | 只读 |
| `libs/database/services/telegram-service/market_data.db` | SQLite 指标数据 | 只读 |
| `backups/timescaledb/` | 数据库备份 | 禁止修改 |

> 提醒：服务启动脚本会检查 `config/.env` 权限（需 600/400），不符合直接退出。`scripts/install.sh` 仍会为各服务复制 `.env`，但运行时只读取 `config/.env`，避免双份配置漂移。

---

## 2. Golden Path（推荐执行路径）

### 2.1 最短可复现场景

```bash
# 进入项目根目录
cd /path/to/tradecat

# 1) 初始化：创建各服务 .venv、安装依赖、复制配置模板
./scripts/init.sh

# 2) 填写全局配置（含 BOT_TOKEN / DB / 代理 等）
cp config/.env.example config/.env && chmod 600 config/.env
# 将 DATABASE_URL 端口改为 5433 以与仓库脚本一致（脚本默认 5433，模板默认 5434）
vim config/.env

# 3) 启动核心服务（data + trading + telegram）
./scripts/start.sh start
./scripts/start.sh status
```

> 顶层 `./scripts/start.sh` 只管理 data-service / trading-service / telegram-service。  
> 手动启动：`cd services/markets-service && ./scripts/start.sh start`（多市场采集）；`cd services/order-service && python -m src.market-maker.main`（做市，需 API Key）；ai-service 作为 Telegram 子模块随 Bot 运行。

### 2.2 开发/修改流程

```bash
# 修改前确认已执行 init.sh 并填好 config/.env

# 1. 进入对应服务并激活虚拟环境（如需要）
cd services/trading-service && source .venv/bin/activate

# 2. 修改代码
# ...

# 3. 验证
cd /path/to/tradecat
./scripts/verify.sh

# 4. 若涉及命令/配置/目录变更，同步更新 README.md 与 AGENTS.md
```

### 2.3 提交前检查

```bash
# 语法检查
python3 -m py_compile services/*/src/*.py

# 格式检查（如有 ruff）
ruff check services/

# 运行验证脚本
./scripts/verify.sh
```

---

## 3. Must-Run Commands（必须执行的命令清单）

### 3.1 环境初始化

| 命令 | 说明 | 前置条件 |
|:---|:---|:---|
| `./scripts/install.sh` | 一键安装所有依赖 | Python 3.10+ |
| `./scripts/init.sh` | 初始化所有服务虚拟环境 | Python 3.10+ |
| `./scripts/init.sh <service>` | 初始化单个服务 | Python 3.10+ |

### 3.2 服务管理

| 服务 | 启动 | 停止 | 状态 |
|:---|:---|:---|:---|
| data-service | `cd services/data-service && ./scripts/start.sh start` | `./scripts/start.sh stop` | `./scripts/start.sh status` |
| trading-service | `cd services/trading-service && ./scripts/start.sh start` | `./scripts/start.sh stop` | `./scripts/start.sh status` |
| telegram-service | `cd services/telegram-service && ./scripts/start.sh start` | `./scripts/start.sh stop` | `./scripts/start.sh status` |
| ai-service | 作为 telegram-service 子模块运行 | - | - |
| order-service | `cd services/order-service && python -m src.market-maker.main` | Ctrl+C | - |
| 全部 | `./scripts/start.sh start` | `./scripts/start.sh stop` | `./scripts/start.sh status` |

**注意**: data-service 默认以守护模式启动，自动重启挂掉的服务（30秒检查一次）。

### 3.3 Make 快捷命令

| 命令 | 说明 |
|:---|:---|
| `make init` | 初始化所有服务 |
| `make start` | 启动所有服务 |
| `make stop` | 停止所有服务 |
| `make status` | 查看服务状态 |
| `make verify` | 代码验证（等价 `./scripts/verify.sh`：ruff→py_compile 核心文件与 ai-service 全量→i18n msgfmt 校验与键对齐→可选 pytest） |
| `make clean` | 清理缓存 |

### 3.4 数据库操作

```bash
# 连接 TimescaleDB（默认脚本端口 5433，若 config/.env 改为 5434 需同步调整）
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d market_data

# 查看 K线数据量
SELECT COUNT(*) FROM market_data.candles_1m;

# 连接 SQLite
sqlite3 libs/database/services/telegram-service/market_data.db

# 导出数据库
./scripts/export_timescaledb.sh
```

### 3.5 历史数据导入

从 HuggingFace 下载数据集后导入：

```bash
# 数据集地址: https://huggingface.co/datasets/123olp/binance-futures-ohlcv-2018-2026

# 1. 恢复表结构
zstd -d schema.sql.zst -c | psql -h localhost -p 5433 -U postgres -d market_data

# 2. 导入 K线数据
zstd -d candles_1m.bin.zst -c | psql -h localhost -p 5433 -U postgres -d market_data \
    -c "COPY market_data.candles_1m FROM STDIN WITH (FORMAT binary)"

# 3. 导入期货数据
zstd -d futures_metrics_5m.bin.zst -c | psql -h localhost -p 5433 -U postgres -d market_data \
    -c "COPY market_data.binance_futures_metrics_5m FROM STDIN WITH (FORMAT binary)"
```

---

## 4. Code Change Rules（修改约束）

### 4.1 架构原则

- **微服务独立**：每个服务有独立的 `.venv`、`requirements.txt`
- **配置统一**：所有配置集中在 `config/.env`，各服务共用
- **数据流向**：`data-service → TimescaleDB → trading-service → SQLite → telegram-service / ai-service / vis-service`

### 4.2 模块边界

| 服务 | 职责 | 禁止 |
|:---|:---|:---|
| data-service | 加密货币数据采集、存储到 TimescaleDB | 禁止计算指标 |
| markets-service | 全市场数据采集（美股/A股/宏观） | 禁止计算指标 |
| trading-service | 指标计算、写入 SQLite | 禁止直接推送消息 |
| telegram-service | Bot 交互、读取 SQLite | 禁止写入数据库 |
| ai-service | AI 分析、Wyckoff 方法论 | 作为 telegram-service 子模块 |
| predict-service | 预测市场信号、策略推送 | 禁止改动主数据采集链路 |
| vis-service | 可视化渲染（只读 DB/SQLite，输出 PNG/JSON） | 禁止写入数据库、禁止采集数据 |
| order-service | 交易执行、做市 | 禁止修改数据采集逻辑 |

### 4.3 依赖添加规则

1. 添加依赖前检查是否已存在
2. 添加到对应服务的 `requirements.txt`
3. 运行 `pip freeze | grep <package>` 更新 `requirements.lock.txt`
4. 如需系统库（如 TA-Lib），在 README 中说明安装方法
5. 禁止添加未经验证的依赖

### 4.4 兼容性要求

- Python >= 3.10
- 保持与现有数据库 schema 兼容
- 新增指标需注册到 `indicators/__init__.py`
- 新增卡片需注册到 `cards/registry.py`

---

## 5. Style & Quality（风格与质量标准）

### 5.1 代码风格

- **格式化**：遵循 PEP 8，推荐使用 ruff
- **类型注解**：关键函数添加类型注解
- **文档字符串**：公开函数需有 docstring

### 5.2 命名约定

| 类型 | 约定 | 示例 |
|:---|:---|:---|
| 文件名 | 小写下划线 / 中文 | `k_pattern.py`, `排行榜服务.py` |
| 类名 | PascalCase | `KPattern`, `DataProvider` |
| 函数名 | snake_case | `compute_indicators()` |
| 常量 | UPPER_SNAKE | `MAX_WORKERS` |

### 5.3 错误处理

- 使用 `except Exception as e:` 捕获异常并记录日志
- 禁止裸 `except:`
- 关键操作添加超时处理

### 5.4 日志规范

```python
import logging
logger = logging.getLogger(__name__)

logger.info("操作成功: %s", detail)
logger.warning("警告: %s", message)
logger.error("错误: %s", error, exc_info=True)
```

---

## 6. Project Map（项目结构速览）

```
tradecat/
├── config/                     # 统一配置（所有服务共用）
│   ├── .env                    # 生产配置（含密钥，不提交）
│   ├── .env.example            # 配置模板
│   └── logrotate.conf          # 日志轮转
│
├── scripts/                    # 全局脚本
│   ├── install.sh              # 一键安装
│   ├── init.sh                 # 初始化脚本
│   ├── start.sh                # 统一启动/守护脚本
│   ├── verify.sh               # 验证脚本
│   ├── export_timescaledb.sh   # 数据导出
│   └── timescaledb_compression.sh  # 压缩管理
│
├── services/                   # 8个微服务
│   ├── data-service/           # 加密货币数据采集服务
│   │   ├── src/
│   │   │   ├── collectors/     # 采集器（backfill/ws/metrics）
│   │   │   ├── adapters/       # 适配器（timescale/ccxt）
│   │   │   └── config.py
│   │   ├── scripts/start.sh
│   │   ├── requirements.txt
│   │   └── requirements.lock.txt
│   │
│   ├── markets-service/        # 全市场数据采集服务（美股/A股/宏观）
│   │   ├── src/
│   │   │   ├── providers/      # 数据源适配器 (8个)
│   │   │   ├── collectors/     # 采集任务调度
│   │   │   ├── models/         # 标准化数据模型
│   │   │   └── core/           # 核心框架
│   │   ├── scripts/start.sh
│   │   ├── requirements.txt
│   │   └── requirements.lock.txt
│   │
│   ├── trading-service/        # 指标计算服务
│   │   ├── src/
│   │   │   ├── indicators/     # 38个指标
│   │   │   ├── core/engine.py  # 计算引擎
│   │   │   └── simple_scheduler.py
│   │   ├── scripts/start.sh
│   │   ├── requirements.txt
│   │   └── requirements.lock.txt
│   │
│   ├── telegram-service/       # Telegram Bot
│   │   ├── src/
│   │   │   ├── cards/          # 排行榜卡片
│   │   │   ├── signals/        # 信号检测引擎
│   │   │   ├── bot/app.py      # Bot 主程序
│   │   │   └── main.py
│   │   ├── scripts/start.sh
│   │   ├── requirements.txt
│   │   └── requirements.lock.txt
│   │
│   ├── ai-service/             # AI 分析服务
│   │   ├── src/
│   │   │   ├── data/           # 数据获取
│   │   │   ├── llm/            # LLM 客户端
│   │   │   ├── prompt/         # Prompt 管理
│   │   │   └── bot/            # Bot 集成
│   │   ├── prompts/            # Prompt 模板
│   │   ├── scripts/start.sh
│   │   └── requirements.txt
│   │
│   ├── predict-service/        # 预测市场信号微服务
│   │   └── docs/               # 需求/设计/ADR/Prompt 文档
│   │
│   ├── vis-service/            # 可视化渲染服务（FastAPI）
│   │   ├── src/                # 模板注册与渲染
│   │   ├── scripts/start.sh
│   │   └── requirements.txt
│   │
│   └── order-service/          # 交易执行服务
│       ├── src/
│       │   └── market-maker/   # A-S 做市系统
│       ├── requirements.txt
│       └── requirements.lock.txt
│
├── libs/
│   ├── database/
│   │   └── services/telegram-service/
│   │       └── market_data.db  # SQLite 指标数据
│   └── common/                 # 共享工具库
│       ├── symbols.py          # 币种管理模块
│       └── proxy_manager.py    # 代理管理器
│
├── Makefile                    # 常用命令快捷方式
├── README.md                   # 项目文档
└── AGENTS.md                   # 本文档
```

### 6.1 关键入口文件

| 文件 | 说明 |
|:---|:---|
| `services/data-service/src/__main__.py` | data-service 入口 |
| `services/markets-service/src/__main__.py` | markets-service 入口 |
| `services/trading-service/src/simple_scheduler.py` | trading-service 调度器 |
| `services/telegram-service/src/main.py` | telegram-service 入口 |
| `services/telegram-service/src/bot/app.py` | Bot 主逻辑 |
| `services/ai-service/src/bot/handler.py` | AI 分析处理器 |
| `services/vis-service/src/main.py` | vis-service FastAPI 入口 |

### 6.2 核心模块

| 模块 | 路径 | 说明 |
|:---|:---|:---|
| 指标计算引擎 | `trading-service/src/core/engine.py` | 批量计算指标 |
| K线形态检测 | `trading-service/src/indicators/batch/k_pattern.py` | TA-Lib + patternpy |
| 期货情绪聚合 | `trading-service/src/indicators/batch/futures_aggregate.py` | OI/多空比/情绪 |
| 数据提供者 | `telegram-service/src/cards/data_provider.py` | 读取 SQLite + 币种过滤 |
| i18n 国际化 | `libs/common/i18n.py` | gettext 封装，支持 zh_CN/en |
| 可视化模板 | `vis-service/src/templates/registry.py` | 4 个内置模板（line/kline/macd/vpvr）|
| 单币快照 | `telegram-service/src/bot/single_token_snapshot.py` | 单币多周期数据表格 |
| 共享币种模块 | `libs/common/symbols.py` | 统一币种过滤逻辑 |
| 代理管理器 | `libs/common/proxy_manager.py` | 运行时代理重试+冷却 |

---

## 7. Common Pitfalls（常见坑与修复）

### 7.1 TA-Lib 安装失败

**问题**：`pip install TA-Lib` 报错

**解决**：
```bash
# 先安装系统库
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib && ./configure --prefix=/usr && make && sudo make install
cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# 再安装 Python 包
pip install TA-Lib
```

### 7.2 K线形态显示"无形态"

**问题**：K线形态检测不工作

**解决**：
```bash
# 安装形态检测库
pip install m-patternpy
pip install tradingpattern --no-deps  # 忽略 numpy 版本冲突
```

### 7.3 数据库连接失败

**问题**：无法连接 TimescaleDB

**检查**：
```bash
# 检查端口
ss -tlnp | grep 5433

# 测试连接
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -c "\l"
```

### 7.4 Telegram Bot 无法启动

**问题**：Bot 启动报错

**检查**：
1. 确认 `config/.env` 中 `BOT_TOKEN` 已设置
2. 检查代理配置（如需）：
   ```bash
   export HTTPS_PROXY=http://127.0.0.1:7890
   ```

### 7.5 虚拟环境问题

**问题**：找不到模块

**解决**：
```bash
# 确保激活正确的虚拟环境
source services/<service>/.venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

### 7.6 端口与配置漂移

**问题**：TimescaleDB 端口不一致或多份 .env 导致读取错误

**说明**：
- `config/.env.example` 默认端口 5434，但仓库脚本（`scripts/export_timescaledb.sh`、`scripts/timescaledb_compression.sh` 等）默认 5433。
- 服务启动脚本仅读取 `config/.env`，且会校验权限 600；`scripts/install.sh` 生成的各服务 `.env` 不再被读取，可能造成配置漂移。

**解决**：
```bash
# 1) 统一端口为脚本默认 5433
sed -i 's@localhost:5434@localhost:5433@' config/.env

# 2) 确保权限符合要求
chmod 600 config/.env
```

### 7.7 新旧库并存（markets-service 相关）

**现象**：`services/markets-service/scripts/init_market_db.sh`、`import_bookdepth.py`、`sync_from_old_db.sh` 及 `scripts/ddl/01_enums_schemas.sql`、`migrate_5434.sql` 默认指向 5434（新库），并包含“5433 -> 5434”迁移脚本；而顶层运维脚本默认 5433。

**约束**：
- 执行 markets-service 脚本前确认目标端口；若全局改回 5433，需同步这些脚本与 SQL 文件。
- 避免在未决端口下写入生产库；若不确定，先导出备份：`./scripts/export_timescaledb.sh`。

### 7.8 双库操作指南（旧库 5433 / 新库 5434）

- 旧库（5433，schema=market_data）：被 `scripts/export_timescaledb.sh`、`scripts/timescaledb_compression.sh` 及大部分示例命令使用。沿用旧链路时，请把 `config/.env` 设为 5433，并将 markets-service 相关脚本端口改为 5433。
- 新库（5434，schema=raw/agg/quality）：`config/.env.example` 与 markets-service 初始化/迁移脚本默认指向。若使用新库，需同步修改顶层运维脚本和 README/AGENTS 示例端口为 5434，确保采集/压缩/导出一致。
- 禁止混指：服务与脚本端口不一致会导致数据分叉或压缩失败；调整前先备份 `./scripts/export_timescaledb.sh`（当前默认 5433）。<!-- TODO: 若决定迁移到 5434，给出统一替换清单与执行顺序 -->

---

## 8. PR / Commit Rules（提交规则）

### 8.1 Commit Message 规范

```
<type>(<scope>): <subject>

<body>
```

**Type**：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `refactor`: 重构
- `chore`: 杂项

**示例**：
```
feat(trading): 添加 K线形态检测指标
fix(telegram): 修复排行榜数据加载错误
docs: 更新 README 快速开始指南
```

### 8.2 分支策略

- `main`: 稳定分支
- `feature/*`: 功能开发
- `fix/*`: Bug 修复

### 8.3 提交前检查清单

- [ ] 代码通过语法检查
- [ ] 相关文档已更新
- [ ] 配置变更已同步到 `config/.env.example`
- [ ] 新依赖已添加到 `requirements.txt`

---

## 9. Documentation Sync Rule（文档同步规则）

### 9.1 强制同步

以下变更**必须**同步更新文档：

| 变更类型 | 需更新的文档 |
|:---|:---|
| 新增/修改命令 | README.md, AGENTS.md |
| 新增/修改配置项 | README.md, `config/.env.example` |
| 新增/修改指标 | README.md (指标列表) |
| 目录结构变更 | README.md, AGENTS.md |
| 依赖变更 | README.md, `requirements.txt` |

### 9.2 TODO 标注规则

对于无法确认的信息，使用以下格式标注：

```markdown
<!-- TODO: 需确认 <具体问题>，查看 <文件/路径> -->
```

### 9.3 禁止猜测

- 不确定的端口、路径、命令**必须**标注 TODO
- 不确定的配置项**必须**查看 `config/.env.example` 确认
- 不确定的依赖版本**必须**查看 `requirements.txt` 确认

---

## 10. 环境变量参考

所有配置集中在 `config/.env`，详细说明见配置文件注释。

### 10.1 核心配置

| 变量 | 说明 | 示例 |
|:---|:---|:---|
| `DATABASE_URL` | TimescaleDB 连接串 | `postgresql://postgres:postgres@localhost:5433/market_data` |
| `BOT_TOKEN` | Telegram Bot Token | `123456:ABC...` |
| `HTTP_PROXY` | HTTP 代理 | `http://127.0.0.1:9910` |
| `DEFAULT_LOCALE` | 默认语言 | `zh-CN` |
| `SUPPORTED_LOCALES` | 支持语言列表 | `zh-CN,en` |
| `FALLBACK_LOCALE` | 翻译回退语言 | `zh-CN` |

### 10.2 币种管理

| 变量 | 说明 | 示例 |
|:---|:---|:---|
| `SYMBOLS_GROUPS` | 使用的分组 | `auto`, `all`, `main6`, `defi,meme` |
| `SYMBOLS_GROUP_xxx` | 自定义分组 | `BTCUSDT,ETHUSDT,...` |
| `SYMBOLS_EXTRA` | 额外添加 | `NEWUSDT` |
| `SYMBOLS_EXCLUDE` | 强制排除 | `BADUSDT` |

### 10.3 服务配置

| 变量 | 服务 | 说明 |
|:---|:---|:---|
| `MAX_CONCURRENT` | data-service | 最大并发请求 |
| `MAX_WORKERS` | trading-service | 计算线程数 |
| `COMPUTE_BACKEND` | trading-service | 计算后端 (thread/process) |
| `BINANCE_API_DISABLED` | telegram-service | 禁用 Binance API |
| `BLOCKED_SYMBOLS` | telegram-service | 屏蔽币种黑名单 |
| `DISABLE_SINGLE_TOKEN_QUERY` | telegram-service | 禁用单币查询 (0=启用) |
| `SNAPSHOT_HIDDEN_FIELDS` | telegram-service | 单币快照屏蔽字段 |
| `AI_INDICATOR_TABLES` | ai-service | 启用的指标表（逗号分隔） |
| `AI_INDICATOR_TABLES_DISABLED` | ai-service | 禁用的指标表 |
| `VIS_SERVICE_HOST` | vis-service | 监听地址（默认 0.0.0.0） |
| `VIS_SERVICE_PORT` | vis-service | 监听端口（默认 8087） |
| `VIS_SERVICE_TOKEN` | vis-service | 访问令牌（可选） |

---

## 11. 快速参考卡片

### 常用命令速查

```bash
# 初始化
./scripts/init.sh               # 初始化所有服务
./scripts/init.sh data-service  # 初始化单个服务

# 启动服务
./scripts/start.sh start        # 启动所有服务
./scripts/start.sh stop         # 停止所有服务
./scripts/start.sh status       # 查看状态
./scripts/start.sh restart      # 重启

# Make 快捷命令
make init                       # 初始化
make start                      # 启动
make stop                       # 停止
make status                     # 查看状态

# 单服务管理
cd services/trading-service
./scripts/start.sh start        # 启动
./scripts/start.sh stop         # 停止
./scripts/start.sh status       # 状态

# markets-service（多市场采集）
cd services/markets-service
./scripts/start.sh start        # 启动
./scripts/crypto-daemon.sh      # 加密货币守护进程

# vis-service（可视化渲染）
cd services/vis-service
source .venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8087

# 验证
./scripts/verify.sh             # 运行验证

# 数据库
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d market_data
sqlite3 libs/database/services/telegram-service/market_data.db

# 备份
./scripts/export_timescaledb.sh
```

### 关键路径速查

| 用途 | 路径 |
|:---|:---|
| 统一配置 | `config/.env` |
| 配置模板 | `config/.env.example` |
| 指标代码 | `services/trading-service/src/indicators/` |
| 排行榜卡片 | `services/telegram-service/src/cards/` |
| SQLite 数据 | `libs/database/services/telegram-service/market_data.db` |
| 日志目录 | `services/*/logs/` |
