# TradeCat - AI Agent 操作手册

> 本文档面向 AI 编码 Agent，以可执行指令的视角编写，约束与指导 Agent 行为。

---

## 1. Mission & Scope（目标与边界）

### 1.1 允许的操作

- 修改 `services/*/src/` 下的业务代码
- 修改 `services-preview/*/src/` 下的业务代码
- 修改 `config/.env.example` 全局配置模板
- 添加/修改技术指标 (`services/trading-service/src/indicators/`)
- 添加/修改排行榜卡片 (`services/telegram-service/src/cards/`)
- 修改启动脚本 (`services/*/scripts/`, `scripts/`)
- 更新文档 (`README.md`, `README_EN.md`, `AGENTS.md`)
- 修改 `Makefile`、`pyproject.toml`

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
| `libs/database/services/signal-service/cooldown.db` | 信号冷却持久化 | 只读 |
| `backups/timescaledb/` | 数据库备份 | 禁止修改 |

> 提醒：服务启动脚本会检查 `config/.env` 权限（需 600/400），不符合直接退出。

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
vim config/.env

# 3) 启动核心服务（data + trading + telegram）
./scripts/start.sh start
./scripts/start.sh status
```

> 顶层 `./scripts/start.sh` 管理 data-service / trading-service / telegram-service。

### 2.2 预览版服务启动

```bash
# signal-service（信号检测）
cd services/signal-service && ./scripts/start.sh start

# markets-service（多市场采集）
cd services-preview/markets-service && ./scripts/start.sh start

# vis-service（可视化，端口 8087）
cd services-preview/vis-service && ./scripts/start.sh start

# order-service（做市，需 API Key）
cd services-preview/order-service && python -m src

# fate-service（命理服务）
cd services-preview/fate-service && make run

# predict-service（预测市场，Node.js）
cd services-preview/predict-service/services/polymarket && npm start
```

### 2.3 开发/修改流程

```bash
# 1. 进入对应服务并激活虚拟环境
cd services/trading-service && source .venv/bin/activate

# 2. 修改代码...

# 3. 使用服务级 Makefile
make lint      # 代码检查
make format    # 代码格式化
make test      # 运行测试

# 4. 验证
cd /path/to/tradecat
./scripts/verify.sh

# 5. 若涉及命令/配置/目录变更，同步更新 README.md / README_EN.md / AGENTS.md
```

---

## 3. Must-Run Commands（必须执行的命令清单）

### 3.1 全局脚本

| 命令 | 说明 |
|:---|:---|
| `./scripts/init.sh` | 初始化所有核心服务虚拟环境 |
| `./scripts/init.sh <service>` | 初始化单个服务 |
| `./scripts/init.sh --all` | 初始化全部服务（含 preview） |
| `./scripts/start.sh start\|stop\|status\|restart` | 核心服务管理 |
| `./scripts/start.sh daemon\|daemon-stop` | 守护进程模式（自动重启崩溃服务） |
| `./scripts/check_env.sh` | 环境检查（Python/依赖/配置/网络/数据库） |
| `./scripts/verify.sh` | 代码验证（ruff + py_compile + i18n） |
| `python scripts/download_hf_data.py` | 从 HuggingFace 下载历史数据并导入 |
| `python scripts/check_i18n_keys.py` | 检查 i18n 翻译键对齐 |
| `./scripts/export_timescaledb.sh` | 导出 TimescaleDB 数据（默认端口 5433） |
| `./scripts/export_timescaledb_main4.sh` | 导出 Main4 精简数据集（默认端口 5433） |
| `./scripts/timescaledb_compression.sh` | 压缩管理（默认端口 5433） |

### 3.2 Make 快捷命令

| 命令 | 说明 |
|:---|:---|
| `make init` | 初始化所有服务 |
| `make install` | 一键安装（等价 `./scripts/install.sh`） |
| `make start` | 启动所有服务 |
| `make stop` | 停止所有服务 |
| `make status` | 查看服务状态 |
| `make daemon` | 启动守护进程（自动重启） |
| `make daemon-stop` | 停止守护进程 |
| `make verify` | 代码验证 |
| `make clean` | 清理缓存 |
| `make export-db` | 导出 TimescaleDB 数据 |

### 3.3 服务级 Makefile（统一接口）

每个服务都有标准化的 Makefile，支持以下 targets：

```bash
cd services/<service-name>  # 或 services-preview/<service-name>

make help        # 显示帮助
make venv        # 创建虚拟环境
make install     # 安装依赖
make install-dev # 安装开发依赖
make clean       # 清理缓存
make reset       # 重建虚拟环境（依赖坏了用这个）
make lock        # 导出当前依赖到 requirements.lock.txt

make lint        # 代码检查 (ruff)
make format      # 代码格式化 (ruff)
make test        # 运行测试 (pytest)
make test-cov    # 运行测试 + 覆盖率
make typecheck   # 类型检查 (mypy)
make check       # 完整检查 (lint + test)
make syntax      # 语法验证（快速）

make run         # 前台运行（调试用）
make start       # 后台启动
make stop        # 停止服务
make status      # 查看状态
```

### 3.4 数据库操作

> **端口说明**：`config/.env.example` 默认端口为 **5434**（新库），但导出/压缩脚本默认 **5433**（旧库）。请根据实际部署选择统一端口。

```bash
# 连接 TimescaleDB（根据 config/.env 中 DATABASE_URL 端口）
# 新库（5434）
PGPASSWORD=postgres psql -h localhost -p 5434 -U postgres -d market_data

# 旧库（5433，脚本默认）
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d market_data

# 查看 K线数据量
SELECT COUNT(*) FROM market_data.candles_1m;

# 连接 SQLite
sqlite3 libs/database/services/telegram-service/market_data.db
```

---

## 4. Code Change Rules（修改约束）

### 4.1 架构原则

- **微服务独立**：每个服务有独立的 `.venv`、`requirements.txt`、`pyproject.toml`、`Makefile`
- **配置统一**：所有配置集中在 `config/.env`，各服务共用
- **数据流向**：`data-service → TimescaleDB → trading-service → SQLite → telegram/ai/signal/vis`

### 4.2 服务清单（11 个）

| 服务 | 位置 | 职责 | 入口 |
|:---|:---|:---|:---|
| data-service | services/ | 加密货币数据采集 | `src/__main__.py` |
| trading-service | services/ | 指标计算 | `src/__main__.py` |
| telegram-service | services/ | Bot 交互 | `src/main.py` |
| ai-service | services/ | AI 分析（telegram 子模块） | `src/__main__.py` |
| signal-service | services/ | 信号检测（129条规则） | `src/__main__.py` |
| api-service | services-preview/ | REST API 服务（端口 8000） | `src/__main__.py` |
| markets-service | services-preview/ | 全市场采集 | `src/__main__.py` |
| vis-service | services-preview/ | 可视化渲染（端口 8087） | `src/__main__.py` |
| order-service | services-preview/ | 交易执行 | `src/__main__.py` |
| predict-service | services-preview/ | 预测市场（Node.js） | `services/*/` |
| fate-service | services-preview/ | 命理服务（端口 8001） | `services/telegram-service/` |

### 4.3 模块边界

| 服务 | 职责 | 禁止 |
|:---|:---|:---|
| data-service | 加密货币数据采集、存储到 TimescaleDB | 禁止计算指标 |
| markets-service | 全市场数据采集（美股/A股/宏观） | 禁止计算指标 |
| trading-service | 指标计算、写入 SQLite | 禁止直接推送消息 |
| telegram-service | Bot 交互、信号推送 UI | 禁止包含信号检测逻辑 |
| ai-service | AI 分析、Wyckoff 方法论 | 作为 telegram-service 子模块 |
| signal-service | 信号检测、规则引擎（独立服务） | 只读数据库，禁止 Telegram 依赖 |
| api-service | REST API 数据查询 | 只读数据库，禁止写入 |
| vis-service | 可视化渲染 | 禁止写入数据库 |
| order-service | 交易执行、做市 | 禁止修改数据采集逻辑 |

> **注意**：telegram-service/signals 模块已解耦，仅保留适配层 (`adapter.py`) 和 UI (`ui.py`)，信号检测逻辑全部在 signal-service 中。
> 冷却持久化：`signal-service/src/storage/cooldown.py` 负责将冷却键写入 `libs/database/services/signal-service/cooldown.db`，SQLite 引擎启动时加载，`_set_cooldown()` 同步落盘；公共接口 `get_cooldown_storage()` 供其他模块复用。

### 4.4 依赖添加规则

1. 添加依赖前检查是否已存在
2. 添加到对应服务的 `requirements.txt`
3. 运行 `make lock` 更新 `requirements.lock.txt`
4. 如需系统库（如 TA-Lib），在 README 中说明安装方法
5. 禁止添加未经验证的依赖

### 4.5 兼容性要求

- Python >= 3.10（CI 使用 3.12，pyproject.toml 声明 >=3.9）
- 保持与现有数据库 schema 兼容
- 新增指标需注册到 `indicators/__init__.py`
- 新增卡片需注册到 `cards/registry.py`

---

## 5. Style & Quality（风格与质量标准）

### 5.1 代码风格

- **格式化**：遵循 PEP 8，使用 ruff
- **行长**：120 字符
- **类型注解**：关键函数添加类型注解
- **文档字符串**：公开函数需有 docstring

### 5.2 项目配置（pyproject.toml 统一标准）

所有服务的 `pyproject.toml` 使用统一配置：

```toml
[project]
requires-python = ">=3.12"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.mypy]
python_version = "3.12"
ignore_missing_imports = true
```

### 5.3 命名约定

| 类型 | 约定 | 示例 |
|:---|:---|:---|
| 文件名 | 小写下划线或中文 | `k_pattern.py`, `资金费率卡片.py` |
| 类名 | PascalCase | `KPattern`, `DataProvider` |
| 函数名 | snake_case | `compute_indicators()` |
| 常量 | UPPER_SNAKE | `MAX_WORKERS` |

### 5.4 错误处理

- 使用 `except Exception as e:` 捕获异常并记录日志
- 禁止裸 `except:`
- 关键操作添加超时处理

### 5.5 日志规范

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
├── config/                         # 统一配置（所有服务共用）
│   ├── .env                        # 生产配置（含密钥，不提交）
│   ├── .env.example                # 配置模板（默认端口 5434）
│   └── logrotate.conf              # 日志轮转
│
├── scripts/                        # 全局脚本
│   ├── init.sh                     # 初始化脚本
│   ├── install.sh                  # 一键安装
│   ├── start.sh                    # 统一启动脚本
│   ├── verify.sh                   # 验证脚本（ruff + py_compile + i18n）
│   ├── check_env.sh                # 环境检查
│   ├── check_i18n_keys.py          # i18n 翻译键对齐检查
│   ├── download_hf_data.py         # HuggingFace 数据下载
│   ├── export_timescaledb.sh       # 数据导出（默认端口 5433）
│   ├── export_timescaledb_main4.sh # 导出 Main4 精简数据集（默认端口 5433）
│   └── timescaledb_compression.sh  # 压缩管理（默认端口 5433）
│
├── services/                       # 稳定版微服务 (5个)
│   ├── data-service/               # 加密货币数据采集
│   ├── trading-service/            # 指标计算（34个指标模块）
│   ├── telegram-service/           # Telegram Bot（39张卡片）
│   ├── ai-service/                 # AI 分析
│   └── signal-service/             # 信号检测（129条规则）
│
├── services-preview/               # 预览版微服务 (6个)
│   ├── api-service/                # REST API 服务（端口 8000）
│   ├── markets-service/            # 全市场数据采集
│   ├── vis-service/                # 可视化渲染（端口 8087）
│   ├── order-service/              # 交易执行
│   ├── predict-service/            # 预测市场（Node.js）
│   └── fate-service/               # 命理服务（端口 8001）
│
├── libs/
│   ├── database/                   # 数据库文件
│   │   ├── db/                     # DDL schema 定义
│   │   ├── csv/                    # CSV 数据
│   │   └── services/
│   │       ├── telegram-service/
│   │       │   └── market_data.db      # 指标数据（Telegram 展示使用）
│   │       └── signal-service/
│   │           └── cooldown.db         # 冷却状态持久化（防重复推送）
│   ├── common/                     # 共享工具库
│   │   ├── i18n.py                 # 国际化模块
│   │   ├── symbols.py              # 币种管理模块
│   │   ├── proxy_manager.py        # 代理管理器
│   │   └── utils/                  # 工具函数
│   └── external/                   # 外部依赖/数据
│
├── .github/workflows/              # CI 配置
│   ├── ci.yml                      # ruff + py_compile 抽样检查
│   ├── pypi-ci.yml                 # PyPI CI
│   └── pypi-publish.yml            # PyPI 发布
│
├── Makefile                        # 常用命令快捷方式
├── pyproject.toml                  # 根级项目配置
├── README.md                       # 项目文档（中文）
├── README_EN.md                    # 项目文档（英文）
└── AGENTS.md                       # 本文档
```

### 6.1 服务标准化结构

每个服务遵循统一结构：

```
<service>/
├── .python-version         # Python 版本 (3.12)
├── .gitignore              # Git 忽略规则
├── .venv/                  # 虚拟环境（不提交）
├── Makefile                # 服务级 Make 命令
├── pyproject.toml          # 项目配置（含 ruff/pytest/mypy）
├── requirements.txt        # 运行依赖
├── requirements-dev.txt    # 开发依赖
├── requirements.lock.txt   # 锁定依赖
├── src/                    # 源代码
│   ├── __init__.py
│   └── __main__.py         # 入口
├── tests/                  # 测试
│   ├── __init__.py
│   └── conftest.py
├── scripts/
│   └── start.sh            # 启动脚本
└── logs/                   # 日志目录
```

---

## 7. Common Pitfalls（常见坑与修复）

### 7.1 TA-Lib 安装失败

```bash
# 先安装系统库
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib && ./configure --prefix=/usr && make && sudo make install
cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# 再安装 Python 包
pip install TA-Lib
```

### 7.2 数据库连接失败

```bash
# 检查端口（根据 config/.env 配置选择 5433 或 5434）
ss -tlnp | grep 5434

# 测试连接
PGPASSWORD=postgres psql -h localhost -p 5434 -U postgres -c "\l"
```

### 7.3 虚拟环境问题

```bash
# 重建虚拟环境（依赖坏了用这个）
cd services/<service>
make reset
```

### 7.4 .env 权限问题

```bash
# 服务启动脚本要求 600 权限
chmod 600 config/.env
```

### 7.5 环境检查

```bash
# 部署前运行环境检查，确保所有依赖就绪
./scripts/check_env.sh

# 检查内容：
# - Python 版本 (3.10+)
# - pip/venv 可用性
# - 虚拟环境完整性
# - config/.env 配置
# - 数据库连接 (pg_isready)
# - 网络连接 (Telegram/Binance API)
# - 磁盘空间
```

### 7.6 日志轮转配置

```bash
# 1. 生成配置文件（替换路径占位符）
cd /path/to/tradecat
sed -e "s|{{PROJECT_ROOT}}|$(pwd)|g" \
    -e "s|{{USER}}|$(whoami)|g" \
    config/logrotate.conf > /tmp/tradecat-logrotate.conf

# 2. 手动执行轮转
sudo logrotate -f /tmp/tradecat-logrotate.conf

# 3. 安装到系统（可选，自动每日执行）
sudo cp /tmp/tradecat-logrotate.conf /etc/logrotate.d/tradecat

# 轮转策略：
# - 核心服务日志：每天或 50MB，保留 14 天
# - 预览服务日志：每天或 50MB，保留 7 天
# - 根目录日志：每天或 20MB，保留 7 天
```

### 7.7 守护进程模式

```bash
# 启动守护进程（自动重启崩溃的服务）
./scripts/start.sh daemon

# 停止守护进程和所有服务
./scripts/start.sh daemon-stop

# 守护策略：
# - 检查间隔：30 秒
# - 最大重试：5 次/5分钟窗口
# - 指数退避：10s → 20s → 40s → ... → 300s (最大)
# - 超过上限后暂停重启，告警写入 alerts.log
```

### 7.8 端口冲突（双库架构）

```bash
# 旧库（5433）：与早期数据采集链兼容，export/compression 脚本默认使用
# 新库（5434）：多 schema 架构（raw/agg/quality），.env.example 默认

# 确认当前使用端口
grep "DATABASE_URL" config/.env | grep -oP ':\K\d+(?=/)'

# 若需切换端口，需同步修改：
# - config/.env 中 DATABASE_URL
# - scripts/export_timescaledb.sh
# - scripts/timescaledb_compression.sh
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
- `style`: 代码格式

**示例**：
```
feat(trading): 添加 K线形态检测指标
fix(telegram): 修复排行榜数据加载错误
docs: 更新 README 快速开始指南
chore: standardize project structure for all services
```

### 8.2 提交前检查清单

- [ ] 代码通过 `make lint`
- [ ] 测试通过 `make test`（如有）
- [ ] 相关文档已更新
- [ ] 配置变更已同步到 `config/.env.example`
- [ ] 新依赖已添加到 `requirements.txt` 并 `make lock`

### 8.3 CI 说明

CI（`.github/workflows/ci.yml`）仅执行：
- ruff 静态检查（忽略 E501, E402）
- py_compile 语法检查（前 50 个 .py 文件抽样）

完整测试需本地运行 `./scripts/verify.sh`。

---

## 9. Documentation Sync Rule（文档同步规则）

### 9.1 强制同步

以下变更**必须**同步更新文档：

| 变更类型 | 需更新的文档 |
|:---|:---|
| 新增/修改命令 | README.md, README_EN.md, AGENTS.md |
| 新增/修改配置项 | README.md, README_EN.md, `config/.env.example` |
| 新增/修改指标 | README.md (指标列表) |
| 目录结构变更 | README.md, README_EN.md, AGENTS.md |
| 新增/修改服务 | README.md, README_EN.md, AGENTS.md |

### 9.2 文档更新原则

- 以实时代码为唯一源头
- 不确定的端口、路径、命令**必须**验证后再写入
- 三份文档（README.md、README_EN.md、AGENTS.md）保持同步

---

## 10. 环境变量参考

所有配置集中在 `config/.env`，详细说明见 `config/.env.example`。

### 10.1 核心配置

| 变量 | 说明 | 示例 |
|:---|:---|:---|
| `DATABASE_URL` | TimescaleDB 连接串 | `postgresql://postgres:postgres@localhost:5434/market_data` |
| `BOT_TOKEN` | Telegram Bot Token | `123456:ABC...` |
| `HTTP_PROXY` | HTTP 代理 | `http://127.0.0.1:9910` |
| `DEFAULT_LOCALE` | 默认语言 | `en` |
| `SIGNAL_DATA_MAX_AGE` | 信号数据最大允许时长（秒，超限不触发） | `600` |
| `COOLDOWN_SECONDS` | signal-service PG 全局冷却时间（秒，持久化） | `300` |

### 10.2 币种管理

| 变量 | 说明 |
|:---|:---|
| `SYMBOLS_GROUPS` | 使用的分组（main4/main6/main20/auto/all） |
| `SYMBOLS_GROUP_<name>` | 自定义分组定义（如 `SYMBOLS_GROUP_defi`） |
| `SYMBOLS_EXTRA` | 额外添加的币种 |
| `SYMBOLS_EXCLUDE` | 强制排除的币种 |

### 10.3 数据采集配置

| 变量 | 服务 | 说明 |
|:---|:---|:---|
| `BACKFILL_MODE` | data-service | 回填模式（all/days/none） |
| `BACKFILL_DAYS` | data-service | 回填天数（BACKFILL_MODE=days 时生效） |
| `BACKFILL_START_DATE` | data-service | 回填起始日期（可选） |
| `MAX_CONCURRENT` | data-service | 最大并发请求数（默认 5） |
| `RATE_LIMIT_PER_MINUTE` | data-service | 每分钟最大请求数（默认 1800） |
| `INTERVALS` | data-service | K线周期（逗号分隔） |
| `KLINE_INTERVALS` | data-service | WebSocket 订阅周期 |
| `FUTURES_INTERVALS` | data-service | 期货指标周期（最小 5m） |

### 10.4 服务配置

| 变量 | 服务 | 说明 |
|:---|:---|:---|
| `MAX_WORKERS` | trading-service | 计算线程数 |
| `COMPUTE_BACKEND` | trading-service | 计算后端（thread/process/hybrid） |
| `HIGH_PRIORITY_TOP_N` | trading-service | auto 模式高优先级币种数量 |
| `VIS_SERVICE_PORT` | vis-service | 监听端口（默认 8087） |
| `FATE_BOT_TOKEN` | fate-service | 命理 Bot Token |
| `FATE_SERVICE_PORT` | fate-service | API 端口（默认 8001） |
| `MARKETS_SERVICE_DATABASE_URL` | markets-service | 独立数据库连接 |
| `CRYPTO_WRITE_MODE` | markets-service | 写入模式（raw/legacy） |

---

## 11. 快速参考卡片

```bash
# 初始化
./scripts/init.sh

# 启动/停止
./scripts/start.sh start|stop|status

# 单服务管理
cd services/<name> && make start|stop|status

# 代码检查
cd services/<name> && make lint format test

# 验证
./scripts/verify.sh

# 数据库（根据实际端口选择 5433 或 5434）
PGPASSWORD=postgres psql -h localhost -p 5434 -U postgres -d market_data
sqlite3 libs/database/services/telegram-service/market_data.db

# 备份
./scripts/export_timescaledb.sh
```
