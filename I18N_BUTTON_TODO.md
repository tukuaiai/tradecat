# 按钮 i18n 标准化 TODO

> 创建时间: 2026-01-06
> 状态: ✅ 已完成

---

## 📊 完成统计

| 项目 | 数量 | 状态 |
|------|------|------|
| 词条总数 | 430 | ✅ |
| 卡片文件 | 39/39 | ✅ |
| app.py 按钮 | 49 | ✅ |
| signals/ui.py 按钮 | 8 | ✅ |

---

## ✅ 已完成项目

### 1. 通用按钮 (b() 函数)

| 按钮文本 | i18n key | 出现次数 |
|----------|----------|----------|
| 降序 | btn.desc | 36 |
| 升序 | btn.asc | 36 |
| 10条 | btn.10 | 36 |
| 20条 | btn.20 | 36 |
| 30条 | btn.30 | 36 |
| 现货 | btn.spot | 33 |
| 期货 | btn.futures | 33 |

### 2. 菜单按钮 (_btn_auto)

| 按钮文本 | i18n key | 出现次数 |
|----------|----------|----------|
| 🏠主菜单 | btn.home | 36 |
| 🔄刷新 | btn.refresh | 36 |
| ⚙️设置 | btn.settings | 1 |
| ⬅️ 返回KDJ | btn.back_kdj | 1 |

### 3. 字段切换按钮 (InlineKeyboardButton)

| 按钮文本 | i18n key |
|----------|----------|
| 主动多空比 | btn.field.taker_ratio |
| 主动偏离 | btn.field.taker_bias |
| 主动动量 | btn.field.taker_momentum |
| 全体多空比 | btn.field.crowd_ratio |
| 全体偏离 | btn.field.crowd_bias |
| 全体波动 | btn.field.crowd_volatility |
| 大户多空比 | btn.field.top_ratio |
| 大户偏离 | btn.field.top_bias |
| 大户动量 | btn.field.top_momentum |
| 大户波动 | btn.field.top_volatility |
| 持仓变动% | btn.field.oi_change_pct |
| 持仓变动 | btn.field.oi_change |
| 持仓金额 | btn.field.oi_value |

### 4. 排序按钮

| 按钮文本 | i18n key |
|----------|----------|
| 持仓金额 | btn.oi_value |
| 持仓变动% | btn.oi_change_pct |
| 持仓变动 | btn.oi_change |
| 大户波动 | btn.big_volatility |
| 大户多空比 | btn.big_ratio |
| 大户动量 | btn.big_momentum |
| 大户偏离 | btn.big_deviation |
| 全体波动 | btn.all_volatility |
| 全体多空比 | btn.all_ratio |
| 全体偏离 | btn.all_deviation |
| 主动多空比 | btn.taker_ratio |
| 主动动量 | btn.taker_momentum |
| 主动偏离 | btn.taker_deviation |

---

## 📝 修改计划 (已执行)

### Phase 1: 通用按钮替换 ✅
```bash
# 批量替换 b() 函数中的硬编码
sed -i 's/b("降序"/b(_t("btn.desc", None, lang=lang)/g' src/cards/*/*.py
sed -i 's/b("升序"/b(_t("btn.asc", None, lang=lang)/g' src/cards/*/*.py
sed -i 's/b("10条"/b(_t("btn.10", None, lang=lang)/g' src/cards/*/*.py
sed -i 's/b("20条"/b(_t("btn.20", None, lang=lang)/g' src/cards/*/*.py
sed -i 's/b("30条"/b(_t("btn.30", None, lang=lang)/g' src/cards/*/*.py
sed -i 's/b("现货"/b(_t("btn.spot", None, lang=lang)/g' src/cards/*/*.py
sed -i 's/b("期货"/b(_t("btn.futures", None, lang=lang)/g' src/cards/*/*.py
```

### Phase 2: 菜单按钮替换 ✅
```bash
# 批量替换 _btn_auto 中的硬编码
sed -i 's/_btn_auto(None, "🏠主菜单"/_btn_auto(None, _t("btn.home", None, lang=lang)/g' src/cards/*/*.py
sed -i 's/_btn_auto(None, "🔄刷新"/_btn_auto(None, _t("btn.refresh", None, lang=lang)/g' src/cards/*/*.py
sed -i 's/_btn_auto(None, "⚙️设置"/_btn_auto(None, _t("btn.settings", None, lang=lang)/g' src/cards/*/*.py
sed -i 's/_btn_auto(None, "⬅️ 返回KDJ"/_btn_auto(None, _t("btn.back_kdj", None, lang=lang)/g' src/cards/*/*.py
```

### Phase 3: 字段切换按钮替换 ✅
手动修改以下文件:
- `src/cards/futures/主动成交方向排行卡片.py`
- `src/cards/futures/全市场情绪排行卡片.py`
- `src/cards/futures/大户情绪排行卡片.py`
- `src/cards/futures/持仓增减速排行卡片.py`

### Phase 4: 排序按钮替换 ✅
```bash
# 批量替换排序按钮
sed -i 's/b("持仓金额"/b(_t("btn.oi_value", None, lang=lang)/g' src/cards/*/*.py
# ... 其他排序按钮
```

---

## ✅ 验收标准

### 1. 代码检查
```bash
# 检查硬编码中文按钮 (应返回 0)
grep -rPn '(InlineKeyboardButton|_btn_auto|b\()[^)]*"[^"]*[\x{4e00}-\x{9fff}]' src/ | grep -v "_t(" | wc -l
# 结果: 0 ✅
```

### 2. 语法检查
```bash
# 所有卡片文件语法正确
python3 -m py_compile src/cards/*/*.py
# 结果: 无错误 ✅
```

### 3. po 文件验证
```bash
# po 文件格式正确
msgfmt --check locales/zh_CN/LC_MESSAGES/bot.po -o /dev/null
msgfmt --check locales/en/LC_MESSAGES/bot.po -o /dev/null
# 结果: 无错误 ✅
```

### 4. 词条完整性
```bash
# 词条数量
grep -c '^msgid ' locales/zh_CN/LC_MESSAGES/bot.po
# 结果: 430 ✅
```

---

## 📁 涉及文件

### po 文件
- `locales/zh_CN/LC_MESSAGES/bot.po`
- `locales/en/LC_MESSAGES/bot.po`

### 卡片文件 (39个)
- `src/cards/basic/*.py` (11个)
- `src/cards/advanced/*.py` (9个)
- `src/cards/futures/*.py` (19个)

### 其他文件
- `src/bot/app.py`
- `src/signals/ui.py`
- `src/cards/排行榜服务.py`

---

## 🔄 Git 提交记录

```
5675a2b feat(i18n): 排行榜服务 排序/市场文本 i18n - 430词条
249b389 feat(i18n): 表头 排名/币种 i18n 化 - 425词条
c5142c6 feat(i18n): 卡片按钮全部 i18n 化 - 417词条
19d2ad2 feat(i18n): non_blocking_ai_handler i18n - 385词条
34d2461 feat(i18n): signals 模块 i18n (ui.py, formatter.py) - 382词条
```

---

## 🟡 后续优化 (可选)

### 字段名 i18n
- `general_display_fields` 中的标签 (如 "成交额"、"振幅")
- `special_display_fields` 中的标签
- 需要修改 38 个卡片文件的字段定义结构
- 建议: 创建字段名映射表，在运行时动态翻译

### 周期显示 i18n
- `period_display` 字典中的中文 (如 "5分钟"、"1小时")
- 建议: 添加 `period.*` 词条

---

## 📌 标准化规范

### 按钮 i18n 模式
```python
# 正确 ✅
b(_t("btn.desc", None, lang=lang), "callback_data", active=True)
_btn_auto(None, _t("btn.home", None, lang=lang), "ranking_menu")
InlineKeyboardButton(_t("btn.field.taker_ratio", None, lang=lang), callback_data="...")

# 错误 ❌
b("降序", "callback_data", active=True)
_btn_auto(None, "🏠主菜单", "ranking_menu")
InlineKeyboardButton("主动多空比", callback_data="...")
```

### 词条命名规范
```
btn.*           - 通用按钮
btn.field.*     - 字段切换按钮
col.*           - 表头列名
sort.*          - 排序相关
card.*          - 卡片相关
signal.*        - 信号相关
data.*          - 数据状态
error.*         - 错误消息
feature.*       - 功能状态
```
