#!/bin/bash

# ============================================================================
# Polymarket Signal Bot - 统一启动脚本
# 自动检测网络，智能启动Telegram信号Bot
# ============================================================================

# 项目配置
PROJECT_DIR="/home/lenovo/.projects/polymarket"
BOT_DIR="$PROJECT_DIR/bot"
PROXY_CONFIG="$PROJECT_DIR/proxychains.conf"
PROXY_HOST="127.0.0.1"
PROXY_PORT="9910"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# 进入项目目录
cd "$PROJECT_DIR" || exit 1

# 打印横幅
print_banner() {
    clear
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}         🤖 Polymarket Signal Bot ${NC}"
    echo -e "${CYAN}         实时套利 + 订单簿失衡检测${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# 检查父项目依赖和构建
check_parent_project() {
    echo -e "${CYAN}📦 检查父项目...${NC}"

    # 检查依赖
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}   正在安装父项目依赖...${NC}"
        npm install > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo -e "${RED}   ❌ 父项目依赖安装失败${NC}"
            return 1
        fi
    fi

    # 检查构建
    if [ ! -d "dist" ] || [ "src" -nt "dist" ]; then
        echo -e "${YELLOW}   正在构建父项目...${NC}"
        npm run build > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo -e "${RED}   ❌ 父项目构建失败${NC}"
            return 1
        fi
    fi

    echo -e "${GREEN}   ✅ 父项目就绪${NC}"
    return 0
}

# 检查Bot依赖
check_bot_dependencies() {
    echo -e "${CYAN}📦 检查Bot依赖...${NC}"

    cd "$BOT_DIR"

    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}   正在安装Bot依赖...${NC}"
        npm install > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo -e "${RED}   ❌ Bot依赖安装失败${NC}"
            return 1
        fi
    fi

    echo -e "${GREEN}   ✅ Bot依赖就绪${NC}"
    cd "$PROJECT_DIR"
    return 0
}

# 检查配置
check_config() {
    echo -e "${CYAN}⚙️  检查配置...${NC}"

    cd "$BOT_DIR"

    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}   创建.env文件...${NC}"
        cp ".env.example" ".env" 2>/dev/null || true
    fi

    # 读取配置
    if [ -f ".env" ]; then
        source ".env"

        local warnings=0

        if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_bot_token_here" ]; then
            echo -e "${YELLOW}   ⚠️  Telegram Bot Token未配置${NC}"
            warnings=$((warnings + 1))
        fi

        if [ -z "$TELEGRAM_CHAT_ID" ] || [ "$TELEGRAM_CHAT_ID" = "your_chat_id_here" ]; then
            echo -e "${YELLOW}   ⚠️  Telegram Chat ID未配置${NC}"
            warnings=$((warnings + 1))
        fi

        if [ $warnings -gt 0 ]; then
            echo -e "${YELLOW}   请编辑 bot/.env 文件配置Telegram信息${NC}"
        else
            echo -e "${GREEN}   ✅ 配置完整${NC}"
        fi
    fi

    cd "$PROJECT_DIR"
    return 0
}

# 测试网络
test_network() {
    timeout 5 bash -c "echo > /dev/tcp/ws-live-data.polymarket.com/443" 2>/dev/null
    return $?
}

# 测试代理
test_proxy() {
    timeout 3 bash -c "echo > /dev/tcp/$PROXY_HOST/$PROXY_PORT" 2>/dev/null
    return $?
}

# 安装 proxychains4
install_proxychains() {
    echo -e "${YELLOW}📦 正在安装 proxychains4...${NC}"

    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y proxychains4
    elif command -v yum &> /dev/null; then
        sudo yum install -y proxychains-ng
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm proxychains-ng
    else
        echo -e "${RED}❌ 无法自动安装 proxychains4${NC}"
        echo -e "${YELLOW}请手动安装:${NC}"
        echo "  Ubuntu/Debian: sudo apt-get install proxychains4"
        return 1
    fi

    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ proxychains4 安装失败${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ proxychains4 安装成功${NC}"
    return 0
}

# 启动Bot
start_bot() {
    local network_mode=$1  # auto / direct / proxy

    cd "$BOT_DIR"

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🎬 启动 Polymarket Signal Bot${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # 根据网络模式启动
    case $network_mode in
        "auto")
            # 自动检测
            echo -e "${CYAN}🔍 检测网络环境...${NC}"
            if test_network; then
                echo -e "${GREEN}✅ 网络正常，使用直连${NC}"
                echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo -e "${YELLOW}💡 按 Ctrl+C 停止Bot${NC}"
                echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo ""
                node src/bot.js
            else
                echo -e "${YELLOW}⚠️  直连失败，尝试代理模式${NC}"
                if ! test_proxy; then
                    echo -e "${RED}❌ 代理不可用 ($PROXY_HOST:$PROXY_PORT)${NC}"
                    echo -e "${YELLOW}请先启动代理服务${NC}"
                    return 1
                fi
                echo -e "${GREEN}✅ 代理可用${NC}"

                if ! command -v proxychains4 &> /dev/null; then
                    echo -e "${YELLOW}⚠️  未安装 proxychains4${NC}"
                    read -p "是否安装? [Y/n] " -n 1 -r
                    echo ""
                    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
                        install_proxychains || return 1
                    else
                        return 1
                    fi
                fi

                echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo -e "${MAGENTA}📡 使用代理: http://$PROXY_HOST:$PROXY_PORT${NC}"
                echo -e "${YELLOW}💡 按 Ctrl+C 停止Bot${NC}"
                echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo ""
                proxychains4 -q -f "$PROXY_CONFIG" node src/bot.js
            fi
            ;;

        "direct")
            # 强制直连
            echo -e "${GREEN}📶 强制直连模式${NC}"
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${YELLOW}💡 按 Ctrl+C 停止Bot${NC}"
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            node src/bot.js
            ;;

        "proxy")
            # 强制代理
            echo -e "${MAGENTA}🔒 强制代理模式${NC}"

            if ! test_proxy; then
                echo -e "${RED}❌ 代理不可用 ($PROXY_HOST:$PROXY_PORT)${NC}"
                echo -e "${YELLOW}请先启动代理服务${NC}"
                return 1
            fi

            if ! command -v proxychains4 &> /dev/null; then
                echo -e "${YELLOW}⚠️  未安装 proxychains4${NC}"
                read -p "是否安装? [Y/n] " -n 1 -r
                echo ""
                if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
                    install_proxychains || return 1
                else
                    return 1
                fi
            fi

            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${MAGENTA}📡 使用代理: http://$PROXY_HOST:$PROXY_PORT${NC}"
            echo -e "${YELLOW}💡 按 Ctrl+C 停止Bot${NC}"
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            proxychains4 -q -f "$PROXY_CONFIG" node src/bot.js
            ;;
    esac

    local exit_code=$?

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ Bot正常退出${NC}"
    else
        echo -e "${RED}❌ Bot异常退出 (退出码: $exit_code)${NC}"
    fi
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    return $exit_code
}

# 显示主菜单
show_menu() {
    print_banner

    echo -e "${CYAN}请选择启动模式:${NC}"
    echo ""
    echo -e "${GREEN}  【网络模式】${NC}"
    echo -e "  ${YELLOW}1.${NC} 自动检测 ${CYAN}(推荐)${NC}"
    echo -e "  ${YELLOW}2.${NC} 强制直连"
    echo -e "  ${YELLOW}3.${NC} 强制代理"
    echo ""
    echo -e "${GREEN}  【快捷选项】${NC}"
    echo -e "  ${YELLOW}Q.${NC} 快速启动 ${CYAN}(自动检测，最常用)${NC}"
    echo ""
    echo -e "  ${YELLOW}0.${NC} 退出"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 主函数
main() {
    # 检查依赖
    print_banner
    echo -e "${CYAN}🔍 检查环境...${NC}"
    echo ""
    check_parent_project || exit 1
    check_bot_dependencies || exit 1
    check_config
    echo ""

    # 如果有命令行参数，处理命令行参数
    if [ $# -gt 0 ]; then
        case "$1" in
            "--menu"|"-m")
                # 显示交互式菜单
                ;;
            "quick"|"q"|"Q")
                start_bot "auto"
                exit $?
                ;;
            "auto"|"a"|"A")
                start_bot "auto"
                exit $?
                ;;
            "direct"|"d"|"D")
                start_bot "direct"
                exit $?
                ;;
            "proxy"|"p"|"P")
                start_bot "proxy"
                exit $?
                ;;
            "--help"|"-h")
                echo "用法: $0 [选项]"
                echo ""
                echo "默认行为:"
                echo "  无参数          自动检测网络 (推荐)"
                echo ""
                echo "快捷选项:"
                echo "  quick, q, Q     自动检测网络 (推荐)"
                echo "  auto,  a, A     自动检测网络"
                echo "  direct, d, D    强制直连"
                echo "  proxy, p, P     强制代理"
                echo ""
                echo "其他:"
                echo "  --menu, -m      显示交互式菜单"
                echo "  --help, -h      显示帮助信息"
                echo ""
                echo "示例:"
                echo "  $0              # 自动检测（推荐）"
                echo "  $0 quick        # 快速启动"
                echo "  $0 proxy        # 强制代理"
                echo "  $0 --menu       # 显示菜单"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 未知选项: $1${NC}"
                echo "使用 $0 --help 查看帮助"
                exit 1
                ;;
        esac
    else
        # 无参数时，默认自动检测
        echo -e "${GREEN}🚀 自动检测网络模式 (推荐)${NC}"
        echo -e "${CYAN}💡 提示: 使用 $0 --menu 显示完整菜单${NC}"
        echo ""
        start_bot "auto"
        exit $?
    fi

    # 交互式菜单
    while true; do
        show_menu
        read -p "请输入选项: " choice

        case $choice in
            1|[aA])
                start_bot "auto"
                echo ""
                read -p "按回车继续..." dummy
                ;;
            2|[dD])
                start_bot "direct"
                echo ""
                read -p "按回车继续..." dummy
                ;;
            3|[pP])
                start_bot "proxy"
                echo ""
                read -p "按回车继续..." dummy
                ;;
            [qQ])
                start_bot "auto"
                echo ""
                read -p "按回车继续..." dummy
                ;;
            0)
                echo -e "${GREEN}👋 再见！${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 无效选择，请重试${NC}"
                sleep 1
                ;;
        esac
    done
}

# 运行主函数
main "$@"
