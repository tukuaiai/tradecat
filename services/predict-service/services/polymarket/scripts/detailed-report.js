#!/usr/bin/env node
/**
 * 详细报告生成器 - 使用 Gamma API 获取正确的市场链接
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const LOG_PATH = process.env.LOG_PATH || path.join(__dirname, '../logs/pm2-out.log');
const GAMMA_API = 'https://gamma-api.polymarket.com';

// 获取市场 slug 映射
async function fetchMarketSlugs() {
    const fetch = (await import('node-fetch')).default;
    const slugMap = new Map();
    
    // 分页获取所有活跃市场
    let offset = 0;
    const limit = 500;
    
    while (true) {
        try {
            const res = await fetch(`${GAMMA_API}/markets?active=true&limit=${limit}&offset=${offset}`);
            if (!res.ok) break;
            const markets = await res.json();
            if (!markets.length) break;
            
            for (const m of markets) {
                slugMap.set(m.question.trim(), m.slug);
            }
            
            if (markets.length < limit) break;
            offset += limit;
        } catch (e) {
            console.error('获取市场数据失败:', e.message);
            break;
        }
    }
    
    console.log(`✅ 获取到 ${slugMap.size} 个市场的 slug 映射`);
    return slugMap;
}

// 解析日志统计
async function parseLogStats(logPath, targetDate) {
    const stats = {
        arbitrage: new Map(),
        largeTrade: new Map(),
        orderbook: new Map(),
        smartMoney: new Map(),
        addresses: new Map()
    };

    const rl = readline.createInterface({
        input: fs.createReadStream(logPath),
        crlfDelay: Infinity
    });

    for await (const line of rl) {
        if (targetDate && !line.includes(targetDate)) continue;

        // 套利信号
        const arbMatch = line.match(/🎉 发现套利.*市场: (.*), 净利润: ([0-9.]+)%, 深度: YES=\$([0-9KM]+) NO=\$([0-9KM]+)/);
        if (arbMatch) {
            const [, market, profit, yes, no] = arbMatch;
            if (!stats.arbitrage.has(market)) {
                stats.arbitrage.set(market, { count: 0, maxProfit: 0, yesDepth: '', noDepth: '' });
            }
            const d = stats.arbitrage.get(market);
            d.count++;
            if (parseFloat(profit) > d.maxProfit) {
                d.maxProfit = parseFloat(profit);
                d.yesDepth = yes;
                d.noDepth = no;
            }
        }

        // 大额交易 (🏷️ 标记)
        const tradeMatch = line.match(/🏷️ (.+)/);
        if (tradeMatch) {
            const market = tradeMatch[1].trim();
            stats.largeTrade.set(market, (stats.largeTrade.get(market) || 0) + 1);
        }

        // 订单簿 (从套利缓存获取市场名称)
        const bookMatch = line.match(/从套利缓存获取市场名称: (.+)/);
        if (bookMatch) {
            const market = bookMatch[1].trim();
            stats.orderbook.set(market, (stats.orderbook.get(market) || 0) + 1);
        }

        // 地址统计
        const addrMatch = line.match(/👤 地址 (0x[a-f0-9]+\.\.\.[a-f0-9]+)/);
        if (addrMatch) {
            const addr = addrMatch[1];
            stats.addresses.set(addr, (stats.addresses.get(addr) || 0) + 1);
        }
    }

    return stats;
}

// 生成报告
function generateReport(stats, slugMap, targetDate) {
    const lines = [];
    
    const makeLink = (market) => {
        const slug = slugMap.get(market);
        return slug ? `https://polymarket.com/event/${slug}` : null;
    };

    lines.push(`
╔══════════════════════════════════════════════════════════════════════════════╗
║           📊 Polymarket 详细市场报告 (${targetDate})                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
`);

    // 套利 Top 15
    lines.push(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 套利信号 Top 15 (共${stats.arbitrage.size}个市场)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);

    const topArb = [...stats.arbitrage.entries()]
        .sort((a, b) => b[1].count - a[1].count)
        .slice(0, 15);

    topArb.forEach(([market, data], i) => {
        const link = makeLink(market);
        lines.push(`
${String(i + 1).padStart(2)}. ${market}
    📊 出现: ${data.count}次 | 最高利润: ${data.maxProfit.toFixed(2)}%
    💰 深度: YES=$${data.yesDepth} | NO=$${data.noDepth}
    🔗 ${link || '(未找到链接)'}`);
    });

    // 大额交易 Top 15
    lines.push(`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💸 大额交易 Top 15 (共${stats.largeTrade.size}个市场)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);

    const topTrade = [...stats.largeTrade.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 15);

    topTrade.forEach(([market, count], i) => {
        const link = makeLink(market);
        lines.push(`
${String(i + 1).padStart(2)}. ${market}
    📊 交易: ${count}次
    🔗 ${link || '(未找到链接)'}`);
    });

    // 订单簿 Top 15
    lines.push(`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 订单簿失衡 Top 15 (共${stats.orderbook.size}个市场)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);

    const topBook = [...stats.orderbook.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 15);

    topBook.forEach(([market, count], i) => {
        const link = makeLink(market);
        lines.push(`
${String(i + 1).padStart(2)}. ${market}
    📊 失衡: ${count}次
    🔗 ${link || '(未找到链接)'}`);
    });

    // 地址 Top 15
    lines.push(`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 高活跃地址 Top 15
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);

    const topAddr = [...stats.addresses.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 15);

    topAddr.forEach(([addr, count], i) => {
        lines.push(`
${String(i + 1).padStart(2)}. ${addr}
    📊 操作: ${count}次
    🔗 https://polymarket.com/profile/${addr.split('...')[0]}`);
    });

    return lines.join('\n');
}

// 主函数
async function main() {
    const targetDate = process.argv[2] || new Date().toISOString().slice(0, 10);
    
    console.log(`📊 生成详细报告: ${targetDate}`);
    console.log(`📂 日志: ${LOG_PATH}`);
    console.log('');

    // 1. 获取市场 slug 映射
    const slugMap = await fetchMarketSlugs();

    // 2. 解析日志
    const stats = await parseLogStats(LOG_PATH, targetDate);

    // 3. 生成报告
    const report = generateReport(stats, slugMap, targetDate);
    console.log(report);

    // 4. 保存
    const outPath = path.join(__dirname, `../data/detailed-report-${targetDate}.txt`);
    fs.writeFileSync(outPath, report);
    console.log(`\n✅ 已保存: ${outPath}`);
}

main().catch(console.error);
