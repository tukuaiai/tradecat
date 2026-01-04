2025-12-25T02:15:25+08:00 WS 消息格式修复
- 任务范围：live-signal-monitor.js 实时订阅解析
- 关键改动：新增 normalizeEvent，按 event_type 对象数组逐条处理；修正 WS 消息解析错误日志
- 涉及文件：live-signal-monitor.js
- 验证：GLOBAL_AGENT_HTTP_PROXY=http://127.0.0.1:9910 timeout 12s node live-signal-monitor.js（收到流动性/订单簿信号，消息计数增长）
- 遗留/下一步：完善其他信号阈值与长期运行观察 TODO
2025-12-25T02:25:52+08:00 新功能文档同步与SDK格式适配
- 任务范围：记录新增信号模块、SDK 消息格式兼容
- 关键改动：更新 AGENTS.md/README.md 列出 7 个新信号；确认 WS event_type 兼容逻辑已落地
- 涉及文件：AGENTS.md，services/polymarket/README.md，services/polymarket/live-signal-monitor.js
- 验证：文档检查，live-signal-monitor 12s 短跑收到 book 信号
- 遗留/下一步：将新信号整合进主 bot 发送逻辑；补充长时间运行观察 TODO
2025-12-25T02:54:08+08:00 降噪调参
- 任务范围：live-signal-monitor 阈值与冷却调整，降低流动性/盘口类告警风暴
- 关键改动：价格突变/大额交易/深度套利/流动性枯竭/订单簿倾斜/聪明钱 全部开启限频；收紧深度与比例阈值，增大窗口；提高大额交易与聪明钱价值门槛
- 涉及文件：services/polymarket/live-signal-monitor.js
- 验证：待长时间实测观察告警频次 TODO
- 遗留/下一步：必要时进一步加入绝对跌幅/倾斜持续性过滤与每小时上限
2025-12-25T03:00:51+08:00 限频策略改为纯“单市场”
- 任务范围：live-signal-monitor 取消全局/每小时限频，只保留单市场冷却
- 关键改动：各检测器 maxSignalsPerHour 设为高值，仍保留每市场 cooldown；阈值与窗口保持上轮收紧配置
- 涉及文件：services/polymarket/live-signal-monitor.js
- 验证：待重启后观察单市场告警频次 TODO
- 遗留/下一步：如仍过多，可增加“连续两次满足才报警”或绝对跌额过滤
2025-12-26T06:17:05+08:00 扫尾盘仅按时间过滤
- 任务范围：closing 扫尾盘过滤与排序去除成交量/流动性/价格影响
- 关键改动：拉取上限提升至 500；移除成交量/流动性/价格过滤；移除价格档位评分；排序仅按剩余时间；日志改为“时间窗口内”；配置删除 priceDeviation/absoluteThreshold
- 涉及文件：services/polymarket/signals/closing/detector.js，services/polymarket/config/settings.js，services/polymarket/bot.js
- 验证：TODO（未跑实时扫描）
- 遗留/下一步：若 7 天内市场 >500 需分页/进一步拉取；视需要调整格式化分页大小
