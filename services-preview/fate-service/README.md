# Fate Service

> 专业级八字排盘服务 | TradeCat 微服务之一

## 项目简介

Fate Service 是 TradeCat 项目的命理服务模块，提供专业的八字排盘、紫微斗数、择日等功能。

## 快速开始

### 1. 环境要求

- Python 3.12+
- Node.js 18+ (寿星万年历支持)

### 2. 安装依赖

```bash
cd services-preview/fate-service

# 创建虚拟环境并安装依赖
make install

# 或手动安装
python3 -m venv .venv
.venv/bin/pip install -r services/telegram-service/requirements.txt
```

### 3. 配置

fate-service 使用 TradeCat 统一配置文件 `config/.env`：

```bash
# 复制配置模板（如果还没有）
cp config/.env.example config/.env

# 编辑配置，填入 fate-service 专用配置
vim config/.env
```

需要配置的变量：

```env
# fate-service 配置（独立 Bot）
FATE_BOT_TOKEN=your_bot_token_here      # 从 @BotFather 获取
FATE_ADMIN_USER_IDS=123456789           # 管理员 Telegram ID
```

### 4. 启动服务

```bash
# 方式一：使用 Makefile（推荐）
make start          # 后台启动
make stop           # 停止服务
make status         # 查看状态
make run            # 前台运行（调试用）

# 方式二：使用启动脚本
./services/telegram-service/scripts/start.sh start

# 方式三：直接运行
cd services/telegram-service
.venv/bin/python start.py bot     # 启动 Telegram Bot
.venv/bin/python start.py api     # 启动 FastAPI 服务
.venv/bin/python start.py both    # 同时启动
```

### 5. 验证运行

```bash
# 查看状态
make status

# 查看日志
tail -f services/telegram-service/output/logs/bot.log
```

## 自动化特性

服务启动时会自动执行以下检查：

1. **目录检查** - 自动创建 logs、output、database 目录
2. **依赖检查** - 验证外部库和配置文件是否存在
3. **数据库初始化** - 自动创建数据库表（如不存在）
4. **配置验证** - 检查 FATE_BOT_TOKEN 是否配置

如果检查失败，服务会输出详细错误信息并拒绝启动。

## 项目结构

```
fate-service/
├── Makefile                    # 常用命令
├── .venv/                      # Python 虚拟环境
├── services/
│   └── telegram-service/       # Telegram Bot 服务
│       ├── src/
│       │   ├── bot.py          # Bot 主程序
│       │   ├── _paths.py       # 统一路径管理
│       │   ├── bazi_calculator.py  # 八字计算核心
│       │   └── ...
│       ├── output/
│       │   ├── logs/           # 日志目录
│       │   └── txt/            # 报告输出
│       ├── scripts/
│       │   └── start.sh        # 启动脚本
│       └── start.py            # 启动入口
├── libs/
│   ├── data/                   # 数据文件（城市坐标等）
│   ├── database/bazi/          # SQLite 数据库
│   └── external/github/        # 外部命理库
└── docs/                       # 文档
```

## 常用命令

```bash
make help       # 查看所有命令
make install    # 安装依赖
make start      # 后台启动
make stop       # 停止服务
make status     # 查看状态
make restart    # 重启服务
make run        # 前台运行
make lint       # 代码检查
make test       # 运行测试
make clean      # 清理缓存
make reset      # 重建虚拟环境
```

## 功能特性

### 核心功能
- 八字排盘（四柱、藏干、十神、神煞、格局）
- 大运流年分析
- 真太阳时计算
- 地点模糊匹配（3199+ 城市）

### 扩展功能
- 紫微斗数
- 择日算法
- 合婚分析
- 姓名学

## 配置说明

所有配置集中在 `tradecat/config/.env`：

| 变量 | 必填 | 说明 |
|------|------|------|
| `FATE_BOT_TOKEN` | ✅ | fate-service 专用 Bot Token |
| `FATE_ADMIN_USER_IDS` | ❌ | 管理员 ID（逗号分隔） |
| `FATE_SERVICE_HOST` | ❌ | API 服务地址（默认 0.0.0.0） |
| `FATE_SERVICE_PORT` | ❌ | API 服务端口（默认 8001） |

## 故障排查

### Bot 无响应

1. 检查配置：`grep FATE_BOT_TOKEN config/.env`
2. 检查网络/代理
3. 确认只有一个 Bot 实例运行

### 排盘失败

1. 检查日志：`tail -f services/telegram-service/output/logs/bot.log`
2. 验证数据库：`sqlite3 libs/database/bazi/bazi.db ".tables"`

### 依赖缺失

```bash
# 重新安装依赖
make reset
make install
```

## 许可证

MIT License
