# API 调用示例

> Base URL: `http://localhost:8089`

---

## 1. 健康检查

```bash
curl -X GET "http://localhost:8089/api/health"
```

**响应:**
```json
{
    "code": "0",
    "msg": "success",
    "data": {
        "status": "healthy",
        "service": "api-service",
        "version": "1.0.0",
        "timestamp": 1768501496200
    },
    "success": true
}
```

---

## 2. 获取支持的币种列表

```bash
curl -X GET "http://localhost:8089/api/futures/supported-coins"
```

**响应:**
```json
{
    "code": "0",
    "msg": "success",
    "data": ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", ...],
    "success": true
}
```

---

## 3. K线历史数据 (OHLC)

### 基础请求
```bash
curl -X GET "http://localhost:8089/api/futures/ohlc/history?symbol=BTC&limit=5"
```

### 带时间范围
```bash
# startTime/endTime 为毫秒时间戳
curl -X GET "http://localhost:8089/api/futures/ohlc/history?symbol=BTC&interval=1h&limit=100&startTime=1768400000000&endTime=1768500000000"
```

### 支持的 symbol 格式
```bash
# 两种格式均支持
curl "http://localhost:8089/api/futures/ohlc/history?symbol=BTC&limit=3"
curl "http://localhost:8089/api/futures/ohlc/history?symbol=BTCUSDT&limit=3"
```

**响应:**
```json
{
    "code": "0",
    "msg": "success",
    "data": [
        {
            "time": 1768501320000,
            "open": "96059.100000000000",
            "high": "96066.800000000000",
            "low": "96006.000000000000",
            "close": "96013.000000000000",
            "volume": "122.240000000000",
            "volume_usd": "0"
        }
    ],
    "success": true
}
```

**参数说明:**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| symbol | string | 是 | - | 交易对 (BTC 或 BTCUSDT) |
| exchange | string | 否 | Binance | 交易所 |
| interval | string | 否 | 1h | 1m/5m/15m/30m/1h/4h/12h/1d |
| limit | int | 否 | 100 | 1-1000 |
| startTime | int | 否 | - | 开始时间 (毫秒) |
| endTime | int | 否 | - | 结束时间 (毫秒) |

---

## 4. Open Interest 历史

```bash
curl -X GET "http://localhost:8089/api/futures/open-interest/history?symbol=BTC&limit=5"
```

**响应:**
```json
{
    "code": "0",
    "msg": "success",
    "data": [
        {
            "time": 1768471800000,
            "open": "9380714072.576",
            "high": "9380714072.576",
            "low": "9380714072.576",
            "close": "9380714072.576"
        }
    ],
    "success": true
}
```

---

## 5. Funding Rate 历史

```bash
curl -X GET "http://localhost:8089/api/futures/funding-rate/history?symbol=ETH&limit=5"
```

**响应:**
```json
{
    "code": "0",
    "msg": "success",
    "data": [
        {
            "time": 1768471800000,
            "open": "1.921",
            "high": "1.921",
            "low": "1.921",
            "close": "1.921"
        }
    ],
    "success": true
}
```

---

## 6. 期货综合指标

```bash
curl -X GET "http://localhost:8089/api/futures/metrics?symbol=BTC&limit=5"
```

**响应:**
```json
{
    "code": "0",
    "msg": "success",
    "data": [
        {
            "time": 1768471800000,
            "symbol": "BTCUSDT",
            "openInterest": "9380714072.57600000",
            "longShortRatio": "1.9210",
            "takerLongShortRatio": "1.1442"
        }
    ],
    "success": true
}
```

---

## 7. 指标表列表

```bash
curl -X GET "http://localhost:8089/api/indicator/list"
```

**响应:**
```json
{
    "code": "0",
    "msg": "success",
    "data": [
        "ADX.py",
        "ATR波幅扫描器.py",
        "CCI.py",
        "KDJ随机指标扫描器.py",
        "MACD柱状扫描器.py",
        "SuperTrend.py",
        ...
    ],
    "success": true
}
```

---

## 8. 指标数据查询

### 查询所有数据
```bash
curl -X GET "http://localhost:8089/api/indicator/data?table=ADX.py&limit=10"
```

### 按币种筛选
```bash
curl -X GET "http://localhost:8089/api/indicator/data?table=MACD柱状扫描器.py&symbol=BTC&limit=5"
```

### 按币种和周期筛选
```bash
curl -X GET "http://localhost:8089/api/indicator/data?table=KDJ随机指标扫描器.py&symbol=ETH&interval=1h&limit=5"
```

**响应:**
```json
{
    "code": "0",
    "msg": "success",
    "data": [
        {
            "交易对": "BTCUSDT",
            "周期": "1h",
            "数据时间": "2026-01-16T01:00:00+00:00",
            "信号概述": "延续",
            "MACD": 417.669451,
            "MACD信号线": 396.58181,
            "MACD柱状图": 42.175282,
            "DIF": 417.669451,
            "DEA": 396.58181,
            "成交额": 0,
            "当前价格": 96100.5
        }
    ],
    "success": true
}
```

**参数说明:**
| 参数 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| table | string | 是 | 指标表名 |
| symbol | string | 否 | 交易对 |
| interval | string | 否 | 周期 (1m/5m/15m/1h/4h) |
| limit | int | 否 | 返回数量 (默认100) |

---

## 9. 信号冷却状态

```bash
curl -X GET "http://localhost:8089/api/signal/cooldown"
```

**响应:**
```json
{
    "code": "0",
    "msg": "success",
    "data": [
        {
            "key": "成交额暴增_BTCUSDT_1h",
            "timestamp": 1768500207603,
            "expireTime": 1768500207603
        },
        {
            "key": "十字星_BNBUSDT_1h",
            "timestamp": 1768490298895,
            "expireTime": 1768490298895
        }
    ],
    "success": true
}
```

---

## 10. Python 调用示例

```python
import requests

BASE_URL = "http://localhost:8089"

# 获取 BTC K线数据
def get_ohlc(symbol: str, limit: int = 100):
    resp = requests.get(f"{BASE_URL}/api/futures/ohlc/history", params={
        "symbol": symbol,
        "interval": "1h",
        "limit": limit
    })
    data = resp.json()
    if data["code"] == "0":
        return data["data"]
    raise Exception(data["msg"])

# 获取指标数据
def get_indicator(table: str, symbol: str = None):
    params = {"table": table, "limit": 100}
    if symbol:
        params["symbol"] = symbol
    resp = requests.get(f"{BASE_URL}/api/indicator/data", params=params)
    return resp.json()["data"]

# 使用示例
btc_klines = get_ohlc("BTC", 50)
macd_data = get_indicator("MACD柱状扫描器.py", "BTC")
```

---

## 11. JavaScript/Node.js 调用示例

```javascript
const BASE_URL = "http://localhost:8089";

// 获取 K线数据
async function getOHLC(symbol, limit = 100) {
    const params = new URLSearchParams({ symbol, interval: "1h", limit });
    const resp = await fetch(`${BASE_URL}/api/futures/ohlc/history?${params}`);
    const data = await resp.json();
    if (data.code === "0") return data.data;
    throw new Error(data.msg);
}

// 获取支持的币种
async function getSupportedCoins() {
    const resp = await fetch(`${BASE_URL}/api/futures/supported-coins`);
    const data = await resp.json();
    return data.data;
}

// 使用示例
const coins = await getSupportedCoins();
const btcKlines = await getOHLC("BTC", 50);
```

---

## 12. 错误响应示例

### 参数错误
```bash
curl "http://localhost:8089/api/futures/ohlc/history?symbol=BTC&interval=invalid"
```
```json
{
    "code": "40003",
    "msg": "无效的 interval: invalid",
    "data": null,
    "success": false
}
```

### 表不存在
```bash
curl "http://localhost:8089/api/indicator/data?table=不存在的表"
```
```json
{
    "code": "40004",
    "msg": "表 '不存在的表' 不存在",
    "data": null,
    "success": false
}
```

### 服务不可用
```json
{
    "code": "50001",
    "msg": "数据库连接失败: ...",
    "data": null,
    "success": false
}
```

---

## 错误码参考

| code | 说明 |
|:---|:---|
| `"0"` | 成功 |
| `"40001"` | 参数错误 |
| `"40002"` | symbol 无效 |
| `"40003"` | interval 无效 |
| `"40004"` | 表不存在 |
| `"50001"` | 服务不可用 |
| `"50002"` | 内部错误 |

---

*文档版本: 1.0*
*最后更新: 2026-01-16*
