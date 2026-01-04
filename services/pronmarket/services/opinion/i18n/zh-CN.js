/**
 * 中文语言包
 */
module.exports = {
  // 通用
  unknownMarket: '未知市场',
  openMarket: '📊 打开市场',
  viewMarket: '🔗 立即查看',
  
  // 时间
  time: { days: '天', hours: '小时', minutes: '分', seconds: '秒', ago: '前', later: '后结束' },
  
  // 套利
  arbitrage: {
    title: '💰 套利警报',
    direction: '方向',
    price: '价格',
    ratio: '占比',
    total: '合计',
    gap: '差价'
  },
  
  // 订单簿
  orderbook: {
    title: '📚 订单簿失衡',
    buy: '买方',
    sell: '卖方',
    imbalance: '失衡',
    bullish: '📈 看涨',
    bearish: '📉 看跌'
  },
  
  // 扫尾盘
  closing: {
    title: '⏰ 扫尾盘速览',
    endsIn: '后结束',
    volume: '成交量',
    liquidity: '流动性',
    page: '页',
    total: '共',
    markets: '个市场',
    prevPage: '⬅️ 上一页',
    nextPage: '下一页 ➡️',
    noMarkets: '当前时间窗口内未发现符合条件的市场，稍后再试。',
    jumpToMarket: '🔗 点击直接跳转到市场'
  },
  
  // 大额交易
  whale: {
    title: '💸 大额交易',
    buy: '买入',
    sell: '卖出',
    value: '价值'
  },
  
  // 新市场
  newMarket: {
    title: '🆕 新市场上线',
    trending: '🔥 热门新市场',
    volume24h: '24h量',
    totalVolume: '总量'
  },
  
  // 价格突变
  priceSpike: {
    title: '价格突变',
    volume24h: '24h量',
    dayChange: '日涨跌'
  },
  
  // 聪明钱
  smartMoney: {
    title: '🧠 聪明钱',
    newPosition: '建仓',
    addPosition: '加仓',
    reducePosition: '减仓',
    closePosition: '清仓',
    action: '操作',
    rank: '排名',
    score: '评分',
    pnl: '盈亏',
    value: '价值',
    address: '地址',
    position: '持仓',
    cost: '成本',
    settle: '结算'
  },
  
  // 深度套利
  deepArb: {
    title: '🔄 深度套利'
  },
  
  // 流动性预警
  liquidityAlert: {
    title: '⚠️ 流动性枯竭'
  },
  
  // 订单簿倾斜
  bookSkew: {
    title: '📊 订单簿倾斜'
  },
  
  // 面板
  panel: {
    title: '🐱 预测猫控制面板',
    moduleNotifThreshold: '模块/通知/阈值',
    beijingTime: '北京时间',
    closing: '📋 扫尾盘',
    threshold: '🎚️ 阈值',
    notification: '📢 通知',
    compactMode: '🔫 颗秒版',
    detailedMode: '📝 详细版',
    langSwitch: '🌐 EN',
    backToMain: '⬅️ 返回主菜单',
    notificationTitle: '📢 通知开关',
    notificationHint: '请选择要开启/关闭的通知类型：',
    thresholdTitle: '🎚️ 阈值设置',
    thresholdHint: '请选择模块并切换阈值：',
    loose: '宽松',
    medium: '中等',
    strict: '严格',
    // 模块名称
    modules: {
      arbitrage: '💼套利　',
      orderbook: '📚订单簿',
      closing: '⏰扫尾盘',
      largeTrade: '💸大额　',
      smartMoney: '🧠聪明钱',
      newMarket: '🆕新市场'
    }
  }
};
