#!/usr/bin/env node
/**
 * CSV 报告生成器 - 带真实市场链接
 * 包含：Top 15 市场 + 活跃时段 + 买卖比例 + 市场类别
 */

const fs = require('fs');
const readline = require('readline');

const GAMMA_API = 'https://gamma-api.polymarket.com';
const LOG_FILE = process.argv[2] || '/root/.pm2/logs/polymarket-bot-out.log';

// 滚动24小时：计算24小时前的时间戳
const now = new Date();
const hours24Ago = new Date(now.getTime() - 24 * 60 * 60 * 1000);

function isWithin24Hours(line) {
  // 提取时间戳 2025-12-30T00:01:08
  const match = line.match(/^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})/);
  if (!match) return false;
  const lineTime = new Date(match[1] + 'Z'); // 假设 UTC
  return lineTime >= hours24Ago && lineTime <= now;
}

const marketSlugs = new Map();

// 市场类别关键词
const CATEGORY_KEYWORDS = {
  sports: ['FC', 'vs.', 'NBA', 'NFL', 'NHL', 'MLB', 'UFC', 'win on', 'Super Bowl', 'World Cup', 'Finals', 'Lakers', 'Celtics', 'Arsenal', 'Liverpool', 'Manchester', 'Chelsea', 'Pistons', 'Mavericks', 'Warriors', 'Rams', 'Falcons', 'Bulls', 'Heat', 'Knicks', 'Spread:', 'O/U', 'Grizzlies', 'Nuggets', 'Pacers'],
  crypto: ['Bitcoin', 'Ethereum', 'BTC', 'ETH', 'Solana', 'XRP', 'crypto', 'token', 'airdrop', 'FDV', 'market cap', 'Lighter', 'Satoshi', 'dip to'],
  politics: ['Trump', 'Biden', 'election', 'President', 'Congress', 'Senate', 'Governor', 'Maduro', 'Newsom', 'Republican', 'Democrat', 'nomination'],
  entertainment: ['movie', 'film', 'Oscar', 'Grammy', 'Netflix', 'Disney', 'Stranger Things', 'Avatar', 'tweets', 'Elon Musk'],
  finance: ['Fed', 'interest rate', 'S&P', 'Nasdaq', 'Gold', 'Silver', 'stock', 'TSLA', 'AAPL', 'GOOGL', 'MSFT', 'close between']
};

function categorizeMarket(name) {
  const lower = name.toLowerCase();
  for (const [cat, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    if (keywords.some(k => lower.includes(k.toLowerCase()))) return cat;
  }
  return 'other';
}

async function buildMarketMap() {
  console.error('📥 获取市场数据...');
  
  // 获取活跃市场和已关闭市场
  for (const closed of [false, true]) {
    let offset = 0;
    const limit = 500;
    const label = closed ? '已关闭' : '活跃';
    
    while (true) {
      try {
        const url = `${GAMMA_API}/markets?closed=${closed}&limit=${limit}&offset=${offset}`;
        const res = await fetch(url);
        const data = await res.json();
        if (!data || data.length === 0) break;
        
        for (const m of data) {
          if (m.question) {
            // 优先使用 event slug，回退到 market slug
            const slug = m.events?.[0]?.slug || m.slug;
            if (slug) {
              marketSlugs.set(m.question, slug);
              marketSlugs.set(m.question.toLowerCase(), slug);
              const simplified = m.question.replace(/\d{4}-\d{2}-\d{2}/g, '').trim();
              if (simplified !== m.question) {
                marketSlugs.set(simplified, slug);
              }
            }
          }
        }
        
        if (!closed) {
          console.error(`  已加载 ${Math.floor(marketSlugs.size / 2)} 个${label}市场...`);
        }
        if (data.length < limit) break;
        offset += limit;
        
        // 已关闭市场只取前5000个（最近的）
        if (closed && offset >= 5000) break;
      } catch (e) {
        console.error(`  API 错误 (${label}):`, e.message);
        break;
      }
    }
  }
  
  console.error(`✅ 共加载 ${Math.floor(marketSlugs.size / 2)} 个市场\n`);
}

function findSlug(marketName) {
  if (!marketName) return null;
  
  // 精确匹配
  if (marketSlugs.has(marketName)) return marketSlugs.get(marketName);
  
  const lower = marketName.toLowerCase();
  if (marketSlugs.has(lower)) return marketSlugs.get(lower);
  
  // 去掉问号和空格
  const normalized = marketName.replace(/\?$/, '').trim();
  if (marketSlugs.has(normalized)) return marketSlugs.get(normalized);
  if (marketSlugs.has(normalized.toLowerCase())) return marketSlugs.get(normalized.toLowerCase());
  
  // 模糊匹配：遍历所有市场找最佳匹配
  let bestMatch = null;
  let bestScore = 0;
  
  for (const [question, slug] of marketSlugs) {
    if (typeof question !== 'string') continue;
    
    const qLower = question.toLowerCase();
    
    // 完全包含
    if (qLower.includes(lower) || lower.includes(qLower)) {
      const score = Math.min(question.length, marketName.length) / Math.max(question.length, marketName.length);
      if (score > bestScore) {
        bestScore = score;
        bestMatch = slug;
      }
    }
    
    // 关键词匹配
    const keywords = lower.split(/\s+/).filter(w => w.length > 3);
    const matchCount = keywords.filter(k => qLower.includes(k)).length;
    if (matchCount >= 3 && matchCount / keywords.length > bestScore) {
      bestScore = matchCount / keywords.length;
      bestMatch = slug;
    }
  }
  
  return bestScore > 0.5 ? bestMatch : null;
}

async function extractData() {
  const arbCounts = new Map(), arbProfits = new Map();
  const largeTradeCounts = new Map(), orderbookCounts = new Map(), smartMoneyCounts = new Map();
  const newMarketCounts = new Map();
  
  // 统计
  const hourlySignals = new Array(24).fill(0);
  const hourlyByType = { arb: new Array(24).fill(0), large: new Array(24).fill(0), orderbook: new Array(24).fill(0), smart: new Array(24).fill(0) };
  const buySellStats = { buy: 0, sell: 0 };
  const smartMoneyOps = { open: 0, add: 0, close: 0 };
  const profitRanges = { '0-2%': 0, '2-5%': 0, '5-10%': 0, '10%+': 0 };
  const categoryStats = { sports: 0, crypto: 0, politics: 0, entertainment: 0, finance: 0, other: 0 };
  
  // 新增统计
  const smartMoneyByCategory = { sports: 0, crypto: 0, politics: 0, entertainment: 0, finance: 0, other: 0 };
  const signalBursts = [];
  const marketSignalTypes = new Map();
  let lastBurstCheck = null;
  let burstCount = 0;
  
  let lastMarketName = null;
  let lastMarketTime = null;
  
  const rl = readline.createInterface({
    input: fs.createReadStream(LOG_FILE),
    crlfDelay: Infinity
  });
  
  for await (const line of rl) {
    if (!isWithin24Hours(line)) continue;
    
    // 提取时间戳用于爆发检测
    const tsMatch = line.match(/^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})/);
    if (tsMatch && line.includes('⏱️')) {
      const ts = tsMatch[1];
      if (lastBurstCheck === ts.slice(0, 15)) {
        burstCount++;
      } else {
        if (burstCount >= 20) {
          signalBursts.push({ time: lastBurstCheck, count: burstCount });
        }
        lastBurstCheck = ts.slice(0, 15);
        burstCount = 1;
      }
    }
    
    // 提取小时
    const hourMatch = line.match(/T(\d{2}):/);
    const hour = hourMatch ? parseInt(hourMatch[1]) : -1;
    
    if (hour >= 0 && line.includes('⏱️')) {
      hourlySignals[hour]++;
    }
    
    // 聪明钱操作类型统计
    if (line.includes('聪明钱')) {
      if (line.includes('建仓')) { smartMoneyOps.open++; buySellStats.buy++; }
      else if (line.includes('加仓')) { smartMoneyOps.add++; buySellStats.buy++; }
      else if (line.includes('清仓')) { smartMoneyOps.close++; buySellStats.sell++; }
      
      if (hour >= 0) hourlyByType.smart[hour]++;
    }
    
    // 套利
    const arbMatch = line.match(/🎉 发现套利.*?市场:\s*(.+?),\s*净利润:\s*([\d.]+)%/);
    if (arbMatch) {
      const name = arbMatch[1].trim();
      const profit = parseFloat(arbMatch[2]);
      arbCounts.set(name, (arbCounts.get(name) || 0) + 1);
      arbProfits.set(name, Math.max(arbProfits.get(name) || 0, profit));
      
      const cat = categorizeMarket(name);
      categoryStats[cat]++;
      
      if (!marketSignalTypes.has(name)) marketSignalTypes.set(name, new Set());
      marketSignalTypes.get(name).add('arb');
      
      if (profit < 2) profitRanges['0-2%']++;
      else if (profit < 5) profitRanges['2-5%']++;
      else if (profit < 10) profitRanges['5-10%']++;
      else profitRanges['10%+']++;
      
      if (hour >= 0) hourlyByType.arb[hour]++;
      continue;
    }
    
    // 新市场
    if (line.includes('🆕 新市场')) {
      if (hour >= 0) hourlySignals[hour]++;
    }
    
    // 🏷️ 标签行
    const tagMatch = line.match(/(\d{2}:\d{2}:\d{2}).*?🏷️\s*(.+)$/);
    if (tagMatch) {
      lastMarketTime = tagMatch[1];
      lastMarketName = tagMatch[2].trim();
      categoryStats[categorizeMarket(lastMarketName)]++;
      continue;
    }
    
    // MessageUpdater
    const msgMatch = line.match(/(\d{2}:\d{2}:\d{2}).*?\[MessageUpdater\].*?\((\w+)\)/);
    if (msgMatch && lastMarketName) {
      const [, time, type] = msgMatch;
      if (timeDiff(time, lastMarketTime) <= 2) {
        const name = lastMarketName;
        
        if (!marketSignalTypes.has(name)) marketSignalTypes.set(name, new Set());
        
        if (type === 'largeTrade') {
          largeTradeCounts.set(name, (largeTradeCounts.get(name) || 0) + 1);
          marketSignalTypes.get(name).add('large');
          if (hour >= 0) hourlyByType.large[hour]++;
        }
        else if (type === 'orderbook') {
          orderbookCounts.set(name, (orderbookCounts.get(name) || 0) + 1);
          marketSignalTypes.get(name).add('orderbook');
          if (hour >= 0) hourlyByType.orderbook[hour]++;
        }
        else if (type === 'smartMoney') {
          smartMoneyCounts.set(name, (smartMoneyCounts.get(name) || 0) + 1);
          marketSignalTypes.get(name).add('smart');
          smartMoneyByCategory[categorizeMarket(name)]++;
        }
        else if (type === 'newMarket') {
          newMarketCounts.set(name, (newMarketCounts.get(name) || 0) + 1);
        }
      }
    }
  }
  
  if (burstCount >= 20) {
    signalBursts.push({ time: lastBurstCheck, count: burstCount });
  }
  
  return { 
    arbCounts, arbProfits, largeTradeCounts, orderbookCounts, smartMoneyCounts, newMarketCounts,
    hourlySignals, hourlyByType, buySellStats, smartMoneyOps, profitRanges, categoryStats,
    smartMoneyByCategory, signalBursts, marketSignalTypes
  };
}

function timeDiff(t1, t2) {
  const toSec = t => { const [h, m, s] = t.split(':').map(Number); return h * 3600 + m * 60 + s; };
  return Math.abs(toSec(t1) - toSec(t2));
}

async function main() {
  const timeRange = `${hours24Ago.toISOString().slice(0, 16)} ~ ${now.toISOString().slice(0, 16)} UTC`;
  console.error(`📊 生成 CSV 报告 (滚动24小时: ${timeRange})...\n`);
  
  await buildMarketMap();
  const data = await extractData();
  
  const sortTop = (m, n = 15) => [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, n);
  const link = n => {
    const s = findSlug(n);
    return s ? `https://polymarket.com/event/${s}` : '';
  };
  
  const arbTop = sortTop(data.arbCounts);
  const largeTop = sortTop(data.largeTradeCounts);
  const obTop = sortTop(data.orderbookCounts);
  const smartTop = sortTop(data.smartMoneyCounts);
  const newMarketTop = sortTop(data.newMarketCounts);
  
  // 综合热门市场
  const combined = new Map();
  [data.arbCounts, data.largeTradeCounts, data.orderbookCounts, data.smartMoneyCounts].forEach(m => {
    for (const [k, v] of m) combined.set(k, (combined.get(k) || 0) + v);
  });
  const combinedTop = sortTop(combined);
  
  let csv = '';
  
  // 1. 套利信号
  csv += '# 套利信号 Top 15\n排名,市场名称,出现次数,最高利润%,链接\n';
  arbTop.forEach(([n, c], i) => csv += `${i+1},"${n}",${c},${data.arbProfits.get(n)||''},${link(n)}\n`);
  
  // 2. 大额交易
  csv += '\n# 大额交易 Top 15\n排名,市场名称,交易次数,链接\n';
  largeTop.forEach(([n, c], i) => csv += `${i+1},"${n}",${c},${link(n)}\n`);
  
  // 3. 订单簿失衡
  csv += '\n# 订单簿失衡 Top 15\n排名,市场名称,失衡次数,链接\n';
  obTop.forEach(([n, c], i) => csv += `${i+1},"${n}",${c},${link(n)}\n`);
  
  // 4. 聪明钱
  csv += '\n# 聪明钱 Top 15\n排名,市场名称,信号次数,链接\n';
  smartTop.forEach(([n, c], i) => csv += `${i+1},"${n}",${c},${link(n)}\n`);
  
  // 5. 新市场 Top 15
  csv += '\n# 新市场 Top 15\n排名,市场名称,出现次数,链接\n';
  newMarketTop.forEach(([n, c], i) => csv += `${i+1},"${n}",${c},${link(n)}\n`);
  
  // 6. 综合热门市场 Top 15
  csv += '\n# 综合热门市场 Top 15\n排名,市场名称,套利,大额,订单簿,聪明钱,总计,链接\n';
  combinedTop.forEach(([n, total], i) => {
    const arb = data.arbCounts.get(n) || 0;
    const large = data.largeTradeCounts.get(n) || 0;
    const ob = data.orderbookCounts.get(n) || 0;
    const smart = data.smartMoneyCounts.get(n) || 0;
    csv += `${i+1},"${n}",${arb},${large},${ob},${smart},${total},${link(n)}\n`;
  });
  
  // 7. 活跃时段分布 (UTC)
  csv += '\n# 活跃时段分布 (UTC)\n小时,信号数量,占比%\n';
  const totalSignals = data.hourlySignals.reduce((a, b) => a + b, 0);
  data.hourlySignals.forEach((count, hour) => {
    const pct = totalSignals > 0 ? (count / totalSignals * 100).toFixed(1) : 0;
    csv += `${hour.toString().padStart(2, '0')}:00,${count},${pct}\n`;
  });
  
  // 8. 时段-类型分布
  csv += '\n# 时段-类型分布 (UTC)\n小时,套利,大额交易,订单簿,聪明钱\n';
  for (let h = 0; h < 24; h++) {
    csv += `${h.toString().padStart(2, '0')}:00,${data.hourlyByType.arb[h]},${data.hourlyByType.large[h]},${data.hourlyByType.orderbook[h]},${data.hourlyByType.smart[h]}\n`;
  }
  
  // 9. 买卖比例
  csv += '\n# 买卖比例\n类型,数量,占比%\n';
  const totalBuySell = data.buySellStats.buy + data.buySellStats.sell;
  if (totalBuySell > 0) {
    csv += `买入(建仓/加仓),${data.buySellStats.buy},${(data.buySellStats.buy / totalBuySell * 100).toFixed(1)}\n`;
    csv += `卖出(清仓),${data.buySellStats.sell},${(data.buySellStats.sell / totalBuySell * 100).toFixed(1)}\n`;
    csv += `买卖比,${(data.buySellStats.buy / (data.buySellStats.sell || 1)).toFixed(2)}:1,\n`;
  }
  
  // 10. 聪明钱操作类型
  csv += '\n# 聪明钱操作类型\n类型,数量,占比%\n';
  const totalOps = data.smartMoneyOps.open + data.smartMoneyOps.add + data.smartMoneyOps.close;
  if (totalOps > 0) {
    csv += `建仓,${data.smartMoneyOps.open},${(data.smartMoneyOps.open / totalOps * 100).toFixed(1)}\n`;
    csv += `加仓,${data.smartMoneyOps.add},${(data.smartMoneyOps.add / totalOps * 100).toFixed(1)}\n`;
    csv += `清仓,${data.smartMoneyOps.close},${(data.smartMoneyOps.close / totalOps * 100).toFixed(1)}\n`;
  }
  
  // 11. 套利利润分布
  csv += '\n# 套利利润分布\n利润区间,数量,占比%\n';
  const totalProfit = Object.values(data.profitRanges).reduce((a, b) => a + b, 0);
  if (totalProfit > 0) {
    Object.entries(data.profitRanges).forEach(([range, count]) => {
      csv += `${range},${count},${(count / totalProfit * 100).toFixed(1)}\n`;
    });
  }
  
  // 12. 市场类别分布
  csv += '\n# 市场类别分布\n类别,信号数量,占比%\n';
  const totalCat = Object.values(data.categoryStats).reduce((a, b) => a + b, 0);
  const catNames = { sports: '体育', crypto: '加密货币', politics: '政治', entertainment: '娱乐', finance: '金融', other: '其他' };
  Object.entries(data.categoryStats)
    .sort((a, b) => b[1] - a[1])
    .forEach(([cat, count]) => {
      const pct = totalCat > 0 ? (count / totalCat * 100).toFixed(1) : 0;
      csv += `${catNames[cat]},${count},${pct}\n`;
    });
  
  // 13. 高频套利市场 (10次以上)
  csv += '\n# 高频套利市场 (10次以上)\n排名,市场名称,出现次数,最高利润%,链接\n';
  const highFreqArb = [...data.arbCounts.entries()].filter(([, c]) => c >= 10).sort((a, b) => b[1] - a[1]);
  highFreqArb.forEach(([n, c], i) => {
    csv += `${i+1},"${n}",${c},${data.arbProfits.get(n)||''},${link(n)}\n`;
  });
  
  // 14. 聪明钱偏好类别
  csv += '\n# 聪明钱偏好类别\n类别,信号数量,占比%\n';
  const totalSmartCat = Object.values(data.smartMoneyByCategory).reduce((a, b) => a + b, 0);
  Object.entries(data.smartMoneyByCategory)
    .sort((a, b) => b[1] - a[1])
    .forEach(([cat, count]) => {
      const pct = totalSmartCat > 0 ? (count / totalSmartCat * 100).toFixed(1) : 0;
      csv += `${catNames[cat]},${count},${pct}\n`;
    });
  
  // 15. 信号频率趋势 (环比)
  csv += '\n# 信号频率趋势 (环比)\n小时,信号数,环比变化%\n';
  data.hourlySignals.forEach((count, hour) => {
    const prevHour = hour === 0 ? 23 : hour - 1;
    const prev = data.hourlySignals[prevHour];
    const change = prev > 0 ? ((count - prev) / prev * 100).toFixed(1) : 'N/A';
    csv += `${hour.toString().padStart(2, '0')}:00,${count},${change}\n`;
  });
  
  // 16. 市场重复出现率 (出现在多种信号类型)
  csv += '\n# 市场重复出现率 (跨信号类型)\n信号类型数,市场数量,占比%\n';
  const typeCountDist = { 1: 0, 2: 0, 3: 0, 4: 0 };
  for (const [, types] of data.marketSignalTypes) {
    typeCountDist[types.size] = (typeCountDist[types.size] || 0) + 1;
  }
  const totalMarkets = Object.values(typeCountDist).reduce((a, b) => a + b, 0);
  Object.entries(typeCountDist).forEach(([n, count]) => {
    const pct = totalMarkets > 0 ? (count / totalMarkets * 100).toFixed(1) : 0;
    csv += `${n}种,${count},${pct}\n`;
  });
  
  // 17. 信号密集时段 (5分钟内爆发)
  csv += '\n# 信号密集时段 (5分钟内20+信号)\n时间,信号数量\n';
  data.signalBursts.sort((a, b) => b.count - a.count).slice(0, 15).forEach(b => {
    csv += `${b.time},${b.count}\n`;
  });
  
  // ========== API 数据模块 ==========
  console.error('📥 获取市场排行数据...');
  
  const [byVolume, byLiquidity] = await Promise.all([
    fetch(`${GAMMA_API}/markets?limit=20&order=volume24hr&ascending=false&active=true`).then(r => r.json()).catch(() => []),
    fetch(`${GAMMA_API}/markets?limit=20&order=liquidity&ascending=false&active=true`).then(r => r.json()).catch(() => [])
  ]);
  
  const getLink = (m) => {
    const slug = m.events?.[0]?.slug || m.slug;
    return `https://polymarket.com/event/${slug}`;
  };
  
  // 18. 24h成交量 Top 15
  csv += '\n# 24h成交量 Top 15\n排名,市场名称,24h成交量,价格,链接\n';
  byVolume.slice(0, 15).forEach((m, i) => {
    const price = m.outcomePrices ? JSON.parse(m.outcomePrices)[0] : '';
    csv += `${i+1},"${m.question}",${Math.round(m.volume24hr || 0)},${price},${getLink(m)}\n`;
  });
  
  // 19. 流动性 Top 15
  csv += '\n# 流动性 Top 15\n排名,市场名称,流动性,24h成交量,链接\n';
  byLiquidity.slice(0, 15).forEach((m, i) => {
    csv += `${i+1},"${m.question}",${Math.round(m.liquidity || 0)},${Math.round(m.volume24hr || 0)},${getLink(m)}\n`;
  });
  
  // 20. 24h涨幅 Top 15
  const withChange = byVolume.filter(m => m.oneDayPriceChange != null);
  const gainers = [...withChange].sort((a, b) => b.oneDayPriceChange - a.oneDayPriceChange);
  csv += '\n# 24h涨幅 Top 15\n排名,市场名称,涨幅%,当前价格,链接\n';
  gainers.slice(0, 15).forEach((m, i) => {
    const price = m.outcomePrices ? JSON.parse(m.outcomePrices)[0] : '';
    csv += `${i+1},"${m.question}",${(m.oneDayPriceChange * 100).toFixed(1)},${price},${getLink(m)}\n`;
  });
  
  // 21. 24h跌幅 Top 15
  const losers = [...withChange].sort((a, b) => a.oneDayPriceChange - b.oneDayPriceChange);
  csv += '\n# 24h跌幅 Top 15\n排名,市场名称,跌幅%,当前价格,链接\n';
  losers.slice(0, 15).forEach((m, i) => {
    const price = m.outcomePrices ? JSON.parse(m.outcomePrices)[0] : '';
    csv += `${i+1},"${m.question}",${(m.oneDayPriceChange * 100).toFixed(1)},${price},${getLink(m)}\n`;
  });
  
  console.log(csv);
}

main().catch(console.error);
