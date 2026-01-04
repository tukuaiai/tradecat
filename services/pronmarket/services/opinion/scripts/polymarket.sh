#!/bin/bash

# ============================================================================
# Polymarket 统一启动脚本
# 整合所有启动方式，提供交互式菜单
# ============================================================================

# 项目配置
PROJECT_DIR="/home/lenovo/.projects/polymarket"
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
    echo -e "${GREEN}         🚀 Polymarket 实时数据客户端 ${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# 检查依赖
check_dependencies() {
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 安装依赖...${NC}"
        yarn install > /dev/null 2>&1 || npm install > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ 依赖安装失败${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ 依赖安装完成${NC}"
    fi

    if [ ! -d "dist" ]; then
        echo -e "${YELLOW}🔨 构建项目...${NC}"
        yarn build > /dev/null 2>&1 || npm run build > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ 构建失败${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ 构建完成${NC}"
    fi
}

# 测试网络
test_network() {
    bash "$PROJECT_DIR/test-network.sh" 1
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
        echo "  CentOS/RHEL:   sudo yum install proxychains-ng"
        echo "  Arch Linux:    sudo pacman -S proxychains-ng"
        return 1
    fi

    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ proxychains4 安装失败${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ proxychains4 安装成功${NC}"
    return 0
}

# 启动客户端
start_client() {
    local client_type=$1   # minimal / full
    local network_mode=$2  # auto / direct / proxy
    local verbose_mode=$3  # 1 / 0 (详细日志模式)

    local client_script=""
    local mode_name=""

    # 选择客户端脚本
    if [ "$client_type" == "minimal" ]; then
        client_script="minimal-client.js"
        mode_name="极简模式"
    else
        client_script="full-client.js"
        mode_name="完整订阅模式"
    fi

    # 设置详细日志环境变量
    if [ "$verbose_mode" == "1" ]; then
        export VERBOSE=1
        mode_name="${mode_name} (详细日志)"
    else
        unset VERBOSE
    fi

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🎬 启动模式: ${mode_name}${NC}"

    # 根据网络模式启动
    case $network_mode in
        "auto")
            # 自动检测
            echo -e "${CYAN}🔍 检测网络环境...${NC}"
            if test_network; then
                echo -e "${GREEN}✅ 网络正常，使用直连${NC}"
                echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo -e "${YELLOW}💡 按 Ctrl+C 停止程序${NC}"
                echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo ""
                node "$client_script"
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
                echo -e "${YELLOW}💡 按 Ctrl+C 停止程序${NC}"
                echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo ""
                proxychains4 -q -f "$PROXY_CONFIG" node "$client_script"
            fi
            ;;

        "direct")
            # 强制直连
            echo -e "${GREEN}📶 强制直连模式${NC}"
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${YELLOW}💡 按 Ctrl+C 停止程序${NC}"
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            node "$client_script"
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
            echo -e "${YELLOW}💡 按 Ctrl+C 停止程序${NC}"
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            proxychains4 -q -f "$PROXY_CONFIG" node "$client_script"
            ;;
    esac

    local exit_code=$?
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ 程序正常退出${NC}"
    else
        echo -e "${RED}❌ 程序异常退出 (退出码: $exit_code)${NC}"
    fi
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    return $exit_code
}

# 显示主菜单
show_menu() {
    print_banner

    echo -e "${CYAN}请选择启动模式:${NC}"
    echo ""
    echo -e "${GREEN}  【客户端类型】${NC}"
    echo -e "  ${YELLOW}1.${NC} 极简模式 ${CYAN}(简化日志，快速启动)${NC}"
    echo -e "  ${YELLOW}2.${NC} 完整订阅模式 ${CYAN}(所有数据，适合分析)${NC}"
    echo ""
    echo -e "${GREEN}  【网络模式】${NC}"
    echo -e "  ${YELLOW}A.${NC} 自动检测 ${CYAN}(推荐)${NC}"
    echo -e "  ${YELLOW}B.${NC} 强制直连"
    echo -e "  ${YELLOW}C.${NC} 强制代理"
    echo ""
    echo -e "${GREEN}  【快捷选项】${NC}"
    echo -e "  ${YELLOW}Q.${NC} 快速启动 ${CYAN}(极简+自动，最常用)${NC}"
    echo -e "  ${YELLOW}F.${NC} 完整启动 ${CYAN}(完整+自动)${NC}"
    echo -e "  ${YELLOW}D.${NC} 调试模式 ${CYAN}(极简+自动+详细日志)${NC}"
    echo -e "  ${YELLOW}V.${NC} 详细日志启动 ${CYAN}(选择模式后启用详细日志)${NC}"
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
    check_dependencies
    echo ""

    # 检查是否有 --verbose 参数
    local verbose_flag=0
    for arg in "$@"; do
        if [ "$arg" == "--verbose" ] || [ "$arg" == "-v" ]; then
            verbose_flag=1
            break
        fi
    done

    # 如果有命令行参数，处理命令行参数
    if [ $# -gt 0 ]; then
        case "$1" in
            "--menu"|"-m")
                # 显示交互式菜单
                ;;
            "quick"|"q"|"Q")
                start_client "minimal" "auto" "$verbose_flag"
                exit $?
                ;;
            "full"|"f"|"F")
                start_client "full" "auto" "$verbose_flag"
                exit $?
                ;;
            "debug"|"d"|"D")
                start_client "minimal" "auto" 1
                exit $?
                ;;
            "minimal-auto"|"ma")
                start_client "minimal" "auto" "$verbose_flag"
                exit $?
                ;;
            "minimal-direct"|"md")
                start_client "minimal" "direct" "$verbose_flag"
                exit $?
                ;;
            "minimal-proxy"|"mp")
                start_client "minimal" "proxy" "$verbose_flag"
                exit $?
                ;;
            "full-auto"|"fa")
                start_client "full" "auto" "$verbose_flag"
                exit $?
                ;;
            "full-direct"|"fd")
                start_client "full" "direct" "$verbose_flag"
                exit $?
                ;;
            "full-proxy"|"fp")
                start_client "full" "proxy" "$verbose_flag"
                exit $?
                ;;
            "--help"|"-h")
                echo "用法: $0 [选项] [--verbose]"
                echo ""
                echo "默认行为:"
                echo "  无参数          显示交互式菜单"
                echo ""
                echo "快捷选项:"
                echo "  quick, q, Q     极简模式+自动网络"
                echo "  full, f, F      完整模式+自动网络"
                echo "  debug, d, D     调试模式 (极简+自动+详细日志)"
                echo ""
                echo "详细选项:"
                echo "  minimal-auto    极简+自动"
                echo "  minimal-direct  极简+直连"
                echo "  minimal-proxy   极简+代理 (推荐)"
                echo "  full-auto       完整+自动"
                echo "  full-direct     完整+直连"
                echo "  full-proxy      完整+代理"
                echo ""
                echo "日志选项:"
                echo "  --verbose, -v   启用详细日志 (打印完整 JSON)"
                echo "                  可与任何模式组合使用"
                echo ""
                echo "其他:"
                echo "  --menu, -m      显示交互式菜单"
                echo "  --help, -h      显示帮助信息"
                echo ""
                echo "示例:"
                echo "  $0                    # 显示交互式菜单（默认）"
                echo "  $0 quick              # 快速启动：极简+自动网络"
                echo "  $0 full               # 完整订阅+自动网络"
                echo "  $0 debug              # 调试模式（详细日志）"
                echo "  $0 quick --verbose    # 极简模式+详细日志"
                echo "  $0 minimal-proxy      # 极简+代理（推荐国内用户）"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 未知选项: $1${NC}"
                echo "使用 $0 --help 查看帮助"
                exit 1
                ;;
        esac
    else
        # 无参数时，显示交互式菜单（默认行为）
        # 不需要 exit，直接进入下方的交互式菜单循环
        :
    fi

    # 交互式菜单
    while true; do
        show_menu
        read -p "请输入选项: " choice

        case $choice in
            1)
                echo ""
                echo -e "${CYAN}选择网络模式:${NC}"
                echo -e "  ${YELLOW}A.${NC} 自动检测 (推荐)"
                echo -e "  ${YELLOW}B.${NC} 强制直连"
                echo -e "  ${YELLOW}C.${NC} 强制代理"
                read -p "请选择 [A/B/C]: " network
                case ${network,,} in
                    a|"") start_client "minimal" "auto" 0 ;;
                    b) start_client "minimal" "direct" 0 ;;
                    c) start_client "minimal" "proxy" 0 ;;
                    *) echo -e "${RED}❌ 无效选择${NC}" ;;
                esac
                echo ""
                read -p "按回车继续..." dummy
                ;;
            2)
                echo ""
                echo -e "${CYAN}选择网络模式:${NC}"
                echo -e "  ${YELLOW}A.${NC} 自动检测 (推荐)"
                echo -e "  ${YELLOW}B.${NC} 强制直连"
                echo -e "  ${YELLOW}C.${NC} 强制代理"
                read -p "请选择 [A/B/C]: " network
                case ${network,,} in
                    a|"") start_client "full" "auto" 0 ;;
                    b) start_client "full" "direct" 0 ;;
                    c) start_client "full" "proxy" 0 ;;
                    *) echo -e "${RED}❌ 无效选择${NC}" ;;
                esac
                echo ""
                read -p "按回车继续..." dummy
                ;;
            [aA])
                echo ""
                echo -e "${CYAN}选择客户端类型:${NC}"
                echo -e "  ${YELLOW}1.${NC} 极简模式"
                echo -e "  ${YELLOW}2.${NC} 完整订阅模式"
                read -p "请选择 [1/2]: " client
                case $client in
                    1) start_client "minimal" "auto" 0 ;;
                    2) start_client "full" "auto" 0 ;;
                    *) echo -e "${RED}❌ 无效选择${NC}" ;;
                esac
                echo ""
                read -p "按回车继续..." dummy
                ;;
            [bB])
                echo ""
                echo -e "${CYAN}选择客户端类型:${NC}"
                echo -e "  ${YELLOW}1.${NC} 极简模式"
                echo -e "  ${YELLOW}2.${NC} 完整订阅模式"
                read -p "请选择 [1/2]: " client
                case $client in
                    1) start_client "minimal" "direct" 0 ;;
                    2) start_client "full" "direct" 0 ;;
                    *) echo -e "${RED}❌ 无效选择${NC}" ;;
                esac
                echo ""
                read -p "按回车继续..." dummy
                ;;
            [cC])
                echo ""
                echo -e "${CYAN}选择客户端类型:${NC}"
                echo -e "  ${YELLOW}1.${NC} 极简模式"
                echo -e "  ${YELLOW}2.${NC} 完整订阅模式"
                read -p "请选择 [1/2]: " client
                case $client in
                    1) start_client "minimal" "proxy" 0 ;;
                    2) start_client "full" "proxy" 0 ;;
                    *) echo -e "${RED}❌ 无效选择${NC}" ;;
                esac
                echo ""
                read -p "按回车继续..." dummy
                ;;
            [qQ])
                start_client "minimal" "auto" 0
                echo ""
                read -p "按回车继续..." dummy
                ;;
            [fF])
                start_client "full" "auto" 0
                echo ""
                read -p "按回车继续..." dummy
                ;;
            [dD])
                start_client "minimal" "auto" 1
                echo ""
                read -p "按回车继续..." dummy
                ;;
            [vV])
                echo ""
                echo -e "${CYAN}选择客户端类型:${NC}"
                echo -e "  ${YELLOW}1.${NC} 极简模式 + 详细日志"
                echo -e "  ${YELLOW}2.${NC} 完整订阅模式 + 详细日志"
                read -p "请选择 [1/2]: " client
                echo ""
                echo -e "${CYAN}选择网络模式:${NC}"
                echo -e "  ${YELLOW}A.${NC} 自动检测 (推荐)"
                echo -e "  ${YELLOW}B.${NC} 强制直连"
                echo -e "  ${YELLOW}C.${NC} 强制代理"
                read -p "请选择 [A/B/C]: " network

                local client_type=""
                case $client in
                    1) client_type="minimal" ;;
                    2) client_type="full" ;;
                    *)
                        echo -e "${RED}❌ 无效选择${NC}"
                        sleep 1
                        continue
                        ;;
                esac

                case ${network,,} in
                    a|"") start_client "$client_type" "auto" 1 ;;
                    b) start_client "$client_type" "direct" 1 ;;
                    c) start_client "$client_type" "proxy" 1 ;;
                    *) echo -e "${RED}❌ 无效选择${NC}" ;;
                esac
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
