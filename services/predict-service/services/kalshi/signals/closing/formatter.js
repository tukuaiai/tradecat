/**
 * 扫尾盘信号格式化
 */

function format(signal, translate = s => s) {
  const { market, yesPrice, noPrice, hoursLeft, confidence } = signal;
  const title = translate(market.title);
  
  // 信心等级 emoji
  const confidenceEmoji = {
    high: '🔥',
    medium: '⚡',
    low: '💡'
  }[confidence] || '💡';
  
  // 主导方向
  const dominant = yesPrice > noPrice ? 'YES' : 'NO';
  const dominantPrice = Math.max(yesPrice, noPrice);
  
  // 时间格式化
  let timeStr;
  if (hoursLeft < 1) {
    timeStr = `${Math.round(hoursLeft * 60)} 分钟`;
  } else if (hoursLeft < 24) {
    timeStr = `${hoursLeft.toFixed(1)} 小时`;
  } else {
    timeStr = `${(hoursLeft / 24).toFixed(1)} 天`;
  }
  
  return `${confidenceEmoji} *扫尾盘信号*

📌 *${title}*

🎯 预期结果: *${dominant}* (${(dominantPrice * 100).toFixed(0)}%)
⏰ 剩余时间: ${timeStr}
📊 成交量: $${(market.volume || 0).toLocaleString()}

💰 YES: $${yesPrice.toFixed(2)} | NO: $${noPrice.toFixed(2)}

🔗 [查看市场](https://kalshi.com/markets/${market.ticker})`;
}

// 批量格式化（列表视图）
function formatList(signals, translate = s => s) {
  if (signals.length === 0) return '暂无扫尾盘信号';
  
  let msg = `📋 *扫尾盘信号列表* (${signals.length}个)\n\n`;
  
  signals.slice(0, 10).forEach((signal, i) => {
    const { market, yesPrice, noPrice, hoursLeft } = signal;
    const title = translate(market.title).slice(0, 30);
    const dominant = yesPrice > noPrice ? 'YES' : 'NO';
    const dominantPrice = Math.max(yesPrice, noPrice);
    
    let timeStr = hoursLeft < 24 
      ? `${hoursLeft.toFixed(0)}h` 
      : `${(hoursLeft / 24).toFixed(0)}d`;
    
    msg += `${i + 1}. ${title}...\n`;
    msg += `   ${dominant} ${(dominantPrice * 100).toFixed(0)}% | ${timeStr}\n\n`;
  });
  
  return msg;
}

module.exports = { format, formatList };
