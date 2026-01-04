# Telegram 响应慢问题排查与修复记录

## 问题现象
- 点击 Telegram 按钮后主菜单不弹出或延迟严重
- 日志大量 `429 Too Many Requests: retry after 60`
- 服务崩溃，日志刷屏 `EPIPE` 错误

## 根本原因

### 1. 信号冷却被设为 0
配置文件 `config/settings.js` 中所有检测器冷却都是 0：
```javascript
// 错误配置
cooldown: 0  // 无冷却，信号量暴增
```

**正确配置**：
```javascript
arbitrage.cooldown: 10000   // 10秒
orderbook.cooldown: 1000    // 1秒
whale.cooldown: 5000        // 5秒
priceSpike.cooldown: 5000   // 5秒
```

### 2. 日志写入 EPIPE 死循环
`setupPersistentLogging()` 函数的文件流写入出现 EPIPE 错误时：
1. 错误被 `uncaughtException` 捕获
2. 捕获后尝试 `console.error` 写日志
3. 写日志又触发 EPIPE
4. 形成死循环，阻塞主线程

**修复**：禁用 `setupPersistentLogging()`
```javascript
if (require.main === module) {
    // 禁用文件日志（避免 EPIPE 错误）
    // setupPersistentLogging();
    
    const bot = new PolymarketSignalBot(config);
    // ...
}
```

### 3. 限速器删除后无保护
删除限速器后，所有 Telegram API 调用直接发送，短时间内大量请求触发 429。

## 关键配置参考（老版本 2025-12-11）

```javascript
// config/settings.js
telegram: {
    rateLimit: {
        enabled: process.env.TELEGRAM_RATE_LIMIT_ENABLED === 'true',
        minIntervalMs: 80,
        retryAfterPaddingMs: 500,
        maxRetries: 0
    }
},
arbitrage: {
    minProfit: 0.003,      // 0.3%
    tradingFee: 0.002,     // 0.2%
    cooldown: 10000,       // 10秒
    maxSignalsPerHour: 9999
},
orderbook: {
    minImbalance: 1.1,
    minDepth: 10,
    cooldown: 1000,        // 1秒
    maxSignalsPerHour: 9999
}
```

## 排查步骤

1. **检查 429 错误**
   ```bash
   tail -100 logs/runtime.log | grep "429"
   ```

2. **检查 EPIPE 错误**
   ```bash
   tail -100 logs/runtime.log | grep "EPIPE"
   ```

3. **检查进程状态**
   ```bash
   ps aux | grep "bot.js" | grep -v grep
   ```

4. **杀死旧进程重启**
   ```bash
   pkill -9 -f "bot.js"
   cd /home/lenovo/.projects/pronmarket/services/telegram-service
   node bot.js > logs/stdout.log 2>&1 &
   ```

## 备份位置
- 老版本备份：`/home/lenovo/.projects/pronmarket/backups/gz/备份_20251211_101124.tar.gz`
- 恢复命令：
  ```bash
  cd /tmp && mkdir old_backup && cd old_backup
  tar -xzf /path/to/备份_20251211_101124.tar.gz services/telegram-service/src/
  ```

## 教训总结

1. **不要把冷却设为 0** - 会导致信号量暴增触发 Telegram 限频
2. **日志写入要防死循环** - 错误处理中不要再写日志
3. **改配置前先备份** - 方便快速回滚
4. **限速器是保护机制** - 删除前要有替代方案

---
*记录时间：2025-12-22*
