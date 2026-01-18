"""
Signal Service 入口

用法:
    python -m src --sqlite          # 启动 SQLite 引擎
    python -m src --pg              # 启动 PG 引擎
    python -m src --all             # 启动所有引擎
    python -m src --once            # 单次检查
    python -m src --stats           # 显示统计
"""

import argparse
import logging
import sys
from pathlib import Path

# 确保 src 在路径中
SRC_DIR = Path(__file__).parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Signal Service - 独立信号检测服务")
    parser.add_argument("--sqlite", action="store_true", help="启动 SQLite 引擎")
    parser.add_argument("--pg", action="store_true", help="启动 PG 引擎")
    parser.add_argument("--all", action="store_true", help="启动所有引擎")
    parser.add_argument("--once", action="store_true", help="单次检查")
    parser.add_argument("--interval", type=int, default=60, help="检查间隔（秒）")
    parser.add_argument("--stats", action="store_true", help="显示统计")
    parser.add_argument("--test", action="store_true", help="测试配置")
    args = parser.parse_args()

    if args.test:
        from config import get_database_url, get_history_db_path, get_sqlite_path
        from rules import RULE_COUNT, TABLE_COUNT

        logger.info("=== Signal Service 配置测试 ===")
        logger.info(f"  SQLite 路径: {get_sqlite_path()}")
        logger.info(f"  PG URL: {get_database_url()[:50]}...")
        logger.info(f"  历史 DB: {get_history_db_path()}")
        logger.info(f"  规则数: {RULE_COUNT}")
        logger.info(f"  表数: {TABLE_COUNT}")
        logger.info("✅ 配置测试通过")
        return

    if args.stats:
        from engines import get_pg_engine, get_sqlite_engine

        logger.info("=== 引擎统计 ===")
        try:
            sqlite_engine = get_sqlite_engine()
            logger.info(f"SQLite: {sqlite_engine.get_stats()}")
        except Exception as e:
            logger.warning(f"SQLite 引擎不可用: {e}")

        try:
            pg_engine = get_pg_engine()
            logger.info(f"PG: {pg_engine.get_stats()}")
        except Exception as e:
            logger.warning(f"PG 引擎不可用: {e}")
        return

    if args.once:
        # 单次检查
        if args.sqlite or args.all:
            from engines import get_sqlite_engine

            engine = get_sqlite_engine()
            signals = engine.check_signals()
            logger.info(f"SQLite 检测到 {len(signals)} 个信号")

        if args.pg or args.all:
            from engines import get_pg_engine

            engine = get_pg_engine()
            signals = engine.check_signals()
            logger.info(f"PG 检测到 {len(signals)} 个信号")
        return

    # 持续运行
    import threading

    # 注册持久化：把事件写入历史表
    try:
        from storage.history import get_history
        from events import SignalPublisher

        history = get_history()
        SignalPublisher.register_persist(lambda ev: history.save(ev, source=ev.source))
        logger.info("已注册历史持久化回调")
    except Exception as e:
        logger.warning(f"历史持久化注册失败: {e}")

    threads = []

    if args.sqlite or args.all:
        from engines import get_sqlite_engine

        def run_sqlite():
            engine = get_sqlite_engine()
            engine.run_loop(interval=args.interval)

        t = threading.Thread(target=run_sqlite, daemon=True, name="SQLiteEngine")
        t.start()
        threads.append(t)
        logger.info("SQLite 引擎已启动")

    if args.pg or args.all:
        from engines import get_pg_engine

        def run_pg():
            engine = get_pg_engine()
            engine.run_loop(interval=args.interval)

        t = threading.Thread(target=run_pg, daemon=True, name="PGEngine")
        t.start()
        threads.append(t)
        logger.info("PG 引擎已启动")

    if not threads:
        logger.error("请指定要启动的引擎: --sqlite, --pg, 或 --all")
        sys.exit(1)

    # 等待
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        logger.info("收到中断信号，退出...")


if __name__ == "__main__":
    main()
