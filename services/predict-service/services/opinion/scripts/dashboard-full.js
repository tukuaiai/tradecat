#!/usr/bin/env node

/**
 * Polymarket 实时数据 - 完整仪表板
 * 使用 blessed 创建实时更新的终端界面
 */

const { RealTimeDataClient } = require("./dist/client");
const blessed = require("blessed");
const contrib = require("blessed-contrib");

// 创建屏幕
const screen = blessed.screen({
    smartCSR: true,
    title: "Polymarket 实时数据看板",
});

// 创建网格布局
const grid = new contrib.grid({
    rows: 12,
    cols: 12,
    screen: screen,
});

// ========== 组件定义 ==========

// 1. 状态栏（顶部）
const statusBar = grid.set(0, 0, 1, 12, blessed.box, {
    content: " 🚀 Polymarket 实时数据看板 | 正在连接...",
    style: {
        fg: "white",
        bg: "blue",
        bold: true,
    },
});

// 2. 统计面板（左上）
const statsBox = grid.set(1, 0, 2, 3, contrib.lcd, {
    label: "📊 消息统计",
    segmentWidth: 0.06,
    segmentInterval: 0.11,
    strokeWidth: 0.1,
    elements: 3,
    display: 0,
    elementSpacing: 4,
    elementPadding: 2,
    color: "green",
    style: {
        border: { fg: "cyan" },
    },
});

// 3. 价格表（右上）
const priceTable = grid.set(1, 3, 2, 4, contrib.table, {
    keys: true,
    vi: true,
    label: "📈 加密货币价格",
    columnWidth: [12, 15, 15],
    style: {
        border: { fg: "cyan" },
        header: { fg: "yellow", bold: true },
        cell: { fg: "white" },
    },
});

// 4. 实时交易列表（左中）
const tradeLog = grid.set(3, 0, 6, 7, contrib.log, {
    label: "💰 最新交易",
    bufferLength: 100,
    style: {
        fg: "white",
        border: { fg: "cyan" },
    },
});

// 5. 评论列表（右中）
const commentLog = grid.set(3, 7, 6, 5, contrib.log, {
    label: "💬 评论动态",
    bufferLength: 100,
    style: {
        fg: "white",
        border: { fg: "cyan" },
    },
});

// 6. 市场活动（底部左）
const marketLog = grid.set(9, 0, 3, 7, contrib.log, {
    label: "📊 市场活动",
    bufferLength: 50,
    style: {
        fg: "white",
        border: { fg: "cyan" },
    },
});

// 7. 帮助信息（底部右）
const helpBox = grid.set(9, 7, 3, 5, blessed.box, {
    label: "💡 帮助",
    content:
`  快捷键：
  ↑/↓   - 滚动日志
  PgUp/PgDn - 翻页
  q     - 退出
  c     - 清空日志

  状态：
  ⚡ 实时数据流
  🔄 自动重连

  数据源：
  • 交易活动
  • 评论反应
  • 加密货币价格
  • 市场数据`,
    style: {
        border: { fg: "cyan" },
        fg: "gray",
    },
});

// 8. 系统日志（右上角小窗口）
const systemLog = grid.set(1, 7, 2, 5, contrib.log, {
    label: "🔔 系统消息",
    bufferLength: 20,
    style: {
        fg: "yellow",
        border: { fg: "cyan" },
    },
});

// ========== 数据统计 ==========

const stats = {
    trades: 0,
    comments: 0,
    prices: 0,
    markets: 0,
    startTime: Date.now(),
};

const prices = {
    "BTC/USDT": { price: "--", change: 0, time: "" },
    "ETH/USDT": { price: "--", change: 0, time: "" },
};

// 更新统计显示
function updateStats() {
    const total = stats.trades + stats.comments + stats.prices + stats.markets;
    statsBox.setDisplay(total.toString());

    const runtime = Math.floor((Date.now() - stats.startTime) / 1000);
    const rate = runtime > 0 ? (total / runtime * 60).toFixed(1) : 0;

    statusBar.setContent(
        ` 🚀 Polymarket 实时数据看板 | ` +
        `总消息: ${total} | ` +
        `交易: ${stats.trades} | ` +
        `评论: ${stats.comments} | ` +
        `价格: ${stats.prices} | ` +
        `市场: ${stats.markets} | ` +
        `速率: ${rate}/分钟 | ` +
        `运行: ${runtime}秒`
    );
    screen.render();
}

// 更新价格表
function updatePriceTable() {
    const data = [
        ["币种", "价格", "变化"],
    ];

    Object.entries(prices).forEach(([symbol, info]) => {
        const changeStr = info.change > 0
            ? `+${info.change.toFixed(2)}%`
            : info.change < 0
            ? `${info.change.toFixed(2)}%`
            : "0.00%";

        data.push([symbol, `$${info.price}`, changeStr]);
    });

    priceTable.setData({
        headers: ["币种", "价格", "变化"],
        data: data.slice(1),
    });
    screen.render();
}

// ========== 消息处理 ==========

const onMessage = (_, message) => {
    const { topic, type, payload } = message;

    try {
        if (topic === "activity" && type === "trades") {
            const time = new Date(payload.timestamp * 1000).toLocaleTimeString();
            const side = payload.side === "BUY" ? "📈" : "📉";
            const sideColor = payload.side === "BUY" ? "{green-fg}" : "{red-fg}";

            tradeLog.log(
                `${time} ${sideColor}${side} ${payload.side}{/} ` +
                `{yellow-fg}$${payload.price}{/} x ${payload.size} ` +
                `{cyan-fg}${payload.slug}{/}`
            );
            stats.trades++;

        } else if (topic === "comments" && type === "comment_created") {
            const time = new Date(payload.createdAt).toLocaleTimeString();
            const user = payload.userAddress.substring(0, 8) + "...";
            const content = payload.body.substring(0, 50);

            commentLog.log(
                `${time} {magenta-fg}${user}{/}: ${content}${payload.body.length > 50 ? "..." : ""}`
            );
            stats.comments++;

        } else if (topic === "comments" && type === "reaction_created") {
            const time = new Date(payload.createdAt).toLocaleTimeString();
            commentLog.log(`${time} ${payload.icon} {yellow-fg}新反应{/}`);
            stats.comments++;

        } else if (topic === "crypto_prices" && type === "update") {
            const symbol = payload.symbol.toUpperCase().replace("USDT", "/USDT");
            const price = parseFloat(payload.value).toFixed(2);
            const oldPrice = parseFloat(prices[symbol]?.price) || price;
            const change = ((price - oldPrice) / oldPrice * 100).toFixed(2);

            prices[symbol] = {
                price: price,
                change: parseFloat(change),
                time: new Date(payload.timestamp).toLocaleTimeString(),
            };

            updatePriceTable();
            stats.prices++;

        } else if (topic === "clob_market") {
            const time = new Date().toLocaleTimeString();
            let msg = `${time} {cyan-fg}[${type}]{/} `;

            if (type === "market_created") {
                msg += `{green-fg}🎉 新市场{/} ${payload.market?.substring(0, 10)}...`;
            } else if (type === "market_resolved") {
                msg += `{yellow-fg}✅ 市场结算{/} ${payload.market?.substring(0, 10)}...`;
            } else if (type === "price_change") {
                msg += `💹 价格变化`;
            } else if (type === "last_trade_price") {
                const side = payload.side === "BUY" ? "📈" : "📉";
                msg += `${side} ${payload.side} $${payload.price}`;
            }

            marketLog.log(msg);
            stats.markets++;
        }

        updateStats();

    } catch (error) {
        systemLog.log(`{red-fg}错误: ${error.message}{/}`);
    }
};

const onConnect = (client) => {
    systemLog.log("{green-fg}✅ 连接成功！{/}");

    // 订阅数据
    client.subscribe({ subscriptions: [{ topic: "comments", type: "*" }] });
    systemLog.log("📡 已订阅: 评论");

    client.subscribe({ subscriptions: [{ topic: "activity", type: "*" }] });
    systemLog.log("📡 已订阅: 交易");

    client.subscribe({
        subscriptions: [{
            topic: "crypto_prices",
            type: "*",
            filters: '{"symbol":"btcusdt"}',
        }],
    });
    systemLog.log("📡 已订阅: BTC");

    client.subscribe({
        subscriptions: [{
            topic: "crypto_prices",
            type: "*",
            filters: '{"symbol":"ethusdt"}',
        }],
    });
    systemLog.log("📡 已订阅: ETH");

    client.subscribe({ subscriptions: [{ topic: "clob_market", type: "*" }] });
    systemLog.log("📡 已订阅: 市场");

    systemLog.log("{yellow-fg}⏳ 等待实时数据...{/}");
    updateStats();
};

const onError = (error) => {
    systemLog.log(`{red-fg}❌ 错误: ${error.message}{/}`);
};

const onDisconnect = () => {
    systemLog.log("{yellow-fg}🔌 连接断开{/}");
};

// ========== 键盘事件 ==========

screen.key(["q", "C-c"], () => {
    return process.exit(0);
});

screen.key(["c"], () => {
    tradeLog.logLines = [];
    commentLog.logLines = [];
    marketLog.logLines = [];
    systemLog.log("{yellow-fg}🗑️  日志已清空{/}");
    screen.render();
});

// 聚焦到日志以便滚动
tradeLog.focus();

// ========== 启动客户端 ==========

screen.render();

new RealTimeDataClient({
    onConnect,
    onMessage,
    onError,
    onDisconnect,
    autoReconnect: true,
}).connect();
