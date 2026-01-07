#!/usr/bin/env python3
"""导入 bookDepth 数据到 TimescaleDB"""
import csv
import io
import logging
import re
import sys
import zipfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from crypto.adapters.timescale import TimescaleAdapter
from crypto.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = settings.data_dir / "downloads" / "bookDepth"


def parse_bookdepth_file(fpath: Path) -> list[dict]:
    """解析单个 bookDepth ZIP 文件"""
    # 从文件名提取 symbol: BTCUSDT-bookDepth-2026-01-05.zip
    match = re.match(r"(\w+)-bookDepth-", fpath.name)
    if not match:
        logger.warning("无法解析文件名: %s", fpath.name)
        return []
    symbol = match.group(1)
    rows = []
    with zipfile.ZipFile(fpath) as zf:
        for name in zf.namelist():
            if not name.endswith(".csv"):
                continue
            with zf.open(name) as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
                for row in reader:
                    # 解析时间戳: "2026-01-05 00:00:09" -> timestamptz
                    ts = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
                    ts = ts.replace(tzinfo=timezone.utc)
                    rows.append({
                        "timestamp": ts,
                        "exchange": "binance_futures_um",
                        "symbol": symbol,
                        "percentage": int(row["percentage"]),
                        "depth": Decimal(row["depth"]),
                        "notional": Decimal(row["notional"]),
                    })
    return rows


def import_to_db(rows: list[dict], ts: TimescaleAdapter) -> int:
    """批量导入到数据库"""
    if not rows:
        return 0
    from psycopg import sql
    cols = ["timestamp", "exchange", "symbol", "percentage", "depth", "notional"]
    with ts.connection() as conn:
        with conn.cursor() as cur:
            # 使用 COPY 高效写入
            with cur.copy(sql.SQL("COPY raw.crypto_book_depth ({}) FROM STDIN").format(
                sql.SQL(", ").join(map(sql.Identifier, cols))
            )) as copy:
                for row in rows:
                    copy.write_row(tuple(row[c] for c in cols))
        conn.commit()
    return len(rows)


def main():
    # 使用 5434 数据库
    db_url = "postgresql://postgres:postgres@localhost:5434/market_data"
    ts = TimescaleAdapter(db_url=db_url)

    files = sorted(DATA_DIR.glob("*.zip"))
    logger.info("找到 %d 个文件", len(files))

    total = 0
    for fpath in files:
        rows = parse_bookdepth_file(fpath)
        if rows:
            n = import_to_db(rows, ts)
            total += n
            logger.info("导入 %s: %d 行", fpath.name, n)

    ts.close()
    logger.info("导入完成: 共 %d 行", total)

    # 验证
    import subprocess
    result = subprocess.run([
        "psql", "-h", "localhost", "-p", "5434", "-U", "postgres", "-d", "market_data",
        "-c", "SELECT symbol, COUNT(*), MIN(timestamp), MAX(timestamp) FROM raw.crypto_book_depth GROUP BY symbol ORDER BY symbol;"
    ], env={"PGPASSWORD": "postgres"}, capture_output=True, text=True)
    print("\n=== 导入结果 ===")
    print(result.stdout)


if __name__ == "__main__":
    main()
