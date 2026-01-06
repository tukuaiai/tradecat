# i18n 全局适配检查清单

> 生成时间: 2026-01-05
> 当前进度: ~80%

---

## 📊 总体统计

| 模块 | 中文行数 | 按钮数 | 状态 |
|------|----------|--------|------|
| `bot/app.py` | 1455 | 101 | 🟡 按钮/标题已替换，待卡片/信号 |
| `cards/basic/*.py` | ~200 | 按钮 | 🟢 按钮已 i18n，字段/描述待补 |
| `cards/advanced/*.py` | ~150 | 按钮 | 🟢 按钮已 i18n，字段/描述待补 |
| `cards/futures/*.py` | ~200 | 按钮 | 🟢 按钮已 i18n，字段/描述待补 |
| `cards/data_provider.py` | ~50 | - | ❌ 未开始 |
| `signals/*.py` | ~50 | - | ❌ 未开始 |
| `bot/single_token_snapshot.py` | ~100 | - | 🟢 标题/提示已 i18n，字段待评估 |

---

## ✅ 已完成

### 1. 基础设施
- [x] `libs/common/i18n.py` - i18n 服务类
- [x] `locales/zh_CN/LC_MESSAGES/bot.po` - 中文词条 (50+)
- [x] `locales/en/LC_MESSAGES/bot.po` - 英文词条 (50+)
- [x] 编译 `.mo` 文件
- [x] 翻译缺失告警（日志一次性记录），缺词回退原值

### 2. 辅助函数 (app.py)
- [x] `_t(update, key)` - 获取翻译
- [x] `_btn(update, key, callback)` - 国际化按钮工厂
- [x] `_btn_lang(lang, key, callback)` - 按语言创建按钮
- [x] `_sort_text(update, order)` - 排序文本
- [x] `_period_text(_lang)` - 周期缺词安全回退

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
- [x] 排序/数量/市场/流向按钮 i18n 化（比率、资金流向、持仓排行等）
- [x] 主菜单返回键全量替换 `_btn/_btn_lang`

### 7. 排行榜与标题
- [x] 成交量/现货成交量标题 → `ranking.volume` / `ranking.spot_volume`
- [x] 持仓/市值、交易量相关比率标题 → `ranking.ratio.*`
- [x] 资金流向标题 → `flow.title.*`
- [x] 时间显示 → `time.update` / `time.last_update`
- [x] 周期显示 → `period.*`
- [x] 资金流向说明文本 → `flow.desc.*`（含期权流向）

---

## 🔄 进行中

### app.py / snapshot 剩余工作
- [ ] 卡片注册/信号/日志等零散中文（部分按钮已 i18n，仍需字段/提示）
- [ ] 单币快照字段映射（带宽/支撑位等）
- [ ] snapshot 表头字段翻译（字段名/卡片名）

---

## ❌ 未开始

### 1. 卡片模块 (cards/*.py)
- [x] 按钮文本统一 `_btn_auto`
- [ ] 标题/描述/FALLBACK/提示词条化（参照 trendline/divergence 模板）
- [ ] 字段标签与来源说明词条化

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
4. CI 增加 i18n 词条检查（已接入 `scripts/verify.sh`，需保持通过）

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

# I18N 待办（文本适配阶段）
# 生成时间：2026-01-05

## 已完成
- 全量按钮国际化（全部卡片/信号使用 _btn_auto，无中文按钮字面量）。
- KDJ 排行文本 i18n：card.kdj.* 词条，包含标题/提示/设置页/无数据/FALLBACK；mo 已编译；验证通过（仅保留 po 头警告、docs/index.md 缺失）。
- 进度文档 I18N_TODO 更新至 ~80%，按钮完成，文本待补。

## 未完成（按优先级/批次）
### P0 文本 i18n（逐批提交）
- basic 组（标题/描述/提示/来源/FALLBACK/字段标签）：
  - 布林带排行卡片.py
  - MACD柱状排行卡片.py
  - 成交量排行卡片.py
  - 成交量比率排行卡片.py
  - 支撑阻力排行卡片.py
  - OBV排行卡片.py
  - RSI谐波排行卡片.py
  - 资金流向卡片.py
- advanced 组：ATR、EMA、K线形态、CVD、VPVR、VWAP、MFI、超级精准趋势、流动性。
- futures 组：持仓/持仓增减速/OI 系列/主动成交系/情绪类/资金费率/市场深度/风险拥挤/波动度/翻转雷达等全部文件。
- signals 文案：signals/formatter.py、signals/rules/*（对用户可见的提示/错误文本全部 _t 化）。
- 单币快照：字段标签与卡片名词条化（snapshot.field.* / snapshot.card.*）。

### P1
- 为新增词条补全中英翻译，清理 check_i18n_keys 报出的冗余键。
- 将 scripts/check_i18n_keys.py 纳入 CI；保留 msgfmt 检查。

### 回归/验证
- zh/en 回归：/vol /flow 与持仓/比率/资金流向链路，检查键盘与文案一致、无 raw key。
- msgfmt --check 与 python3 scripts/check_i18n_keys.py。

### 已知警告
- po 头部缺少元信息（历史 warning）。
- docs/index.md 缺失（verify 报告）。

## 执行建议
- 逐批（1–3 文件）手工改写文本，补词条后编译 mo，运行 verify，再提交。
