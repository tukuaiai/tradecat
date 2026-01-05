# i18n 全局适配检查清单

> 生成时间: 2026-01-05
> 当前进度: ~30%

---

## 📊 总体统计

| 模块 | 中文行数 | 按钮数 | 状态 |
|------|----------|--------|------|
| `bot/app.py` | 1455 | 101 | 🔄 进行中 |
| `cards/basic/*.py` | ~200 | - | ❌ 未开始 |
| `cards/advanced/*.py` | ~150 | - | ❌ 未开始 |
| `cards/futures/*.py` | ~200 | - | ❌ 未开始 |
| `cards/data_provider.py` | ~50 | - | ❌ 未开始 |
| `signals/*.py` | ~50 | - | ❌ 未开始 |
| `bot/single_token_snapshot.py` | ~100 | - | ❌ 未开始 |

---

## ✅ 已完成

### 1. 基础设施
- [x] `libs/common/i18n.py` - i18n 服务类
- [x] `locales/zh_CN/LC_MESSAGES/bot.po` - 中文词条 (50+)
- [x] `locales/en/LC_MESSAGES/bot.po` - 英文词条 (50+)
- [x] 编译 `.mo` 文件

### 2. 辅助函数 (app.py)
- [x] `_t(update, key)` - 获取翻译
- [x] `_btn(update, key, callback)` - 国际化按钮工厂
- [x] `_btn_lang(lang, key, callback)` - 按语言创建按钮
- [x] `_sort_text(update, order)` - 排序文本

### 3. 核心界面
- [x] 主菜单文本 `menu.main_text`
- [x] 底部键盘 `kb.*`
- [x] 帮助页面 `help.body`
- [x] 语言切换 `lang.*`
- [x] 启动消息 `start.*`

### 4. 错误消息
- [x] `error.not_ready` - 系统未就绪
- [x] `error.query_failed` - 查询失败
- [x] `error.refresh_failed` - 刷新失败
- [x] `error.export_failed` - 导出失败
- [x] `error.status_failed` - 状态获取失败
- [x] `query.disabled` - 单币查询关闭
- [x] `query.hint` - 查询提示
- [x] `feature.coming_soon` - 功能开发中
- [x] `signal.coming_soon` - 信号功能开发中

### 5. 面板按钮
- [x] `panel.basic` - 💵基础
- [x] `panel.futures` - 📑合约
- [x] `panel.advanced` - 🧠高级
- [x] `panel.pattern` - 🕯️形态

### 6. 通用按钮
- [x] `btn.back_home` - 🏠 返回主菜单
- [x] `btn.refresh` - 🔄 刷新
- [x] `btn.next_page` - 下一页 ➡️
- [x] `btn.prev_page` - ⬅️ 上一页
- [x] `btn.asc` - 升序
- [x] `btn.desc` - 降序
- [x] `btn.show_more` - 显示更多

---

## 🔄 进行中

### app.py 按钮替换 (101处)

#### 返回主菜单按钮 (~20处)
- [ ] L1251: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L1266: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L1769: `InlineKeyboardButton("🔙 返回主菜单", ...)`
- [ ] L2232: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L2245: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L3532: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L3706: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L3713: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L3974: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L4132: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L4161: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L4898: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L4917: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L4936: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L4953: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L4963: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L5193: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L5291: `InlineKeyboardButton("🏠 返回主菜单", ...)`
- [ ] L5309: `InlineKeyboardButton("🏠 返回主菜单", ...)`

#### 比率类型按钮 (L1743-1745)
- [ ] `"持仓/市值"` → `ratio.position_market`
- [ ] `"交易量/市值"` → `ratio.volume_market`
- [ ] `"交易量/持仓"` → `ratio.volume_oi`

#### 排序按钮 (~30处)
- [ ] L1753-1757: `"✅降序"/"升序"` → `btn.desc`/`btn.asc`
- [ ] L2153-2157: `"✅降序"/"升序"`
- [ ] L2198-2201: `"✅降序"/"升序"`

#### 条数按钮 (~10处)
- [ ] L1763-1765: `f"{limit_val}条"` → `sort.items`
- [ ] L2208-2210: `f"{limit_val}条"`

#### 市场类型按钮 (L2091-2095)
- [ ] `"现货"` → `market.spot`
- [ ] `"合约"` → `market.futures`

#### 资金流向按钮 (L2102-2147)
- [ ] `"绝对值"` → `flow.absolute`
- [ ] `"流入"` → `flow.inflow`
- [ ] `"流出"` → `flow.outflow`
- [ ] `"市值"` → `flow.volume`

---

## ❌ 未开始

### 1. 排行榜标题 (app.py)

需要新增词条并替换：

```python
# L1350 成交量排行
f"📈 成交量排行 - 成交额热度榜 📈" → ranking.volume

# L1408 现货交易量
f"💹 {period_text}现货交易量排行榜 💹" → ranking.spot_volume

# L1489 持仓/市值比
f"📊 持仓/市值比排行榜 📊" → ranking.ratio.position_market

# L1581 交易量/市值比
f"📊 交易量/市值比排行榜 📊" → ranking.ratio.volume_market

# L1669 交易量/持仓量比
f"📊 交易量/持仓量比排行榜 📊" → ranking.ratio.volume_oi

# L3454 持仓量排行
f"🐋 持仓量排行 - 大鲸追踪，资金嗅探 🐋" → ranking.position
```

### 2. 资金流向标题 (app.py)

```python
# L1953-1962
f"🟢 合约多头资金流入({period_name})" → flow.title.futures_long
f"🔴 合约空头资金流出({period_name})" → flow.title.futures_short
f"📦 合约交易量排行({period_name})" → flow.title.futures_volume
f"💧 资金流向排行 - 合约({period_name})" → flow.title.futures

# L2042-2051
f"🟢 现货多头资金流入({period_name})" → flow.title.spot_long
f"🔴 现货空头资金流出({period_name})" → flow.title.spot_short
f"📦 现货交易量排行({period_name})" → flow.title.spot_volume
f"💧 现货资金流向排行({period_name})" → flow.title.spot
```

### 3. 时间显示 (app.py)

```python
# 多处
f"⏰ 更新 {time_info['full']}" → time.update
f"⏰ 最后更新 {time_info['full']}" → time.last_update
```

### 4. 周期显示 (app.py)

```python
# L1346-1349
period_display = {
    '5m': '5分钟', '15m': '15分钟', '30m': '30分钟',
    '1h': '1小时', '4h': '4小时', '12h': '12小时', '24h': '24小时'
}
```

需要新增词条：
- `period.5m` = "5分钟" / "5min"
- `period.15m` = "15分钟" / "15min"
- `period.1h` = "1小时" / "1hour"
- `period.4h` = "4小时" / "4hours"
- `period.24h` = "24小时" / "24hours"

### 5. 卡片模块 (cards/*.py)

每个卡片文件包含：
- 卡片标题
- 字段名称
- 提示文本
- 按钮文本

示例 `KDJ排行卡片.py`:
```python
FALLBACK = "🔄 KDJ 数据准备中"
description = "KDJ 随机指标强度榜"
("quote_volume", "成交额", False)
("振幅", "振幅", False)
"暂无数据"
```

### 6. 信号模块 (signals/*.py)

```python
# engine_v2.py
f"非法表名: {table}"
f"读取表 {table} 失败: {e}"
f"信号触发: {symbol} {rule.direction} - {rule.name}"

# formatter.py
信号格式化文本
```

### 7. 单币快照 (single_token_snapshot.py)

```python
# 字段映射
("bandwidth", "带宽")
("百分比b", "百分比")
("支撑位", "支撑位")
("阻力位", "阻力位")
```

---

## 📝 需要新增的词条

### bot.po 补充词条

```po
# 周期
msgid "period.5m"
msgstr "5分钟" / "5min"

msgid "period.15m"
msgstr "15分钟" / "15min"

msgid "period.1h"
msgstr "1小时" / "1hour"

msgid "period.4h"
msgstr "4小时" / "4hours"

msgid "period.24h"
msgstr "24小时" / "24hours"

# 排行榜
msgid "ranking.spot_volume"
msgstr "💹 现货交易量排行榜 💹" / "💹 Spot Volume Ranking 💹"

# 数据字段（可选，保持中文也可）
msgid "field.volume"
msgstr "成交额" / "Volume"

msgid "field.amplitude"
msgstr "振幅" / "Amplitude"

msgid "field.trades"
msgstr "成交笔数" / "Trades"
```

---

## 🔧 实施建议

### 优先级 P0 (用户直接可见)
1. 剩余按钮替换 (~100处)
2. 排行榜标题替换 (~10处)
3. 错误消息补全

### 优先级 P1 (功能界面)
1. 资金流向标题
2. 时间显示格式
3. 周期显示

### 优先级 P2 (数据展示)
1. 卡片模块 - 可保持中文字段名
2. 信号模块
3. 单币快照

### 优先级 P3 (内部日志)
1. 日志消息 - 可保持中文
2. 注释 - 无需翻译

---

## 📋 检查命令

```bash
# 统计剩余中文按钮
grep -nP 'InlineKeyboardButton.*[\x{4e00}-\x{9fff}]' src/bot/app.py | wc -l

# 统计剩余中文行
grep -cP '[\x{4e00}-\x{9fff}]' src/bot/app.py

# 查找特定中文
grep -n '"返回主菜单"' src/bot/app.py

# 验证翻译文件
msgfmt --check locales/zh_CN/LC_MESSAGES/bot.po
msgfmt --check locales/en/LC_MESSAGES/bot.po
```

---

## 📅 更新记录

| 日期 | 内容 |
|------|------|
| 2026-01-05 | 初始创建，完成核心界面适配 (~30%) |
