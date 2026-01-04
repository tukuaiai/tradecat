# 贡献指南

## 协作规则

### 文档优先原则
- 所有变更必须关联 `docs/` 下的文档链接
- 新功能需先在 `docs/requirements/` 创建需求文档
- 架构变更需在 `docs/decisions/adr/` 创建 ADR

### 提交规范
- 提交信息格式：`<type>: <description>`
- type: feat/fix/docs/refactor/test/chore
- 必须包含关联的文档链接

### Git 钩子启用
```bash
git config core.hooksPath .githooks
```

### 代码风格
- 2 空格缩进
- 单引号字符串
- camelCase 变量/函数
- UPPER_SNAKE_CASE 常量

### PR 要求
- 填写 `.github/PULL_REQUEST_TEMPLATE.md` 模板
- 关联 docs 链接
- 通过 `scripts/verify.sh` 检查

## 目录约定

| 目录 | 用途 |
|------|------|
| `docs/requirements/` | 需求文档 |
| `docs/design/` | 设计文档 |
| `docs/decisions/adr/` | 架构决策记录 |
| `docs/prompts/` | Prompt 模板 |
| `docs/sessions/` | 会话记录 |
| `docs/retros/` | 迭代复盘 |

## 禁止行为
- 直接提交 `.env` 或密钥文件
- 修改 `libs/external/` 下的文件
- 删除运行时数据文件

---
*最后更新：2025-12-30*
