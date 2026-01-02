# TradeCat - AI Agent 操作手册

> 本文档面向 AI 编码 Agent，以可执行指令的视角编写，约束与指导 Agent 行为。

---

## 1. Mission & Scope（目标与边界）

### 1.1 允许的操作

- 修改 `services/*/src/` 下的业务代码
- 修改 `services/*/config/.env.example` 配置模板
- 添加/修改技术指标 (`services/trading-service/src/indicators/`)
- 添加/修改排行榜卡片 (`services/telegram-service/src/cards/`)
- 修改启动脚本 (`services/*/scripts/`)
- 更新文档 (`README.md`, `AGENTS.md`, `docs/`)

### 1.2 禁止的操作

- **禁止修改** `services/*/config/.env` 生产配置文件
- **禁止修改** 数据库 schema（除非明确要求）
- **禁止删除** `libs/database/` 下的数据文件
- **禁止修改** `.gitignore` 中已忽略的敏感文件
- **禁止** 大范围重构，除非任务明确要求
- **禁止** 添加未经验证的第三方依赖

### 1.3 敏感区域

| 路径 | 说明 | 操作限制 |
|:---|:---|:---|
| `services/*/config/.env` | 生产配置（含密钥） | 只读 |
| `libs/database/services/telegram-service/market_data.db` | SQLite 指标数据 | 只读 |
| `backups/timescaledb/` | 数据库备份 | 禁止修改 |

---

## 2. Golden Path（推荐执行路径）

### 2.1 环境准备

```bash
# 1. 进入项目目录
cd /path/to/tradecat

# 2. 一键安装（首次）
./scripts/install.sh

# 3. 或手动初始化单个服务
./scripts/init.sh trading-service
```

### 2.2 开发流程

```bash
# 1. 激活虚拟环境
source services/trading-service/.venv/bin/activate

# 2. 修改代码
# ...

# 3. 运行验证
./scripts/verify.sh

# 4. 测试运行
cd services/trading-service
./scripts/start.sh start
./scripts/start.sh status
./scripts/start.sh stop

# 5. 更新文档（如有变更）
# 同步更新 README.md 和 AGENTS.md
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
| order-service | `cd services/order-service && python -m src.market-maker.main` | Ctrl+C | - |
| 全部（守护） | `./scripts/start.sh daemon` | `./scripts/start.sh daemon-stop` | `./scripts/start.sh daemon-status` |

### 3.3 验证与测试

| 命令 | 说明 |
|:---|:---|
| `./scripts/verify.sh` | 运行格式检查、语法检查、文档链接检查 |
| `python3 -m py_compile <file>` | 单文件语法检查 |

### 3.4 数据库操作

```bash
# 连接 TimescaleDB
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d market_data

# 查看 K线数据量
SELECT COUNT(*) FROM market_data.candles_1m;

# 连接 SQLite
sqlite3 libs/database/services/telegram-service/market_data.db

# 导出数据库
./scripts/export_timescaledb.sh
```

---

## 4. Code Change Rules（修改约束）

### 4.1 架构原则

- **微服务独立**：每个服务有独立的 `.venv`、`config/`、`requirements.txt`
- **数据流向**：`data-service → TimescaleDB → trading-service → SQLite → telegram-service`
- **配置分离**：配置文件统一放在 `services/*/config/` 目录

### 4.2 模块边界

| 服务 | 职责 | 禁止 |
|:---|:---|:---|
| data-service | 数据采集、存储到 TimescaleDB | 禁止计算指标 |
| trading-service | 指标计算、写入 SQLite | 禁止直接推送消息 |
| telegram-service | Bot 交互、读取 SQLite | 禁止写入数据库 |
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

- 使用 try-except 捕获预期异常
- 记录日志而非静默失败
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
├── services/                   # 4个微服务
│   ├── data-service/           # 数据采集服务
│   │   ├── src/
│   │   │   ├── collectors/     # 采集器（backfill/ws/metrics）
│   │   │   ├── adapters/       # 适配器（timescale/ccxt）
│   │   │   └── config.py
│   │   ├── config/.env.example
│   │   ├── scripts/start.sh
│   │   ├── requirements.txt
│   │   └── requirements.lock.txt  # 依赖版本锁定
│   │
│   ├── trading-service/        # 指标计算服务
│   │   ├── src/
│   │   │   ├── indicators/     # 38个指标
│   │   │   ├── core/engine.py  # 计算引擎
│   │   │   └── simple_scheduler.py
│   │   ├── config/.env.example
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
│   │   ├── config/.env.example
│   │   ├── requirements.txt
│   │   └── requirements.lock.txt
│   │
│   └── order-service/          # 交易执行服务
│       ├── src/
│       │   └── market-maker/   # A-S 做市系统
│       ├── config/.env.example
│       ├── requirements.txt
│       └── requirements.lock.txt
│
├── libs/
│   ├── database/
│   │   └── services/telegram-service/
│   │       └── market_data.db  # SQLite 指标数据
│   └── common/                 # 共享工具库
│       └── proxy_manager.py    # 代理管理器（运行时重试+冷却）
│
├── config/
│   ├── .env.example            # 全局配置模板
│   └── logrotate.conf          # 日志轮转配置
│
├── scripts/
│   ├── init.sh                 # 初始化脚本
│   ├── start.sh                # 统一启动/守护脚本
│   ├── verify.sh               # 验证脚本
│   ├── export_timescaledb.sh   # 数据导出
│   └── timescaledb_compression.sh  # 压缩管理
│
# install.sh 已移至 scripts/                  # 一键安装
├── Makefile                    # 常用命令
└── README.md                   # 项目文档
```

### 6.1 关键入口文件

| 文件 | 说明 |
|:---|:---|
| `services/data-service/src/__main__.py` | data-service 入口 |
| `services/trading-service/src/simple_scheduler.py` | trading-service 调度器 |
| `services/telegram-service/src/main.py` | telegram-service 入口 |
| `services/telegram-service/src/bot/app.py` | Bot 主逻辑 |

### 6.2 核心模块

| 模块 | 路径 | 说明 |
|:---|:---|:---|
| 指标计算引擎 | `trading-service/src/core/engine.py` | 批量计算指标 |
| K线形态检测 | `trading-service/src/indicators/batch/k_pattern.py` | TA-Lib + patternpy |
| 数据提供者 | `telegram-service/src/cards/data_provider.py` | 读取 SQLite 数据（连接池） |
| 排行榜服务 | `telegram-service/src/cards/排行榜服务.py` | 生成排行榜 |
| 信号引擎 | `telegram-service/src/signals/engine.py` | 信号检测与触发 |
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
1. 确认 `config/.env` 中 `TELEGRAM_BOT_TOKEN` 已设置
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
- [ ] 配置变更已同步到 `.env.example`
- [ ] 新依赖已添加到 `requirements.txt`

---

## 9. Documentation Sync Rule（文档同步规则）

### 9.1 强制同步

以下变更**必须**同步更新文档：

| 变更类型 | 需更新的文档 |
|:---|:---|
| 新增/修改命令 | README.md, AGENTS.md |
| 新增/修改配置项 | README.md, `.env.example` |
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
- 不确定的配置项**必须**查看 `.env.example` 确认
- 不确定的依赖版本**必须**查看 `requirements.txt` 确认

---

## 10. 环境变量参考

### 10.1 data-service

| 变量 | 说明 | 默认值 |
|:---|:---|:---|
| `DATABASE_URL` | TimescaleDB 连接串 | - |
| `HTTP_PROXY` | HTTP 代理 | - |
| `RATE_LIMIT_PER_MINUTE` | API 限流 | 1800 |
| `MAX_CONCURRENT` | 最大并发 | 5 |

### 10.2 trading-service

| 变量 | 说明 | 默认值 |
|:---|:---|:---|
| `DATABASE_URL` | TimescaleDB 连接串 | - |
| `INDICATOR_SQLITE_PATH` | SQLite 输出路径 | 自动使用相对路径 |
| `MAX_WORKERS` | 计算线程数 | 4 |
| `COMPUTE_BACKEND` | 计算后端 (thread/process/hybrid) | thread |
| `MAX_IO_WORKERS` | IO 任务线程数 | 8 |
| `MAX_CPU_WORKERS` | CPU 任务进程数 | 4 |

### 10.3 telegram-service

| 变量 | 说明 | 默认值 |
|:---|:---|:---|
| `BOT_TOKEN` | Telegram Bot Token | - |
| `DATABASE_URL` | TimescaleDB 连接串 | - |
| `HTTP_PROXY` | HTTP 代理 | - |
| `BINANCE_API_DISABLED` | 禁用 Binance API | 1 |
| `BLOCKED_SYMBOLS` | 屏蔽币种（逗号分隔） | BNXUSDT,ALPACAUSDT |

---

## 11. 快速参考卡片

### 常用命令速查

```bash
# 初始化
./scripts/init.sh               # 初始化所有服务
./scripts/init.sh data-service  # 初始化单个服务

# 启动服务（推荐守护模式）
./scripts/start.sh daemon       # 启动 + 守护（自动重启）
./scripts/start.sh daemon-stop  # 停止守护 + 全部服务
./scripts/start.sh daemon-status # 查看状态

# 仅启动（不守护）
./scripts/start.sh start        # 启动全部
./scripts/start.sh stop         # 停止全部
./scripts/start.sh status       # 查看状态

# 单服务管理
cd services/trading-service
./scripts/start.sh daemon       # 启动 + 守护
./scripts/start.sh start        # 仅启动
./scripts/start.sh stop         # 停止
./scripts/start.sh status       # 状态

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
| 指标代码 | `services/trading-service/src/indicators/batch/` |
| 排行榜卡片 | `services/telegram-service/src/cards/` |
| SQLite 数据 | `libs/database/services/telegram-service/market_data.db` |
| 日志目录 | `services/*/logs/` |
| 配置模板 | `services/*/config/.env.example` |
