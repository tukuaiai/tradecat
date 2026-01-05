#!/usr/bin/env python3
# 兼容入口：保留原路径，实际逻辑迁移到 bot/app.py
# 导出所有符号，确保模块可被导入
from bot.app import *  # noqa: F401,F403
from bot.app import main  # noqa: F401 - explicit import for __main__
import sys as _sys

# 将当前模块设置别名，便于其他模块引用
_sys.modules.setdefault("main", _sys.modules[__name__])

if __name__ == "__main__":
    main()
