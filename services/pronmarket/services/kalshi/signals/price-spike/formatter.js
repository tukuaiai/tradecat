/**
 * 价格突变信号格式化
 */

function format(signal, translate = s => s) {
  const { market, oldPrice, newPrice, change, direction } = signal;
  const title = translate(market?.title || signal.ticker);
  
  const emoji = direction === 'up' ? '📈' : '📉';
  const arrow = direction === 'up' ? '⬆️' : '⬇️';
  const changePercent = (change * 100).toFixed(1);
  
  return `${emoji} *价格突变*

📌 *${title}*

${arrow} 变化: *${direction === 'up' ? '+' : '-'}${changePercent}%*
💰 $${oldPrice.toFixed(2)} → $${newPrice.toFixed(2)}

⚠️ 短时间内价格剧烈波动

🔗 [查看市场](https://kalshi.com/markets/${signal.ticker})`;
}

module.exports = { format };
