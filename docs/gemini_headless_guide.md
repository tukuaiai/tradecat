# Gemini CLI 完全使用指南 (含无头模式与模型配置)

## 1. 模型配置与默认设置
你可以通过 `-m` 参数指定使用的模型。例如，使用 `gemini-3-flash-preview`（或当前最新的 `gemini-3-flash-preview`）。

### 设置默认模型 (Shell Alias)
要永久使用特定模型，建议在 `~/.bashrc` 或 `~/.zshrc` 中添加别名：
```bash
alias gemini='gemini -m gemini-3-flash-preview'
```

---

## 2. 核心参数详解与具体用例

### A. 交互与输入
- **`query` (直接输入)**
  - **用例**：单次快速问答。
  ```bash
  gemini "写一个 Golang 的 HTTP 客户端示例"
  ```
- **`-i, --prompt-interactive`**
  - **用例**：执行指令后进入交互模式，方便后续追问。
  ```bash
  gemini -i "读取并解释 package.json"
  ```
- **管道输入 (Piping)**
  - **用例**：处理其他命令的输出。
  ```bash
  cat error.log | gemini "分析这些错误产生的原因"
  ```

### B. 自动化与授权 (脚本集成)
- **`-y, --yolo`**
  - **用例**：全自动模式，无需人工确认即可执行所有建议操作。
  ```bash
  gemini "将目录下所有 .txt 文件改为 .md" --yolo
  ```
- **`--approval-mode`**
  - **用例**：精细化授权。
  ```bash
  # 自动编辑代码，但涉及 Shell 命令时需手动确认
  gemini "优化代码结构" --approval-mode auto_edit
  ```

### C. 安全与环境
- **`-s, --sandbox`**
  - **用例**：在受限的隔离环境中运行，防止 Gemini 建议的命令对系统造成破坏。
  ```bash
  gemini "运行这段复杂的清理脚本" --sandbox --yolo
  ```
- **`--include-directories`**
  - **用例**：引入外部目录作为上下文。
  ```bash
  gemini "对比当前项目与备份项目的不同" --include-directories ../backup-project
  ```

### D. 输出格式化
- **`-o, --output-format`**
  - **用例**：生成机器可读的 JSON 供脚本解析。
  ```bash
  gemini "提取文档中的所有 API 接口" --output-format json
  ```

### E. 会话管理
- **`-r, --resume`**
  - **用例**：继续上一次对话。
  ```bash
  gemini "继续刚才的重构工作" --resume latest --yolo
  ```
- **`--list-sessions`**
  - **用例**：查看历史会话列表。
  ```bash
  gemini --list-sessions
  ```

### F. 调试与诊断
- **`-d, --debug`**
  - **用例**：遇到连接问题或 MCP 错误时查看详细日志。
  ```bash
  gemini "测试 MCP 服务器连接" --debug
  ```

---

## 3. 无头模式 (Headless Mode) 实战
无头模式指在脚本中调用 Gemini，并在完成后自动退出。

### 自动生成 Git Commit 脚本
```bash
#!/bin/bash
DIFF=$(git diff --cached)
if [ -n "$DIFF" ]; then
    echo "$DIFF" | gemini "生成简洁的 commit message" -m gemini-3-flash-preview | git commit -F -
fi
```

### 自动修复 Lint 错误
```bash
#!/bin/bash
LINT_ERRORS=$(npm run lint 2>&1)
if [ $? -ne 0 ]; then
    echo "$LINT_ERRORS" | gemini "修复这些 lint 错误" --yolo
fi
```

---

## 4. 常见问题
1. **如何关闭 MCP？**
   使用 `gemini mcp remove --scope user <name>`。
2. **命令执行卡住？**
   检查是否遗漏了 `--yolo` 参数，脚本模式下需要自动批准。
3. **模型不存在？**
   请确保使用 `-m` 指定的模型名称是正确的，如 `gemini-3-flash-preview`。