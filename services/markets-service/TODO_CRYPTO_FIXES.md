# Crypto 模块修复 TODO

## 状态说明
- ☐ 待处理
- ⏳ 进行中
- ✅ 已完成
- ❌ 阻塞

---

## 修复清单

| ID | 问题 | 优先级 | 状态 |
|:---|:---|:---:|:---:|
| F-01 | 数据库密码硬编码 | P0 | ✅ |
| F-02 | SQL 注入风险 | P1 | ✅ |
| F-03 | 双模式写入原子性 | P1 | ✅ |
| F-04 | batch_id 获取失败无回退 | P1 | ✅ |
| F-05 | 配置验证缺失 | P2 | ✅ |
| R2-01 | 遗留方法 SQL 拼接 | P2 | ✅ |
| R2-02 | 默认密码警告 | P3 | ✅ |
| R2-03 | 废弃 _quote_val 方法 | P3 | ✅ |

---

## Round 1 修复 (2026-01-05)

### F-01 ~ F-05: 见上方表格，全部完成

---

## Round 2 修复 (2026-01-05)

### R2-01: 遗留方法 SQL 拼接 [P2]

**状态**: ✅ 已完成

**修复**:
- `get_symbols()`, `get_counts()`, `detect_gaps()`, `query()` 使用 `sql.Identifier`
- `_get_batch_id()` 使用 `sql.Identifier` 包装 schema 名
- 所有方法添加 `validate_table_name()` 验证

### R2-02: 默认密码警告 [P3]

**状态**: ✅ 已完成

**修复**: `_validate()` 中检测 `postgres:postgres@` 并输出警告日志

### R2-03: 废弃 _quote_val 方法 [P3]

**状态**: ✅ 已完成

**修复**: 删除 `_quote_val()` 方法

---

## 验收记录

| 日期 | 轮次 | 测试项 | 结果 |
|:---|:---:|:---|:---:|
| 2026-01-05 | R1 | F-01 硬编码密码检查 | ✅ |
| 2026-01-05 | R1 | F-02 表名白名单验证 | ✅ |
| 2026-01-05 | R1 | F-03 WriteResult 数据类 | ✅ |
| 2026-01-05 | R1 | F-04 安全 batch_id 获取 | ✅ |
| 2026-01-05 | R1 | F-05 配置验证 | ✅ |
| 2026-01-05 | R2 | R2-01 f-string SQL 消除 | ✅ |
| 2026-01-05 | R2 | R2-02 默认密码警告 | ✅ |
| 2026-01-05 | R2 | R2-03 _quote_val 删除 | ✅ |
| 2026-01-05 | R2 | crypto-scan 功能验证 | ✅ |

---

## 修改文件清单

| 文件 | Round 1 | Round 2 |
|:---|:---|:---|
| `src/crypto/config.py` | WriteMode, ALLOWED_TABLES, validate_table_name, _validate | 默认密码警告 |
| `src/crypto/schema_adapter.py` | 表名函数使用白名单验证 | - |
| `src/crypto/adapters/timescale.py` | WriteResult, _get_batch_id_safe | sql.Identifier, 删除 _quote_val |
