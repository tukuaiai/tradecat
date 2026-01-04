#!/usr/bin/env node
/**
 * 信号统计脚本 - 从日志中提取信号频率统计
 * 用于生成每日摘要
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const LOG_PATH = process.env.LOG_PATH || path.join(__dirname, '../logs/pm2-out.log');

// 信号模式匹配
const PATTERNS = {
    arbitrage: /🎉 发现套利/,
    orderbook: /🎉 发现订单簿/,
    smartMoneyOpen: /聪明钱建仓/,
    smartMoneyAdd: /聪明钱加仓/,
    smartMoneyClose: /聪明钱清仓/,
    largeTrade: /大额交易/,
    newMarket: /新市场/,
    closingScan: /扫尾盘扫描/,
    signalSent: /发送信号:/
};

// 日期提取
const DATE_PATTERN = /^(\d{4}-\d{2}-\d{2})T(\d{2}):/;

async function parseLog(logPath, targetDate) {
    const stats = {
        date: targetDate,
        byType: {},
        byHour: {},
        total: { detected: 0, sent: 0 }
    };

    // 初始化
    Object.keys(PATTERNS).forEach(k => {
        stats.byType[k] = 0;
        stats.byHour[k] = {};
        for (let h = 0; h < 24; h++) {
            stats.byHour[k][h] = 0;
        }
    });

    const fileStream = fs.createReadStream(logPath);
    const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

    for await (const line of rl) {
        const dateMatch = line.match(DATE_PATTERN);
        if (!dateMatch) continue;

        const [, date, hour] = dateMatch;
        if (targetDate && date !== targetDate) continue;

        const h = parseInt(hour, 10);

        for (const [type, pattern] of Object.entries(PATTERNS)) {
            if (pattern.test(line)) {
                stats.byType[type]++;
                stats.byHour[type][h]++;

                if (type === 'signalSent') {
                    stats.total.sent++;
                } else if (type !== 'closingScan') {
                    stats.total.detected++;
                }
            }
        }
    }

    return stats;
}

function formatStats(stats) {
    const lines = [];
    lines.push(`📊 Polymarket 信号统计 (${stats.date || '全部'})`);
    lines.push('');
    lines.push('=== 信号检测统计 ===');
    lines.push(`套利机会: ${stats.byType.arbitrage}`);
    lines.push(`订单簿失衡: ${stats.byType.orderbook}`);
    lines.push(`聪明钱建仓: ${stats.byType.smartMoneyOpen}`);
    lines.push(`聪明钱加仓: ${stats.byType.smartMoneyAdd}`);
    lines.push(`聪明钱清仓: ${stats.byType.smartMoneyClose}`);
    lines.push(`大额交易: ${stats.byType.largeTrade}`);
    lines.push(`新市场: ${stats.byType.newMarket}`);
    lines.push('');
    lines.push('=== 发送统计 ===');
    lines.push(`检测总数: ${stats.total.detected}`);
    lines.push(`实际发送: ${stats.total.sent}`);
    lines.push(`发送率: ${(stats.total.sent / stats.total.detected * 100).toFixed(1)}%`);
    lines.push('');
    lines.push('=== 套利按小时分布 ===');
    for (let h = 0; h < 24; h++) {
        const count = stats.byHour.arbitrage[h];
        if (count > 0) {
            const bar = '█'.repeat(Math.min(count / 5, 20));
            lines.push(`${String(h).padStart(2, '0')}:00 ${bar} ${count}`);
        }
    }
    return lines.join('\n');
}

async function main() {
    const targetDate = process.argv[2] || new Date().toISOString().slice(0, 10);
    
    console.log(`正在分析日志: ${LOG_PATH}`);
    console.log(`目标日期: ${targetDate}`);
    console.log('');

    try {
        const stats = await parseLog(LOG_PATH, targetDate);
        console.log(formatStats(stats));

        // 输出 JSON 格式（可选）
        if (process.argv.includes('--json')) {
            console.log('\n=== JSON ===');
            console.log(JSON.stringify(stats, null, 2));
        }
    } catch (err) {
        console.error('错误:', err.message);
        process.exit(1);
    }
}

main();
