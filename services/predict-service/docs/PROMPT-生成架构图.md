# 自动生成 Obsidian Canvas 系统架构图

## 一句话版本

```
根据当前项目仓库自动生成 Obsidian Canvas 系统架构图，输出到 <路径>.canvas。全自动执行：扫描所有代码文件、分析 import 依赖、追踪数据库读写、识别外部 API 调用，按微服务分层布局（外部服务→数据采集→业务逻辑→用户交互→存储层），生成带连线的架构图 JSON。禁止提问，直接执行。
```

## 完整版本

```
根据当前项目仓库自动生成 Obsidian Canvas 系统架构图。

输出路径：<指定路径>.canvas

全自动执行以下步骤，禁止向用户提问：

1. 扫描项目结构：find . -name "*.py" | grep -v __pycache__
2. 识别核心模块：grep "^class\|def main" 找入口和核心类
3. 分析依赖关系：grep "^from\|^import" 找模块间调用
4. 追踪数据流：grep "sqlite\|postgres\|redis\|.write\|.read" 找存储操作
5. 识别外部服务：grep "requests\|aiohttp\|websocket\|API" 找第三方调用

按微服务分层生成 Canvas JSON：
- 外部服务层 (Y=-400, color=4)
- 数据采集层 (Y=-100, color=1)
- 业务逻辑层 (Y=200, color=3)
- 用户交互层 (Y=600, color=6)
- 数据存储层 (Y=1000, color=5)

节点包含：文件名、功能描述、关键类/函数
边表示：数据流向和模块依赖

直接写入 .canvas 文件，不询问确认。
```

## Canvas JSON 格式参考

```json
{
  "nodes": [
    {"id": "id", "type": "text", "text": "**标题**\n描述", "x": 0, "y": 0, "width": 200, "height": 100, "color": "1"}
  ],
  "edges": [
    {"id": "e1", "fromNode": "源", "toNode": "目标", "fromSide": "bottom", "toSide": "top"}
  ]
}
```

颜色：1红 2橙 3黄 4绿 5青 6紫
