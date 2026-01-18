# API 规范对比文档

> 本文档对比 CoinGlass API V4 规范与 TradeCat API 的差异，用于指导 API 重构。

---

## 1. 基础信息对比

| 项目 | CoinGlass V4 | TradeCat 当前 | TradeCat 目标 | 状态 |
|:---|:---|:---|:---|:---|
| Base URL | `https://open-api-v4.coinglass.com` | `http://localhost:8089` | 不变 | - |
| API 前缀 | `/api/futures/...` | `/api/v1/...` | `/api/futures/...` | ⚠️ 需改 |
| 版本号 | 无 (路径中无 v1) | `/api/v1/` | `/api/` | ⚠️ 需改 |
| 数据格式 | JSON | JSON | JSON | ✅ 对齐 |

---

## 2. 认证机制对比

| 项目 | CoinGlass V4 | TradeCat 当前 | TradeCat 目标 | 状态 |
|:---|:---|:---|:---|:---|
| 认证方式 | API Key | 无 | API Key (可选) | ⚠️ 需加 |
| Header 名称 | `CG-API-KEY` | - | `X-API-KEY` | ⚠️ 需加 |
| 缺失 Key 响应 | 401 Unauthorized | - | 401 | ⚠️ 需加 |

### CoinGlass 认证示例
```bash
curl -X GET "https://open-api-v4.coinglass.com/api/futures/supported-coins" \
  -H "accept: application/json" \
  -H "CG-API-KEY: YOUR_API_KEY"
```

---

## 3. 响应格式对比

### 3.1 成功响应

| 项目 | CoinGlass V4 | TradeCat 当前 | TradeCat 目标 | 状态 |
|:---|:---|:---|:---|:---|
| code 字段 | `"0"` (字符串) | 无 | `"0"` | ⚠️ 需改 |
| msg 字段 | `"success"` | 无 | `"success"` | ⚠️ 需改 |
| data 字段 | 数组或对象 | 有 | 数组或对象 | ✅ 对齐 |
| success 字段 | 有 | 无 | 有 | ⚠️ 需加 |
| 外层包装 | 无 count/symbol | 有 count | 无 | ⚠️ 需改 |

#### CoinGlass 成功响应示例
```json
{
  "code": "0",
  "msg": "success",
  "data": [
    {
      "time": 1745366400000,
      "open": "93404.9",
      "high": "93864.9",
      "low": "92730",
      "close": "92858.2",
      "volume_usd": "1166471854.3026"
    }
  ]
}
```

#### TradeCat 当前响应 (需修改)
```json
{
  "symbol": "BTCUSDT",
  "interval": "1m",
  "data": [...],
  "count": 3
}
```

### 3.2 错误响应

| HTTP 状态码 | CoinGlass 含义 | TradeCat 目标 |
|:---|:---|:---|
| 400 | 参数缺失或无效 | ✅ |
| 401 | API Key 无效或缺失 | ⚠️ 需加 |
| 404 | 资源不存在 | ✅ |
| 405 | HTTP 方法不支持 | ✅ |
| 408 | 请求超时 | ⚠️ 需加 |
| 422 | 参数有效但不可接受 | ✅ |
| 429 | 超出速率限制 | ⚠️ 需加 |
| 500 | 服务器内部错误 | ✅ |

### 3.3 业务错误码

| 错误码 | CoinGlass 含义 | TradeCat 目标 |
|:---|:---|:---|
| `"0"` | 成功 | ✅ |
| `"40001"` | 参数错误，查看 msg | ✅ |
| `"50001"` | 超出速率限制 | ⚠️ 需加 |

---

## 4. 端点路径对比

| 功能 | CoinGlass V4 | TradeCat 当前 | TradeCat 目标 | 状态 |
|:---|:---|:---|:---|:---|
| 健康检查 | 无 | `GET /health` | `GET /api/health` | ⚠️ 需改 |
| 支持币种 | `GET /api/futures/supported-coins` | `GET /api/v1/symbols` | `GET /api/futures/supported-coins` | ⚠️ 需改 |
| K线历史 | `GET /api/futures/price/history` | `GET /api/v1/candles/{symbol}` | `GET /api/futures/ohlc/history` | ⚠️ 需改 |
| OI历史 | `GET /api/futures/open-interest/history` | 无 | `GET /api/futures/open-interest/history` | ⚠️ 需加 |
| 资金费率历史 | `GET /api/futures/funding-rate/history` | 无 | `GET /api/futures/funding-rate/history` | ⚠️ 需加 |
| 期货指标 | 无对应 | `GET /api/v1/metrics/{symbol}` | `GET /api/futures/metrics` | ⚠️ 需改 |
| 指标表列表 | 无对应 | `GET /api/v1/indicators/tables` | `GET /api/indicator/list` | ⚠️ 需改 |
| 指标数据 | 无对应 | `GET /api/v1/indicators/{table}` | `GET /api/indicator/data` | ⚠️ 需改 |
| 信号冷却 | 无对应 | `GET /api/v1/signals/cooldown` | `GET /api/signal/cooldown` | ⚠️ 需改 |

---

## 5. 请求参数对比

### 5.1 通用参数

| 参数 | CoinGlass V4 | TradeCat 当前 | TradeCat 目标 | 状态 |
|:---|:---|:---|:---|:---|
| `symbol` | 查询参数, `BTC` | 路径参数, `BTCUSDT` | 查询参数, 支持两种 | ⚠️ 需改 |
| `exchange` | 查询参数, `Binance` | 无 | 查询参数 (可选) | ⚠️ 需加 |
| `interval` | 查询参数 | 查询参数 | 查询参数 | ✅ 对齐 |
| `limit` | 查询参数 | 查询参数 | 查询参数 | ✅ 对齐 |
| `startTime` | 毫秒时间戳 | 无 | 毫秒时间戳 | ⚠️ 需加 |
| `endTime` | 毫秒时间戳 | 无 | 毫秒时间戳 | ⚠️ 需加 |

### 5.2 interval 可选值

| CoinGlass V4 | TradeCat 目标 | 状态 |
|:---|:---|:---|
| `1m` | `1m` | ✅ |
| `5m` | `5m` | ✅ |
| `15m` | `15m` | ✅ |
| `30m` | `30m` | ⚠️ 需加 |
| `1h` | `1h` | ✅ |
| `4h` | `4h` | ✅ |
| `12h` | `12h` | ⚠️ 需加 |
| `1d` | `1d` | ✅ |

### 5.3 symbol 格式

| CoinGlass V4 | TradeCat 当前 | TradeCat 目标 |
|:---|:---|:---|
| `BTC` | `BTCUSDT` | 支持 `BTC` 和 `BTCUSDT` 两种格式 |
| `ETH` | `ETHUSDT` | 自动转换: `BTC` → `BTCUSDT` |

---

## 6. 响应字段对比

### 6.1 OHLC 数据

| CoinGlass V4 | TradeCat 当前 | TradeCat 目标 | 状态 |
|:---|:---|:---|:---|
| `time` (毫秒) | `timestamp` (ISO) | `time` (毫秒) | ⚠️ 需改 |
| `open` (字符串) | `open` (浮点) | `open` (字符串) | ⚠️ 需改 |
| `high` (字符串) | `high` (浮点) | `high` (字符串) | ⚠️ 需改 |
| `low` (字符串) | `low` (浮点) | `low` (字符串) | ⚠️ 需改 |
| `close` (字符串) | `close` (浮点) | `close` (字符串) | ⚠️ 需改 |
| `volume_usd` | `volume` | `volume_usd` | ⚠️ 需改 |

#### CoinGlass OHLC 响应
```json
{
  "time": 1745366400000,
  "open": "93404.9",
  "high": "93864.9",
  "low": "92730",
  "close": "92858.2",
  "volume_usd": "1166471854.3026"
}
```

### 6.2 Open Interest 数据

| CoinGlass V4 | TradeCat 当前 | TradeCat 目标 |
|:---|:---|:---|
| `time` | - | `time` |
| `open` (OI开盘) | - | `open` |
| `high` (OI最高) | - | `high` |
| `low` (OI最低) | - | `low` |
| `close` (OI收盘) | - | `close` |

### 6.3 Funding Rate 数据

| CoinGlass V4 | TradeCat 当前 | TradeCat 目标 |
|:---|:---|:---|
| `time` | - | `time` |
| `open` (FR开盘) | - | `open` |
| `high` (FR最高) | - | `high` |
| `low` (FR最低) | - | `low` |
| `close` (FR收盘) | - | `close` |

### 6.4 Supported Coins 数据

| CoinGlass V4 | TradeCat 当前 | TradeCat 目标 | 状态 |
|:---|:---|:---|:---|
| `["BTC", "ETH", ...]` | `["BTCUSDT", ...]` + count | `["BTC", "ETH", ...]` | ⚠️ 需改 |

#### CoinGlass supported-coins 响应
```json
{
  "code": "0",
  "msg": "success",
  "data": ["BTC", "ETH", "SOL", "XRP", "DOGE"]
}
```

---

## 7. 速率限制对比

| 项目 | CoinGlass V4 | TradeCat 目标 |
|:---|:---|:---|
| 响应 Header | `API-KEY-MAX-LIMIT` | `X-RateLimit-Limit` |
| 响应 Header | `API-KEY-USE-LIMIT` | `X-RateLimit-Remaining` |
| 超限状态码 | 429 | 429 |
| 超限错误码 | `"50001"` | `"50001"` |

---

## 8. 文件修改清单

### 8.1 需要新增的文件

| 文件路径 | 说明 |
|:---|:---|
| `src/schemas/response.py` | 统一响应模型 |
| `src/utils/errors.py` | 错误码定义 |
| `src/middleware/auth.py` | API Key 认证中间件 |
| `src/middleware/ratelimit.py` | 速率限制中间件 |
| `src/routers/open_interest.py` | OI 历史端点 |
| `src/routers/funding_rate.py` | 资金费率历史端点 |

### 8.2 需要重命名的文件

| 原文件 | 新文件 |
|:---|:---|
| `src/routers/symbols.py` | `src/routers/coins.py` |
| `src/routers/candles.py` | `src/routers/ohlc.py` |
| `src/routers/metrics.py` | `src/routers/futures_metrics.py` |
| `src/routers/indicators.py` | `src/routers/indicator.py` |
| `src/routers/signals.py` | `src/routers/signal.py` |

### 8.3 需要修改的文件

| 文件 | 修改内容 |
|:---|:---|
| `src/app.py` | 路由注册, 中间件 |
| `src/schemas/__init__.py` | 导出新模型 |
| `src/schemas/models.py` | 字段重命名 |
| `src/routers/__init__.py` | 导出新路由 |
| `src/routers/health.py` | 响应格式 |
| `src/routers/coins.py` | 路径+响应 |
| `src/routers/ohlc.py` | 路径+参数+响应 |
| `src/routers/futures_metrics.py` | 路径+参数+响应 |
| `src/routers/indicator.py` | 路径+响应 |
| `src/routers/signal.py` | 路径+响应 |

---

## 9. 改动优先级

### P0 - 必须 (核心对齐)
1. 统一响应格式 `{code, msg, data}`
2. 端点路径修改 (去掉 v1, 对齐命名)
3. 参数从路径改为查询参数
4. symbol 格式支持 (BTC/BTCUSDT)
5. 时间戳格式统一 (毫秒)
6. 数值改为字符串格式

### P1 - 重要 (功能完善)
1. 新增 `startTime`/`endTime` 参数
2. 新增 `exchange` 参数
3. 新增 OI 历史端点
4. 新增 Funding Rate 历史端点

### P2 - 可选 (增强功能)
1. API Key 认证
2. 速率限制
3. interval 扩展 (30m, 12h)

---

## 10. 验收标准

- [ ] 所有端点返回 `{code: "0", msg: "success", data: [...]}` 格式
- [ ] 错误响应返回对应错误码
- [ ] symbol 参数支持 `BTC` 和 `BTCUSDT` 两种格式
- [ ] 时间字段统一为毫秒时间戳 `time`
- [ ] 数值字段统一为字符串格式
- [ ] 端点路径完全对齐 CoinGlass 命名规范
- [ ] 参数均为查询参数 (非路径参数)

---

*文档版本: 1.0*
*创建时间: 2026-01-16*
*最后更新: 2026-01-16*
