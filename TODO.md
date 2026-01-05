[ ] i18n 完善  
    - 统一 /lang 与 /ai 入口的语言偏好落盘/读取路径，覆盖按钮流、命令流、快捷触发三条链路。  
    - 补齐 locales/en 与 zh_CN 词条缺失项，运行 ./scripts/verify.sh 后人工对话验收。  

[ ] 优化部署流程（简单、方便，有效先使用旧的数据库配置优化流程和实现）  
    - 明确 TimescaleDB 端口单一来源（5433 或 5434），同步 config/.env.example、export/restore 脚本与 README。  
    - 在 install/init/start 三脚本中补充失败提示与依赖缺失指引，保证全流程零交互可跑通。  

[ ] 优化信号功能  
    - 检查 telegram-service/src/signals 下规则，补充单元/集成测试或最小复现脚本。  
    - 为高频告警增加去重/节流配置项（写入 config/.env.example 并文档化）。  

[ ] 适配新的服务和本地 GEMINI CLI 处理 AI 请求的方法  
    - 梳理 services/predict-service 入口（各 package.json）并写入 README/AGENTS 的启动示例。  
    - 提供本地 CLI 示例：ai-service/scripts/start.sh analyze/test，确保无需 Telegram 也能跑通。  

[ ] 数据库完全迁移到新的 TimescaleDB（RAW/QUALITY schema）  
    - 迁移脚本与 README 说明统一到新端口/新 schema；确保数据导出/恢复/压缩脚本可用。  
    - 验收：使用 restore_*.sh 完成一次全量恢复并通过 ./scripts/verify.sh。


[ ] 新建专业的可视化数据分析微服务，内置有常用可视化类型/模板

\\wsl.localhost\Ubuntu\home\lenovo\.projects\tradecat\image.png

vpvr可视化的山脊图版本