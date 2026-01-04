/**
 * 扫尾盘检测模块
 * 
 * 检测即将到期且价格极端的市场
 */

const config = require('../../config/settings');

class ClosingDetector {
  constructor(kalshiClient) {
    this.client = kalshiClient;
    this.onSignal = null;
  }

  // 扫描即将到期的市场
  async scan() {
    const signals = [];
    const now = Date.now();
    const windowMs = config.closing.timeWindowHours * 3600 * 1000;
    
    try {
      const { markets } = await this.client.getMarkets({
        limit: 500,
        status: 'open',
        max_close_ts: Math.floor((now + windowMs) / 1000)
      });
      
      for (const market of markets) {
        // 过滤低成交量
        if ((market.volume || 0) < config.closing.minVolume) continue;
        
        // 计算价格（cents -> 0-1）
        const yesPrice = (market.yes_bid || 0) / 100;
        const noPrice = (market.no_bid || 0) / 100;
        
        // 检测高确定性市场（YES 或 NO > 90%）
        const isHighConfidence = yesPrice >= 0.90 || noPrice >= 0.90;
        if (!isHighConfidence) continue;
        
        // 计算剩余时间
        const closeTime = new Date(market.close_time).getTime();
        const hoursLeft = (closeTime - now) / (3600 * 1000);
        
        // 确定信心等级
        let confidence = 'low';
        if (hoursLeft <= config.closing.highConfidenceHours) {
          confidence = 'high';
        } else if (hoursLeft <= config.closing.mediumConfidenceHours) {
          confidence = 'medium';
        }
        
        const signal = {
          type: 'closing',
          market,
          yesPrice,
          noPrice,
          hoursLeft,
          confidence,
          timestamp: now
        };
        
        signals.push(signal);
        
        if (this.onSignal) {
          this.onSignal(signal);
        }
      }
      
      // 按剩余时间排序
      signals.sort((a, b) => a.hoursLeft - b.hoursLeft);
      
      if (signals.length > 0) {
        console.log(`[Closing] 发现 ${signals.length} 个扫尾盘机会`);
      }
    } catch (err) {
      console.error('[Closing] 扫描失败:', err.message);
    }
    
    return signals.slice(0, config.closing.maxMarkets);
  }

  // 启动定时扫描
  start() {
    if (!config.closing.enabled) {
      console.log('[Closing] 模块已禁用');
      return;
    }

    console.log('[Closing] 模块已启动');
    
    // 首次扫描
    this.scan();
    
    // 定时扫描
    this.timer = setInterval(() => this.scan(), config.closing.refreshIntervalMs);
  }

  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }
}

module.exports = ClosingDetector;
