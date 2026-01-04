/**
 * 新市场信号格式化
 */

function format(signal, translate = s => s) {
  const { market } = signal;
  const title = translate(market.title);
  const category = market.category || '未分类';
  const closeTime = new Date(market.close_time).toLocaleString('zh-CN');
  
  // 价格转换（Kalshi 用 cents）
  const yesPrice = market.yes_bid ? (market.yes_bid / 100).toFixed(2) : '-';
  const noPrice = market.no_bid ? (market.no_bid / 100).toFixed(2) : '-';
  const volume = market.volume_24h || 0;
  
  return `🆕 *新市场上线*

📌 *${title}*

📊 分类: ${category}
💰 YES: $${yesPrice} | NO: $${noPrice}
📈 24h成交: $${volume.toLocaleString()}
⏰ 截止: ${closeTime}

🔗 [查看市场](https://kalshi.com/markets/${market.ticker})`;
}

module.exports = { format };
