<p align="center">
  <img src="https://github.com/tukuaiai.png" alt="TradeCat" width="100px">
</p>

<div align="center">

# 🐱 交易猫

**toy-level 数据分析/交易数据平台**

*全部市场，全部数据，全部方法，分析一切，交易一切，监控一切*

[English](README_EN.md) | 简体中文

---

<p>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PostgreSQL-TimescaleDB-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="TimescaleDB">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
</p>

<p>
  <img src="https://img.shields.io/badge/Pandas-数据处理-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas">
  <img src="https://img.shields.io/badge/NumPy-计算-013243?style=for-the-badge&logo=numpy&logoColor=white" alt="NumPy">
  <img src="https://img.shields.io/badge/TA--Lib-技术分析-green?style=for-the-badge" alt="TA-Lib">
  <img src="https://img.shields.io/badge/CCXT-交易所API-000?style=for-the-badge" alt="CCXT">
</p>

<p>
  <img src="https://img.shields.io/badge/Telegram_Bot-机器人-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Bot">
  <img src="https://img.shields.io/badge/AsyncIO-异步-FF6F00?style=for-the-badge&logo=python&logoColor=white" alt="AsyncIO">
  <img src="https://img.shields.io/badge/AIOHTTP-HTTP客户端-2C5BB4?style=for-the-badge&logo=aiohttp&logoColor=white" alt="AIOHTTP">
</p>

<p>
  <a href="https://t.me/tradecat_ai_channel"><img src="https://img.shields.io/badge/Telegram-频道-blue?style=for-the-badge&logo=telegram" alt="Telegram"></a>
  <a href="https://t.me/glue_coding"><img src="https://img.shields.io/badge/Telegram-交流群-blue?style=for-the-badge&logo=telegram" alt="交流群"></a>
  <a href="https://x.com/123olp"><img src="https://img.shields.io/badge/Twitter-@123olp-black?style=for-the-badge&logo=x" alt="Twitter"></a>
</p>

</div>

---

## 📖 目录

- [✨ 核心特性](#-核心特性)
- [🏗️ 架构设计](#️-架构设计)
- [📊 数据规模](#-数据规模)
- [📈 技术指标](#-技术指标)
- [🤖 Telegram Bot](#-telegram-bot)
- [🚀 快速开始](#-快速开始)
- [📁 目录结构](#-目录结构)
- [🔧 运维指南](#-运维指南)
- [📞 联系方式](#-联系方式)

> 🤖 **从零开始？** 复制这行到 AI 助手：`按照 https://github.com/tukuaiai/tradecat/blob/main/README.md 的说明帮我安装 TradeCat`

---

## ✨ 核心特性

<table>
<tr>
<td width="50%">

### 🔄 实时数据采集
- **WebSocket 实时推送** - 币安期货全币种 K线
- **多周期支持** - 1m/5m/15m/1h/4h/1d/1w
- **期货指标** - 持仓量、多空比、资金费率
- **数据延迟** - < 5 秒

</td>
<td width="50%">

### 📊 38个技术指标
- **趋势指标** - EMA/MACD/SuperTrend/ADX
- **动量指标** - RSI/KDJ/CCI/MFI
- **波动指标** - 布林带/ATR/Keltner
- **形态识别** - 61种蜡烛 + 价格形态

</td>
</tr>
<tr>
<td width="50%">

### 🤖 Telegram Bot
- **实时排行榜** - 20+ 种排行卡片
- **信号推送** - 形态突破、指标异常
- **交互查询** - 单币详情、历史回溯
- **高优先级** - 智能筛选活跃币种

</td>
<td width="50%">

### 🗄️ 海量数据存储
- **K线数据** - 3.73亿条 (2018-至今)
- **期货数据** - 9457万条 (2021-至今)
- **存储引擎** - TimescaleDB 时序优化
- **压缩备份** - zstd 压缩至 ~15GB

</td>
</tr>
</table>

---

## 🏗️ 架构设计

### 系统架构图

```
                              ┌─────────────────────────────────────────┐
                              │            币安交易所 API                │
                              │   WebSocket K线  │  REST 期货指标       │
                              └────────┬─────────┴──────────┬───────────┘
                                       │                    │
                    ┌──────────────────▼────────────────────▼──────────────────┐
                    │                    data-service                          │
                    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
                    │  │  backfill   │  │    live     │  │   metrics   │      │
                    │  │  历史回填    │  │  实时采集   │  │  期货指标   │      │
                    │  └─────────────┘  └─────────────┘  └─────────────┘      │
                    └──────────────────────────┬───────────────────────────────┘
                                               │
                    ┌──────────────────────────▼───────────────────────────────┐
                    │                     TimescaleDB                          │
                    │  ┌─────────────────────┐  ┌─────────────────────┐       │
                    │  │    candles_1m       │  │  futures_metrics    │       │
                    │  │   3.73亿条 / 99GB   │  │  9457万条 / 5GB     │       │
                    │  └─────────────────────┘  └─────────────────────┘       │
                    └──────────────────────────┬───────────────────────────────┘
                                               │
                    ┌──────────────────────────▼───────────────────────────────┐
                    │                   trading-service                        │
                    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
                    │  │   engine    │  │ indicators  │  │  scheduler  │      │
                    │  │  计算引擎   │  │  38个指标   │  │  定时调度   │      │
                    │  └─────────────┘  └─────────────┘  └─────────────┘      │
                    └──────────────────────────┬───────────────────────────────┘
                                               │
                    ┌──────────────────────────▼───────────────────────────────┐
                    │                    market_data.db                        │
                    │              SQLite 指标结果 (38张表)                    │
                    └──────────────────────────┬───────────────────────────────┘
                                               │
                    ┌──────────────────────────▼───────────────────────────────┐
                    │                  telegram-service                        │
                    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
                    │  │   cards     │  │  handlers   │  │    bot      │      │
                    │  │  排行卡片   │  │  命令处理   │  │  主程序     │      │
                    │  └─────────────┘  └─────────────┘  └─────────────┘      │
                    └──────────────────────────┬───────────────────────────────┘
                                               │
                              ┌────────────────▼────────────────┐
                              │         Telegram 用户           │
                              │   排行榜查询  │  信号接收       │
                              └─────────────────────────────────┘
```

### 服务说明

| 服务 | 端口 | 职责 | 技术栈 |
|:---|:---:|:---|:---|
| **data-service** | - | WebSocket K线采集、期货指标采集、历史数据回填 | Python, asyncio, ccxt, cryptofeed |
| **trading-service** | - | 38个技术指标计算、高优先级币种筛选、定时调度 | Python, pandas, numpy, TA-Lib |
| **telegram-service** | - | Bot 交互、排行榜展示、信号推送 | python-telegram-bot, aiohttp |
| **order-service** | - | 交易执行、Avellaneda-Stoikov 做市 | Python, ccxt, cryptofeed |
| **TimescaleDB** | 5433 | K线存储、期货数据存储、时序查询优化 | PostgreSQL 16 + TimescaleDB |

### 数据流向

```
币安 WebSocket ──▶ data-service ──▶ TimescaleDB (candles_1m)
                                          │
                                          ▼
                                   trading-service
                                          │
                                          ▼
                                   market_data.db (SQLite)
                                          │
                                          ▼
                                   telegram-service ──▶ 用户
```


---

## 📊 数据规模

**🔗 历史数据下载**: [HuggingFace 数据集](https://huggingface.co/datasets/123olp/binance-futures-ohlcv-2018-2026)

| 数据集 | 说明 | 大小 |
|:---|:---|:---|
| `candles_1m.bin.zst` | K线数据 (2018-至今, 3.73亿条) | ~15 GB |
| `futures_metrics_5m.bin.zst` | 期货指标 (2021-至今, 9457万条) | ~800 MB |

<details>
<summary><strong>📋 数据详情与导入步骤</strong></summary>

### 数据概览

<table>
<tr>
<td width="50%">

#### 📈 K线数据 (candles_1m)

| 指标 | 数值 |
|:---|---:|
| **总记录数** | 373,342,599 |
| **币种数量** | 615 |
| **时间范围** | 2018-01-01 ~ 至今 |
| **存储大小** | 99 GB |
| **压缩后** | ~15 GB (zstd) |

**字段说明**:
- `bucket_ts` - K线时间戳
- `open/high/low/close` - OHLC 价格
- `volume` - 成交量
- `quote_volume` - 成交额 (USDT)
- `taker_buy_volume` - 主动买入量

</td>
<td width="50%">

#### 📊 期货数据 (futures_metrics_5m)

| 指标 | 数值 |
|:---|---:|
| **总记录数** | 94,576,458 |
| **币种数量** | 612 |
| **时间范围** | 2021-12-01 ~ 至今 |
| **存储大小** | 5 GB |
| **压缩后** | ~800 MB (zstd) |

**字段说明**:
- `sum_open_interest` - 持仓量
- `sum_open_interest_value` - 持仓价值 (USDT)
- `sum_toptrader_long_short_ratio` - 大户多空比
- `sum_taker_long_short_vol_ratio` - 主动买卖比

</td>
</tr>
</table>

### 数据更新频率

| 数据类型 | 更新频率 | 延迟 |
|:---|:---|:---|
| K线 (1m) | 实时 WebSocket | < 5秒 |
| K线 (5m/15m/1h/4h/1d/1w) | 聚合计算 | < 10秒 |
| 期货指标 | 每 5 分钟 | < 30秒 |
| 技术指标 | 每分钟轮询 | < 3分钟 |

### 导入步骤

```bash
# 1. 下载数据文件
# 从 HuggingFace 下载 .bin.zst 文件到 backups/timescaledb/

# 2. 恢复表结构
zstd -d schema.sql.zst -c | psql -h localhost -p 5433 -U postgres -d market_data

# 3. 导入 K线数据
zstd -d candles_1m.bin.zst -c | psql -h localhost -p 5433 -U postgres -d market_data \
    -c "COPY market_data.candles_1m FROM STDIN WITH (FORMAT binary)"

# 4. 导入期货数据
zstd -d futures_metrics_5m.bin.zst -c | psql -h localhost -p 5433 -U postgres -d market_data \
    -c "COPY market_data.binance_futures_metrics_5m FROM STDIN WITH (FORMAT binary)"
```

> 💡 导入后即可使用 trading-service 计算指标，无需从头采集历史数据。

</details>

---

## 📈 技术指标

<details>
<summary><strong>🔥 趋势指标 (8个)</strong></summary>

| 指标 | 说明 | 参数 |
|:---|:---|:---|
| **EMA** | 指数移动平均 | 7/25/99 周期 |
| **MACD** | 异同移动平均 | 12/26/9 |
| **SuperTrend** | 超级趋势 | ATR 周期 10, 乘数 3 |
| **ADX** | 平均趋向指数 | 14 周期 |
| **Ichimoku** | 一目均衡表 | 9/26/52 |
| **Donchian** | 唐奇安通道 | 20 周期 |
| **Keltner** | 肯特纳通道 | 20 周期, ATR 2倍 |
| **趋势线** | 自动趋势线识别 | 动态计算 |

</details>

<details>
<summary><strong>📊 动量指标 (6个)</strong></summary>

| 指标 | 说明 | 参数 |
|:---|:---|:---|
| **RSI** | 相对强弱指数 | 14 周期 |
| **KDJ** | 随机指标 | 9/3/3 |
| **CCI** | 商品通道指数 | 20 周期 |
| **WilliamsR** | 威廉指标 | 14 周期 |
| **MFI** | 资金流量指数 | 14 周期 |
| **RSI谐波** | RSI 背离检测 | 14 周期 |

</details>

<details>
<summary><strong>📉 波动指标 (4个)</strong></summary>

| 指标 | 说明 | 参数 |
|:---|:---|:---|
| **布林带** | Bollinger Bands | 20 周期, 2倍标准差 |
| **ATR** | 真实波幅 | 14 周期 |
| **ATR波幅** | 波动率排行 | 14 周期 |
| **支撑阻力** | 关键价位识别 | 动态计算 |

</details>

<details>
<summary><strong>📦 成交量指标 (6个)</strong></summary>

| 指标 | 说明 | 用途 |
|:---|:---|:---|
| **OBV** | 能量潮 | 量价背离 |
| **CVD** | 累积成交量差 | 买卖力量 |
| **VWAP** | 成交量加权均价 | 机构成本 |
| **成交量比率** | 相对成交量 | 放量识别 |
| **流动性** | 买卖盘深度 | 滑点预估 |
| **VPVR** | 成交量分布 | 密集成交区 |

</details>

<details>
<summary><strong>🕯️ K线形态 (61+种)</strong></summary>

**蜡烛形态 (TA-Lib, 61种)**

| 类型 | 形态 |
|:---|:---|
| **反转形态** | 锤子线、上吊线、吞没、孕线、晨星、黄昏星、三只乌鸦 |
| **持续形态** | 三法、分离线、并列阴阳 |
| **中性形态** | 十字星、纺锤线、高浪线 |

**价格形态 (patternpy)**

| 类型 | 形态 | 信号 |
|:---|:---|:---|
| **头肩形态** | 头肩顶、头肩底 | 强反转 |
| **双重形态** | 双顶、双底 | 中等反转 |
| **三角形态** | 上升三角、下降三角、对称三角 | 突破方向 |
| **楔形形态** | 上升楔形、下降楔形 | 反向突破 |
| **通道形态** | 上升通道、下降通道、水平通道 | 趋势延续 |

</details>

<details>
<summary><strong>📡 期货指标 (8个)</strong></summary>

| 指标 | 说明 | 信号含义 |
|:---|:---|:---|
| **持仓量** | Open Interest | 市场参与度 |
| **持仓价值** | OI Value (USDT) | 资金规模 |
| **多空比** | Long/Short Ratio | 散户情绪 |
| **大户多空比** | Top Trader L/S | 主力方向 |
| **主动买卖比** | Taker Buy/Sell | 即时情绪 |
| **资金费率** | Funding Rate | 多空成本 |
| **爆仓数据** | Liquidations | 极端行情 |
| **期货情绪聚合** | 综合评分 | 多维度分析 |

</details>

### 高优先级算法

系统自动识别高优先级币种 (约 130-150 个)，基于以下维度：

```
高优先级 = K线维度 ∪ 期货维度

K线维度:
  - 成交额 Top 50
  - 波动率 Top 30  
  - 涨跌幅 Top 30

期货维度:
  - 持仓价值 Top 30
  - 主动买卖比极端 (>1.5 或 <0.67)
  - 多空比极端 (>2.0 或 <0.5)
```


---

## 🤖 Telegram Bot

### 功能概览

<table>
<tr>
<td width="50%">

#### 📊 排行榜卡片 (20+种)

| 类别 | 卡片 |
|:---|:---|
| **基础排行** | RSI、MACD、KDJ、布林带、OBV |
| **高级排行** | EMA、ATR、CVD、MFI、VWAP、流动性 |
| **形态排行** | K线形态、支撑阻力、趋势线 |
| **期货排行** | 持仓量、多空比、主动买卖比 |

</td>
<td width="50%">

#### 🔔 信号推送

| 信号类型 | 触发条件 |
|:---|:---|
| **形态突破** | 检测到头肩、双顶等形态 |
| **指标异常** | RSI 超买超卖、MACD 金叉死叉 |
| **量价异动** | 成交量突增、价格突破 |
| **期货异常** | 多空比极端、持仓量剧变 |

</td>
</tr>
</table>

### 命令与触发方式

| 触发方式 | 功能 | 说明 |
|:---|:---|:---|
| `BTC!` | 单币查询 | 交互式多面板查看 |
| `BTC!!` | 完整TXT导出 | 下载 psql 风格完整报告 |
| `BTC@` | AI分析 | 威科夫深度市场分析 |
| `/data` | 数据面板 | 访问排行榜卡片 |
| `/ai` | AI分析 | 进入AI币种选择 |
| `/query` | 币种查询 | 显示可查询币种 |
| `/help` | 帮助 | 使用说明 |

### 常驻键盘布局

```
┌─────────────┬─────────────┬─────────────┐
│ 📊 数据面板 │ 🔍 币种查询 │  🤖 AI分析  │
├─────────────┴──────┬──────┴─────────────┤
│     🏠 主菜单      │      ℹ️ 帮助       │
└────────────────────┴────────────────────┘
```

### 单币查询面板

1. **基础面板** - 布林带、KDJ、MACD、RSI、OBV、量比
2. **期货面板** - 持仓量、多空比、情绪指标
3. **高级面板** - 支撑阻力、ATR、流动性、趋势、VWAP
4. **形态面板** - K线形态识别 (61种)

---

## 🚀 快速开始

### 🤖 AI 一键安装（推荐）

> 把下面的提示词复制到 **Claude / ChatGPT / Cursor / Kiro**，AI 会自动执行安装，零人工介入

<details>
<summary><strong>📋 点击展开安装提示词</strong></summary>

```
按照 https://github.com/tukuaiai/tradecat/blob/main/README.md 的说明帮我安装 TradeCat

要求：
1. 读取文档后直接执行安装命令，不要生成脚本
2. 一步一步执行，每步确认成功后继续
3. 遇到错误自动分析并修复
4. 安装完成后运行 ./scripts/verify.sh 验证
5. 全程零人工介入
```

</details>

### 🪟 Windows WSL2 用户

先在 Windows 用户目录创建 `.wslconfig`：

```powershell
notepad "$env:USERPROFILE\.wslconfig"
```

写入：

```ini
[wsl2]
memory=10GB
processors=6
swap=12GB
networkingMode=mirrored
```

重启 WSL：`wsl --shutdown`，然后使用上面的 AI 安装提示词。

### ⚙️ 配置 Bot Token（必须）

```bash
vim ~/.projects/tradecat/services/telegram-service/config/.env
```

```ini
TELEGRAM_BOT_TOKEN=你的Token
# 如需代理
HTTPS_PROXY=http://127.0.0.1:7890
```

### 🎬 启动服务

```bash
cd ~/.projects/tradecat
./scripts/start.sh daemon    # 启动
./scripts/start.sh status    # 查看状态
```

### ✅ 验证安装

```bash
./scripts/verify.sh
```

---

<details>
<summary><strong>📖 手动安装步骤（点击展开）</strong></summary>

### 环境要求

| 依赖 | 版本 | 说明 |
|:---|:---|:---|
| Python | 3.10+ | 推荐 3.12 |
| PostgreSQL | 16+ | 需安装 TimescaleDB 扩展 |
| TA-Lib | 0.4+ | 系统级库，需单独安装 |
| SQLite | 3.x | 系统自带 |

### 安装步骤

#### 1. 克隆仓库

```bash
git clone https://github.com/tukuaiai/tradecat.git
cd tradecat
```

#### 2. 安装系统依赖

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y build-essential python3-dev

# 安装 TA-Lib
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib && ./configure --prefix=/usr && make && sudo make install
cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
```

#### 3. 一键初始化

```bash
# 初始化所有服务（创建虚拟环境、安装依赖、复制配置）
./scripts/init.sh

# 或单独初始化某个服务
./scripts/init.sh data-service
```

#### 4. 配置环境变量

```bash
# 编辑各服务配置（init.sh 已自动从 .env.example 复制）
vim config/.env
```

#### 5. 启动服务

```bash
# 一键启动 + 守护（推荐，自动重启挂掉的服务）
./scripts/start.sh daemon

# 查看状态
./scripts/start.sh status

# 停止全部
./scripts/start.sh stop
```

#### 6. 验证安装

```bash
./scripts/verify.sh
```

</details>

---

## 📁 目录结构

```
tradecat/
│
├── 📂 config/                      # 统一配置（所有服务共用）
│   ├── .env                        # 生产配置（含密钥，不提交）
│   ├── .env.example                # 配置模板
│   └── logrotate.conf              # 日志轮转
│
├── 📂 scripts/                     # 全局脚本
│   ├── install.sh                  # 一键安装
│   ├── init.sh                     # 初始化脚本
│   ├── start.sh                    # 统一启动/守护脚本
│   ├── verify.sh                   # 验证脚本
│   ├── export_timescaledb.sh       # 数据导出
│   └── timescaledb_compression.sh  # 压缩管理
│
├── 📂 services/                    # 微服务目录 (4个)
│   │
│   ├── 📂 data-service/            # 数据采集服务
│   │   ├── 📂 src/
│   │   │   ├── 📂 collectors/      # 采集器
│   │   │   ├── 📂 adapters/        # 适配器
│   │   │   └── config.py
│   │   ├── 📂 scripts/
│   │   ├── requirements.txt
│   │   └── requirements.lock.txt
│   │
│   ├── 📂 trading-service/         # 指标计算服务
│   │   ├── 📂 src/
│   │   │   ├── 📂 indicators/      # 38个指标
│   │   │   ├── 📂 core/            # 计算引擎
│   │   │   └── simple_scheduler.py
│   │   ├── 📂 scripts/
│   │   ├── requirements.txt
│   │   └── requirements.lock.txt
│   │
│   ├── 📂 telegram-service/        # Telegram Bot
│   │   ├── 📂 src/
│   │   │   ├── 📂 cards/           # 排行榜卡片
│   │   │   ├── 📂 signals/         # 信号检测引擎
│   │   │   ├── 📂 bot/             # Bot 主程序
│   │   │   └── main.py
│   │   ├── 📂 scripts/
│   │   ├── requirements.txt
│   │   └── requirements.lock.txt
│   │
│   └── 📂 order-service/           # 交易执行服务
│       ├── 📂 src/
│       │   └── 📂 market-maker/    # A-S 做市系统
│       ├── requirements.txt
│       └── requirements.lock.txt
│
├── 📂 libs/                        # 共享库
│   ├── 📂 database/                # 数据库文件
│   │   └── 📂 services/telegram-service/
│   │       └── market_data.db      # SQLite 指标数据
│   └── 📂 common/                  # 共享工具
│       └── proxy_manager.py        # 代理管理器
│
├── 📂 backups/                     # 备份目录
│   └── 📂 timescaledb/             # 数据库备份
│
├── Makefile                        # 常用命令
├── README.md                       # 项目说明
├── AGENTS.md                       # AI Agent 指南
└── CONTRIBUTING.md                 # 贡献指南
```


---

## 🔧 运维指南

### 服务管理

<details>
<summary><strong>统一管理（推荐）</strong></summary>

```bash
# 启动 + 守护（自动重启挂掉的服务，30秒检查一次）
./scripts/start.sh daemon

# 查看状态
./scripts/start.sh status

# 停止全部
./scripts/start.sh daemon-stop

# 仅启动（不守护）
./scripts/start.sh start
./scripts/start.sh stop
./scripts/start.sh restart
```

</details>

<details>
<summary><strong>单服务管理</strong></summary>

```bash
# data-service
cd services/data-service
./scripts/start.sh daemon   # 启动 + 守护
./scripts/start.sh start    # 仅启动
./scripts/start.sh stop     # 停止
./scripts/start.sh status   # 状态

# trading-service / telegram-service 同上
```

</details>

<details>
<summary><strong>初始化</strong></summary>

```bash
# 初始化全部服务
./scripts/init.sh

# 初始化单个服务
./scripts/init.sh data-service
```

</details>

<details>
<summary><strong>验证与检查</strong></summary>

```bash
./scripts/verify.sh
```

</details>

<details>
<summary><strong>查看日志</strong></summary>

```bash
# data-service 日志
tail -f services/data-service/logs/backfill.log
tail -f services/data-service/logs/ws_klines.log
tail -f services/data-service/logs/metrics.log

# trading-service 日志
tail -f services/trading-service/logs/simple_scheduler.log

# telegram-service 日志
tail -f services/telegram-service/logs/bot.log

# 守护进程日志
tail -f daemon.log
```

</details>

<details>
<summary><strong>进程监控</strong></summary>

```bash
# 查看所有相关进程
ps aux | grep -E "data-service|trading-service|telegram|simple_scheduler"

# 查看资源占用
htop -p $(pgrep -d',' -f "simple_scheduler|crypto_trading")
```

</details>

### 数据库操作

<details>
<summary><strong>TimescaleDB 查询</strong></summary>

```bash
# 连接数据库
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d market_data

# 常用查询
-- K线数据量
SELECT COUNT(*) FROM market_data.candles_1m;

-- 最新数据时间
SELECT MAX(bucket_ts) FROM market_data.candles_1m;

-- 币种列表
SELECT DISTINCT symbol FROM market_data.candles_1m ORDER BY symbol;

-- 单币种数据
SELECT * FROM market_data.candles_1m 
WHERE symbol = 'BTCUSDT' 
ORDER BY bucket_ts DESC LIMIT 10;
```

</details>

<details>
<summary><strong>SQLite 查询</strong></summary>

```bash
# 连接数据库
sqlite3 libs/database/services/telegram-service/market_data.db

# 常用查询
.tables                          -- 查看所有表
.schema "K线形态扫描器.py"        -- 查看表结构

-- 查看形态数据
SELECT * FROM "K线形态扫描器.py" 
WHERE 形态类型 LIKE '%头肩%' 
LIMIT 10;
```

</details>

### 数据备份

<details>
<summary><strong>导出 TimescaleDB</strong></summary>

```bash
# 运行导出脚本 (后台执行)
nohup ./scripts/export_timescaledb.sh &

# 查看进度
tail -f backups/timescaledb/export.log
ls -lh backups/timescaledb/

# 输出文件:
# - candles_1m_*.bin.zst      (~15GB, K线数据)
# - futures_metrics_*.bin.zst (~800MB, 期货数据)
# - schema_*.sql.zst          (表结构)
# - restore_*.sh              (恢复脚本)
```

</details>

<details>
<summary><strong>恢复数据</strong></summary>

```bash
cd backups/timescaledb

# 恢复 schema
zstd -d schema_*.sql.zst -c | psql -h localhost -p 5433 -U postgres -d market_data

# 恢复 K线数据
zstd -d candles_1m_*.bin.zst -c | psql -h localhost -p 5433 -U postgres -d market_data \
    -c "COPY market_data.candles_1m FROM STDIN WITH (FORMAT binary)"

# 恢复期货数据
zstd -d futures_metrics_*.bin.zst -c | psql -h localhost -p 5433 -U postgres -d market_data \
    -c "COPY market_data.binance_futures_metrics_5m FROM STDIN WITH (FORMAT binary)"
```

</details>

### 常见问题

<details>
<summary><strong>Q: TA-Lib 安装失败？</strong></summary>

```bash
# 确保先安装系统库
sudo apt-get install -y build-essential

# 下载并编译 TA-Lib
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib
./configure --prefix=/usr
make
sudo make install

# 然后安装 Python 包
pip install TA-Lib
```

</details>

<details>
<summary><strong>Q: K线形态显示"无形态"？</strong></summary>

```bash
# 检查 TA-Lib 是否安装
python -c "import talib; print(talib.__version__)"

# 检查形态库是否安装
pip install m-patternpy
pip install tradingpattern --no-deps

# 重启 trading-service
cd services/trading-service
./scripts/start.sh restart
```

</details>

<details>
<summary><strong>Q: 数据库连接失败？</strong></summary>

```bash
# 检查 PostgreSQL 是否运行
sudo systemctl status postgresql

# 检查端口
ss -tlnp | grep 5433

# 检查连接
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -c "\l"
```

</details>

---

## 📞 联系方式

<table>
<tr>
<td width="50%">

### 社区

- **Telegram 频道**: [@tradecat_ai_channel](https://t.me/tradecat_ai_channel)
- **Telegram 交流群**: [@glue_coding](https://t.me/glue_coding)
- **Twitter/X**: [@123olp](https://x.com/123olp)

</td>
<td width="50%">

### 支持项目

救救孩子，感谢了，好人一生平安🙏🙏🙏

-   **币安 UID**: `572155580`
-   **Tron (TRC20)**: `TQtBXCSTwLFHjBqTS4rNUp7ufiGx51BRey`
-   **Solana**: `HjYhozVf9AQmfv7yv79xSNs6uaEU5oUk2USasYQfUYau`
-   **Ethereum (ERC20)**: `0xa396923a71ee7D9480b346a17dDeEb2c0C287BBC`
-   **BNB Smart Chain (BEP20)**: `0xa396923a71ee7D9480b346a17dDeEb2c0C287BBC`
-   **Bitcoin**: `bc1plslluj3zq3snpnnczplu7ywf37h89dyudqua04pz4txwh8z5z5vsre7nlm`
-   **Sui**: `0xb720c98a48c77f2d49d375932b2867e793029e6337f1562522640e4f84203d2e`

</td>
</tr>
</table>

---

## 📜 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

---

<div align="center">

### ⭐ 如果这个项目对您有帮助，请点亮 Star！

---

**Made with ❤️ by [tukuaiai](https://github.com/tukuaiai)**

[⬆ 返回顶部](#-tradecat)

</div>
