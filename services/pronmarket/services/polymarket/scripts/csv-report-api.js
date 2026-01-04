#!/usr/bin/env node
/**
 * CSV 报告生成器 - 直接从 API 获取数据
 */

const GAMMA_API = 'https://gamma-api.polymarket.com';

async function fetchJson(url) {
  const res = await fetch(url);
  return res.json();
}

async function main() {
  console.error('📊 生成 CSV 报告...\n');
  
  // 获取热门市场
  const [byVolume, byLiquidity] = await Promise.all([
    fetchJson(`${GAMMA_API}/markets?limit=50&order=volume24hr&ascending=false&active=true`),
    fetchJson(`${GAMMA_API}/markets?limit=50&order=liquidity&ascending=false&active=true`)
  ]);
  
  // 获取 event slug
  const getLink = (m) => {
    const events = m.events || [];
    const slug = events[0]?.slug || m.slug;
    return `https://polymarket.com/event/${slug}`;
  };
  
  let csv = '';
  
  // 1. 24h成交量 Top 15
  csv += '# 24h成交量 Top 15\n排名,市场名称,24h成交量,价格,链接\n';
  byVolume.slice(0, 15).forEach((m, i) => {
    const price = m.outcomePrices ? JSON.parse(m.outcomePrices)[0] : '';
    csv += `${i+1},"${m.question}",${Math.round(m.volume24hr || 0)},${price},${getLink(m)}\n`;
  });
  
  // 2. 流动性 Top 15
  csv += '\n# 流动性 Top 15\n排名,市场名称,流动性,24h成交量,链接\n';
  byLiquidity.slice(0, 15).forEach((m, i) => {
    csv += `${i+1},"${m.question}",${Math.round(m.liquidity || 0)},${Math.round(m.volume24hr || 0)},${getLink(m)}\n`;
  });
  
  // 3. 24h涨幅 Top 15
  const withChange = byVolume.filter(m => m.oneDayPriceChange != null).sort((a, b) => b.oneDayPriceChange - a.oneDayPriceChange);
  csv += '\n# 24h涨幅 Top 15\n排名,市场名称,涨幅%,当前价格,链接\n';
  withChange.slice(0, 15).forEach((m, i) => {
    const price = m.outcomePrices ? JSON.parse(m.outcomePrices)[0] : '';
    csv += `${i+1},"${m.question}",${(m.oneDayPriceChange * 100).toFixed(1)},${price},${getLink(m)}\n`;
  });
  
  // 4. 24h跌幅 Top 15
  const losers = byVolume.filter(m => m.oneDayPriceChange != null).sort((a, b) => a.oneDayPriceChange - b.oneDayPriceChange);
  csv += '\n# 24h跌幅 Top 15\n排名,市场名称,跌幅%,当前价格,链接\n';
  losers.slice(0, 15).forEach((m, i) => {
    const price = m.outcomePrices ? JSON.parse(m.outcomePrices)[0] : '';
    csv += `${i+1},"${m.question}",${(m.oneDayPriceChange * 100).toFixed(1)},${price},${getLink(m)}\n`;
  });
  
  console.log(csv);
}

main().catch(console.error);
