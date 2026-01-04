/**
 * English language pack
 */
module.exports = {
  // Common
  unknownMarket: 'Unknown Market',
  openMarket: '📊 Open Market',
  viewMarket: '🔗 View Now',
  
  // Time
  time: { days: 'd', hours: 'h', minutes: 'm', seconds: 's', ago: 'ago', later: 'left' },
  
  // Arbitrage
  arbitrage: {
    title: '💰 Arbitrage Alert',
    direction: 'Side',
    price: 'Price',
    ratio: 'Ratio',
    total: 'Total',
    gap: 'Gap'
  },
  
  // Orderbook
  orderbook: {
    title: '📚 Orderbook Imbalance',
    buy: 'Buy',
    sell: 'Sell',
    imbalance: 'Imbalance',
    bullish: '📈 Bullish',
    bearish: '📉 Bearish'
  },
  
  // Closing
  closing: {
    title: '⏰ Closing Markets',
    endsIn: 'left',
    volume: 'Volume',
    liquidity: 'Liquidity',
    page: 'Page',
    total: 'Total',
    markets: 'markets',
    prevPage: '⬅️ Prev',
    nextPage: 'Next ➡️',
    noMarkets: 'No markets found in current time window. Try again later.',
    jumpToMarket: '🔗 Jump to market'
  },
  
  // Whale
  whale: {
    title: '💸 Large Trade',
    buy: 'Buy',
    sell: 'Sell',
    value: 'Value'
  },
  
  // New Market
  newMarket: {
    title: '🆕 New Market',
    trending: '🔥 Trending New',
    volume24h: '24h Vol',
    totalVolume: 'Total Vol'
  },
  
  // Price Spike
  priceSpike: {
    title: 'Price Spike',
    volume24h: '24h Vol',
    dayChange: '24h Chg'
  },
  
  // Smart Money
  smartMoney: {
    title: '🧠 Smart Money',
    newPosition: 'Open',
    addPosition: 'Add',
    reducePosition: 'Reduce',
    closePosition: 'Close',
    action: 'Action',
    rank: 'Rank',
    score: 'Score',
    pnl: 'P&L',
    value: 'Value',
    address: 'Addr',
    position: 'Pos',
    cost: 'Cost',
    settle: 'Settle'
  },
  
  // Deep Arb
  deepArb: {
    title: '🔄 Deep Arbitrage'
  },
  
  // Liquidity Alert
  liquidityAlert: {
    title: '⚠️ Low Liquidity'
  },
  
  // Book Skew
  bookSkew: {
    title: '📊 Book Skew'
  },
  
  // Panel
  panel: {
    title: '🐱 Predict Cat Panel',
    moduleNotifThreshold: 'Module/Notif/Threshold',
    beijingTime: 'UTC+8',
    closing: '📋 Closing',
    threshold: '🎚️ Threshold',
    notification: '📢 Notif',
    compactMode: '🔫 Compact',
    detailedMode: '📝 Detailed',
    langSwitch: '🌐 中文',
    backToMain: '⬅️ Back',
    notificationTitle: '📢 Notifications',
    notificationHint: 'Toggle notifications:',
    thresholdTitle: '🎚️ Thresholds',
    thresholdHint: 'Select module and threshold:',
    loose: 'Loose',
    medium: 'Medium',
    strict: 'Strict',
    // Module names
    modules: {
      arbitrage: '💼Arb',
      orderbook: '📚Book',
      closing: '⏰Close',
      largeTrade: '💸Whale',
      smartMoney: '🧠Smart',
      newMarket: '🆕New'
    }
  }
};
