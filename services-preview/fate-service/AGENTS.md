# AGENTS.md - Fate Service 开发指南

> AI Agent 操作手册 | 最后更新: 2026-01-11

## 项目概述

Fate Service 是 TradeCat 项目的命理服务模块，提供八字排盘、紫微斗数等功能。

**重要：本服务已迁移到 TradeCat 统一配置管理。**

---

## 配置管理

### 统一配置路径

```
tradecat/config/.env          # 生产配置（所有服务共用）
tradecat/config/.env.example  # 配置模板
```

### fate-service 专用配置

```env
# fate-service 配置（独立 Bot）
FATE_BOT_TOKEN=xxx            # 必填，fate-service 专用 Bot Token
FATE_ADMIN_USER_IDS=xxx       # 管理员 ID
FATE_SERVICE_HOST=0.0.0.0     # API 服务地址
FATE_SERVICE_PORT=8001        # API 服务端口
```

### 禁止操作

- ❌ 禁止在 fate-service 目录下创建 `.env` 文件
- ❌ 禁止硬编码绝对路径（如 `/home/xxx/`）
- ❌ 禁止修改 `config/.env` 中的敏感信息

---

## 项目结构

```
fate-service/
├── Makefile                        # 标准化命令
├── pyproject.toml                  # 项目配置
├── .venv/                          # 虚拟环境
├── services/
│   └── telegram-service/
│       ├── src/
│       │   ├── _paths.py           # ⭐ 统一路径管理模块
│       │   ├── bot.py              # Telegram Bot 入口
│       │   ├── bazi_calculator.py  # 八字计算核心
│       │   ├── report_generator.py # 报告生成
│       │   ├── location.py         # 地点匹配
│       │   └── *_integration.py    # 外部库集成模块
│       ├── output/
│       │   ├── logs/               # 日志（自动创建）
│       │   └── txt/                # 报告输出（自动创建）
│       ├── scripts/start.sh        # 启动脚本
│       └── start.py                # 启动入口
├── libs/
│   ├── data/                       # 数据文件
│   │   └── china_coordinates.csv   # 城市坐标（3199条）
│   ├── database/bazi/
│   │   ├── bazi.db                 # SQLite 数据库（自动创建）
│   │   ├── db_v2.py                # 数据库操作（含 ensure_db）
│   │   └── schema_v2.sql           # 数据库 schema
│   └── external/github/            # 外部命理库（只读）
│       ├── lunar-python-master/
│       ├── bazi-1-master/
│       ├── sxwnl-master/
│       ├── fortel-ziweidoushu-main/
│       └── ...
└── tests/                          # 测试目录
```

---

## 路径管理规范

### _paths.py 模块

所有路径必须通过 `_paths.py` 统一管理：

```python
from _paths import (
    PROJECT_ROOT,        # tradecat 根目录
    FATE_SERVICE_ROOT,   # fate-service 根目录
    CONFIG_DIR,          # config/ 目录
    ENV_FILE,            # config/.env 路径
    BAZI_DB_DIR,         # 数据库目录
    LOGS_DIR,            # 日志目录
    LUNAR_PYTHON_DIR,    # 外部库路径
    get_env_file,        # 获取配置文件（带验证）
    ensure_dirs,         # 确保目录存在
    startup_check,       # 启动检查
    check_dependencies,  # 依赖检查
)
```

### 路径使用规则

```python
# ✅ 正确：使用 _paths 模块
from _paths import LUNAR_PYTHON_DIR, get_env_file
load_dotenv(get_env_file())

# ❌ 错误：硬编码路径
load_dotenv("/home/lenovo/.projects/fate-engine/.env")
sys.path.insert(0, "/home/lenovo/.projects/fate-engine/libs")
```

---

## 自动化机制

### 启动检查 (startup_check)

Bot 启动时自动执行：

1. **ensure_dirs()** - 创建必要目录
2. **check_dependencies()** - 检查外部库和配置
3. **db.ensure_db()** - 初始化数据库表

```python
# bot.py 启动流程
from _paths import startup_check
startup_check()  # 自动检查目录、依赖、配置

import db_v2 as db
db.ensure_db()   # 自动初始化数据库
```

### 依赖检查清单

| 类型 | 路径 | 必需 |
|------|------|------|
| 配置文件 | `config/.env` | ✅ |
| lunar-python | `libs/external/github/lunar-python-master` | ✅ |
| bazi-1 | `libs/external/github/bazi-1-master` | ✅ |
| sxwnl | `libs/external/github/sxwnl-master` | ✅ |
| 城市坐标 | `libs/data/china_coordinates.csv` | ✅ |
| fortel-ziwei | `libs/external/github/fortel-ziweidoushu-main` | ⚠️ 可选 |
| dantalion | `libs/external/github/dantalion-master` | ⚠️ 可选 |

---

## 运行命令

### Makefile 命令

```bash
make help       # 查看帮助
make install    # 安装依赖
make start      # 后台启动
make stop       # 停止服务
make status     # 查看状态
make restart    # 重启
make run        # 前台运行
make lint       # 代码检查
make test       # 运行测试
make clean      # 清理缓存
make reset      # 重建虚拟环境
```

### 直接运行

```bash
cd services/telegram-service
../../.venv/bin/python start.py bot   # Telegram Bot
../../.venv/bin/python start.py api   # FastAPI 服务
../../.venv/bin/python start.py both  # 同时启动
```

---

## 开发规范

### 代码修改规则

1. **允许修改**：
   - `services/telegram-service/src/` 下的业务代码
   - `libs/database/` 下的数据库代码
   - `Makefile`、`pyproject.toml`

2. **禁止修改**：
   - `libs/external/github/` 下的外部库（只读）
   - `config/.env` 生产配置

### 外部库集成

```python
# 标准集成模式
from _paths import LUNAR_PYTHON_DIR, SRC_DIR
import importlib.util

spec = importlib.util.spec_from_file_location(
    "module_name", 
    str(EXTERNAL_DIR / "some-lib/module.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

### 环境变量读取

```python
# ✅ 正确：通过 _paths 加载
from _paths import get_env_file
from dotenv import load_dotenv
load_dotenv(get_env_file())
token = os.getenv("FATE_BOT_TOKEN")

# ❌ 错误：直接 load_dotenv()
load_dotenv()  # 可能加载错误的文件
```

---

## 故障排查

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `未设置 FATE_BOT_TOKEN` | 配置未填写 | 编辑 `config/.env` 添加 |
| `no such table: records` | 数据库未初始化 | 自动初始化或运行 `db_v2.py` |
| `配置文件不存在` | `.env` 缺失 | `cp config/.env.example config/.env` |
| `缺少必需依赖` | 外部库缺失 | 检查 `libs/external/github/` |

### 日志位置

```bash
# Bot 日志
tail -f services/telegram-service/output/logs/bot.log

# 启动输出
cat services/telegram-service/output/logs/nohup.out
```

---

## 测试

```bash
# 运行测试
make test

# 语法检查
make syntax

# 代码检查
make lint
```

---

## 版本历史

- **2026-01-11**: 迁移到 TradeCat 统一配置管理
  - 所有路径改为相对路径
  - 添加 `_paths.py` 统一路径管理
  - 添加 `startup_check()` 自动检查
  - 添加 `db.ensure_db()` 自动初始化
  - 使用独立 `FATE_BOT_TOKEN` 配置
