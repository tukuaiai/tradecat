# TradeCat AI 一键部署提示词

> 将以下内容完整复制给 AI 助手（Claude/ChatGPT/Cursor/Kiro），AI 将自动完成全部部署步骤。

---

## 提示词开始

```
请帮我在 Ubuntu 系统上部署 TradeCat 加密货币数据分析平台。

## 项目信息
- 仓库地址: https://github.com/tukuaiai/tradecat
- 分支: main (稳定版) 或 dev (开发版)
- 数据集: https://huggingface.co/datasets/123olp/binance-futures-ohlcv-2018-2026

## 部署要求
1. 零人工介入，全自动执行
2. 每步执行后确认成功再继续
3. 遇到错误自动分析并修复
4. 最终验证所有服务运行正常

## 系统要求
- Ubuntu 20.04/22.04/24.04 LTS
- Python 3.10+
- 至少 8GB RAM，推荐 16GB+
- 至少 50GB 磁盘空间（数据量大时需要更多）
- 需要能访问 GitHub 和 HuggingFace（可能需要代理）

## 部署步骤

### 第一步：系统依赖安装

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础依赖
sudo apt install -y python3 python3-pip python3-venv git curl wget

# 安装 PostgreSQL 客户端（用于数据库操作）
sudo apt install -y postgresql-client

# 可选：安装 TA-Lib（K线形态检测需要）
# wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
# tar -xzf ta-lib-0.4.0-src.tar.gz
# cd ta-lib && ./configure --prefix=/usr && make && sudo make install
# cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
# pip install TA-Lib
```

### 第二步：克隆项目

```bash
# 创建项目目录
mkdir -p ~/.projects && cd ~/.projects

# 克隆仓库
git clone https://github.com/tukuaiai/tradecat.git
cd tradecat

# 切换到稳定分支
git checkout main
```

### 第三步：初始化服务

```bash
# 运行初始化脚本（自动创建虚拟环境、安装依赖）
./scripts/init.sh

# 初始化完成后会显示：
# ✓ data-service 初始化完成
# ✓ trading-service 初始化完成
# ✓ telegram-service 初始化完成
# ✓ ai-service 初始化完成
# ✓ signal-service 初始化完成
```

### 第四步：配置环境变量

```bash
# 复制配置模板
cp config/.env.example config/.env
chmod 600 config/.env

# 编辑配置文件，必填项：
# - BOT_TOKEN: Telegram Bot Token（从 @BotFather 获取）
# - DATABASE_URL: TimescaleDB 连接字符串
# - HTTP_PROXY: 代理地址（如需要）

# 示例配置：
# BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
# DATABASE_URL=postgresql://postgres:postgres@localhost:5433/market_data
# HTTP_PROXY=http://127.0.0.1:7890
# SYMBOLS_GROUPS=main4
```

### 第五步：数据库准备（如果使用 TimescaleDB）

```bash
# 检查数据库连接
pg_isready -h localhost -p 5433

# 如果数据库可用，导入 schema
for f in libs/database/db/schema/*.sql; do
  psql -h localhost -p 5433 -U postgres -d market_data -f "$f"
done
```

### 第六步：下载历史数据（可选但推荐）

```bash
# 安装下载依赖
services/data-service/.venv/bin/pip install pandas psycopg2-binary huggingface_hub

# 下载并导入 main4 币种（BTC/ETH/BNB/SOL）全部历史数据
# Main4 数据集约 415MB，包含 1150 万条记录（2020-2026）
services/data-service/.venv/bin/python scripts/download_hf_data.py

# 或者指定特定币种
services/data-service/.venv/bin/python scripts/download_hf_data.py --symbols BTCUSDT,ETHUSDT
```

### 第七步：环境检查

```bash
# 运行环境检查脚本
./scripts/check_env.sh

# 确认输出没有错误（警告可以忽略）
# 检查内容：
# - Python 版本
# - 虚拟环境
# - 配置文件
# - 数据库连接
# - 网络连接
```

### 第八步：启动服务

```bash
# 启动所有服务
./scripts/start.sh start

# 查看服务状态
./scripts/start.sh status

# 期望输出：
# [data-service]   ✓ daemon: 运行中
# [data-service]   ✓ backfill: 运行中
# [data-service]   ✓ metrics: 运行中
# [data-service]   ✓ ws: 运行中
# [trading-service] ✓ 服务运行中
# [telegram-service] ✓ Bot 运行中
```

### 第九步：启动守护进程（可选，推荐生产环境）

```bash
# 启动守护进程模式（自动重启崩溃的服务）
./scripts/start.sh daemon

# 守护进程特性：
# - 每 30 秒检查服务状态
# - 自动重启崩溃服务（最多 5 次/5分钟）
# - 指数退避防止重启风暴
# - 告警日志写入 alerts.log
```

### 第十步：配置日志轮转（可选，推荐生产环境）

```bash
# 生成 logrotate 配置
sed -e "s|{{PROJECT_ROOT}}|$(pwd)|g" \
    -e "s|{{USER}}|$(whoami)|g" \
    config/logrotate.conf > /tmp/tradecat-logrotate.conf

# 安装到系统
sudo cp /tmp/tradecat-logrotate.conf /etc/logrotate.d/tradecat
```

## 验证部署

部署完成后，执行以下验证：

1. **服务状态检查**
```bash
./scripts/start.sh status
# 所有服务应显示 ✓ 运行中
```

2. **Telegram Bot 测试**
- 在 Telegram 中搜索你的 Bot
- 发送 /start 命令
- 应该收到欢迎消息

3. **数据检查**
```bash
# 检查 SQLite 数据
sqlite3 libs/database/services/telegram-service/market_data.db "SELECT COUNT(*) FROM indicators_1m;"

# 检查 TimescaleDB 数据（如果使用）
psql -h localhost -p 5433 -U postgres -d market_data -c "SELECT COUNT(*) FROM market_data.candles_1m;"
```

## 常用命令

```bash
# 服务管理
./scripts/start.sh start      # 启动服务
./scripts/start.sh stop       # 停止服务
./scripts/start.sh status     # 查看状态
./scripts/start.sh restart    # 重启服务
./scripts/start.sh daemon     # 守护模式
./scripts/start.sh daemon-stop # 停止守护

# 环境检查
./scripts/check_env.sh

# 代码验证
./scripts/verify.sh

# 下载历史数据
python scripts/download_hf_data.py [--symbols X,Y] [--days N]
```

## 目录结构

```
tradecat/
├── config/.env           # 配置文件（必填）
├── scripts/              # 脚本目录
│   ├── init.sh           # 初始化
│   ├── start.sh          # 启动/停止
│   ├── check_env.sh      # 环境检查
│   └── download_hf_data.py # 数据下载
├── services/             # 核心服务
│   ├── data-service/     # 数据采集
│   ├── trading-service/  # 指标计算
│   ├── telegram-service/ # Bot 交互
│   ├── ai-service/       # AI 分析
│   └── signal-service/   # 信号检测
└── libs/database/        # 数据库文件
```

## 故障排查

1. **Bot 无法连接 Telegram**
   - 检查 BOT_TOKEN 是否正确
   - 检查代理配置 HTTP_PROXY
   - 运行 `curl -x $HTTP_PROXY https://api.telegram.org`

2. **数据库连接失败**
   - 检查 DATABASE_URL 格式
   - 检查数据库服务是否运行
   - 运行 `pg_isready -h localhost -p 5433`

3. **服务启动失败**
   - 检查日志 `tail -f services/*/logs/*.log`
   - 检查虚拟环境 `ls services/*/.venv/`
   - 重新初始化 `./scripts/init.sh`

4. **依赖缺失**
   - 运行 `./scripts/check_env.sh` 查看缺失项
   - 重建虚拟环境 `cd services/<name> && make reset`

请按照上述步骤执行部署，每一步都确认成功后再继续。如遇到任何错误，请分析原因并尝试修复后重试。
```

---

## 提示词结束

**使用方法**：
1. 复制上方 ` ``` ` 之间的全部内容
2. 粘贴到 AI 助手对话框
3. 等待 AI 自动执行部署

**预计时间**：
- 基础部署：10-20 分钟
- 含历史数据下载：1-3 小时（取决于网络和数据量）

**支持的 AI 助手**：
- Claude (推荐)
- ChatGPT (GPT-4)
- Cursor
- Kiro
- 其他支持代码执行的 AI 工具
