/**
 * 大额交易信号格式化
 */

function format(signal, market, translate = s => s) {
  const { trade, value, side, price } = signal;
  const title = translate(market?.title || signal.ticker);
  
  const emoji = side === 'yes' ? '🟢' : '🔴';
  const sideText = side === 'yes' ? 'YES' : 'NO';
  
  // 金额等级
  let sizeEmoji = '🐋';
  if (value >= 10000) sizeEmoji = '🐳';
  else if (value >= 5000) sizeEmoji = '🐋';
  else sizeEmoji = '🐟';
  
  return `${sizeEmoji} *大额交易*

${emoji} *${title}*

💰 金额: *$${value.toLocaleString()}*
📊 方向: ${sideText} @ $${price.toFixed(2)}
📦 数量: ${trade.count} 合约

🔗 [查看市场](https://kalshi.com/markets/${signal.ticker})`;
}

module.exports = { format };
