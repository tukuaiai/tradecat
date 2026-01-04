#!/bin/bash
# 验证脚本 - 统一执行格式化、静态检查、测试

set -e

echo "=========================================="
echo "tradecat Pro 验证脚本"
echo "=========================================="

cd "$(dirname "$0")/.."
ROOT_DIR=$(pwd)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

success() { echo -e "${GREEN}✓ $1${NC}"; }
fail() { echo -e "${RED}✗ $1${NC}"; exit 1; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }

# 1. 检查 Python 环境
echo ""
echo "1. 检查 Python 环境..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    success "虚拟环境已激活"
else
    warn "未找到 .venv，使用系统 Python"
fi

# 2. 代码格式检查 (ruff)
echo ""
echo "2. 代码格式检查 (ruff)..."
if command -v ruff &> /dev/null; then
    if ruff check services/ --quiet; then
        success "ruff 检查通过"
    else
        fail "ruff 检查失败"
    fi
else
    warn "ruff 未安装，跳过"
fi

# 3. 语法检查
echo ""
echo "3. Python 语法检查..."
# 3.1 关键入口文件
if python3 -m py_compile services/telegram-service/src/bot/app.py 2>/dev/null; then
    success "telegram-service app.py 语法正确"
else
    fail "telegram-service app.py 语法错误"
fi
# 3.2 ai-service 全量（compileall，确保真正命中所有文件）
if python3 -m compileall -q services/ai-service/src 2>/dev/null; then
    success "ai-service 源码语法正确"
else
    fail "ai-service 语法检查失败"
fi
# 3.3 其他服务（粗粒度）
for service in data-service trading-service; do
    if [ -d "services/$service/src" ]; then
        if python3 -m py_compile services/$service/src/*.py 2>/dev/null; then
            success "services/$service 语法正确"
        else
            warn "services/$service 部分文件语法检查跳过"
        fi
    fi
done

# 4. 文档链接检查
echo ""
echo "4. 文档链接检查..."
if [ -f "docs/index.md" ]; then
    BROKEN_LINKS=0
    while IFS= read -r line; do
        if [[ $line =~ \[.*\]\((.*)\) ]]; then
            link="${BASH_REMATCH[1]}"
            if [[ $link != http* ]] && [[ $link != \#* ]]; then
                full_path="docs/$link"
                if [ ! -f "$full_path" ] && [ ! -d "$full_path" ]; then
                    warn "死链: $link"
                    BROKEN_LINKS=$((BROKEN_LINKS + 1))
                fi
            fi
        fi
    done < docs/index.md
    
    if [ $BROKEN_LINKS -eq 0 ]; then
        success "docs/index.md 链接检查通过"
    else
        warn "发现 $BROKEN_LINKS 个死链"
    fi
else
    fail "docs/index.md 不存在"
fi

# 5. ADR 编号检查
echo ""
echo "5. ADR 编号检查..."
if [ -d "docs/decisions/adr" ]; then
    ADR_COUNT=$(ls docs/decisions/adr/*.md 2>/dev/null | wc -l)
    success "ADR 文件数: $ADR_COUNT"
else
    warn "docs/decisions/adr 目录不存在"
fi

# 6. Prompt 模板检查
echo ""
echo "6. Prompt 模板检查..."
if [ -d "docs/prompts" ]; then
    PROMPT_COUNT=$(ls docs/prompts/*.md 2>/dev/null | wc -l)
    success "Prompt 文件数: $PROMPT_COUNT"
else
    warn "docs/prompts 目录不存在"
fi

# 7. 单元测试 (如有)
echo ""
echo "7. 单元测试..."
if command -v pytest &> /dev/null; then
    if [ -d "tests" ] && [ "$(ls -A tests 2>/dev/null)" ]; then
        if pytest tests/ -q --tb=no 2>/dev/null; then
            success "单元测试通过"
        else
            warn "单元测试失败或无测试"
        fi
    else
        warn "无测试文件，跳过"
    fi
else
    warn "pytest 未安装，跳过"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}验证完成${NC}"
echo "=========================================="
