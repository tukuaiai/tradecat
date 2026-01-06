#!/usr/bin/env python3
"""下载 Binance Vision bookDepth 数据"""
import csv
import io
import logging
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests

from crypto.adapters.ccxt import load_symbols
from crypto.adapters.rate_limiter import acquire, release
from crypto.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BINANCE_DATA_URL = "https://data.binance.vision"
DATA_DIR = settings.data_dir / "downloads" / "bookDepth"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def download_bookdepth(symbol: str, d: date) -> Path | None:
    """下载单个币种单日 bookDepth"""
    fname = f"{symbol}-bookDepth-{d}.zip"
    fpath = DATA_DIR / fname
    
    if fpath.exists():
        logger.debug("已存在: %s", fname)
        return fpath
    
    url = f"{BINANCE_DATA_URL}/data/futures/um/daily/bookDepth/{symbol}/{fname}"
    
    acquire(1)
    try:
        proxies = {"http": settings.http_proxy, "https": settings.http_proxy} if settings.http_proxy else {}
        r = requests.get(url, proxies=proxies, timeout=60)
        if r.status_code == 404:
            logger.warning("不存在: %s", fname)
            return None
        r.raise_for_status()
        fpath.write_bytes(r.content)
        logger.info("下载完成: %s (%.1f KB)", fname, len(r.content) / 1024)
        return fpath
    except Exception as e:
        logger.error("下载失败 %s: %s", fname, e)
        return None
    finally:
        release()


def parse_bookdepth(fpath: Path) -> list[dict]:
    """解析 bookDepth ZIP 文件"""
    rows = []
    try:
        with zipfile.ZipFile(fpath) as zf:
            for name in zf.namelist():
                if not name.endswith(".csv"):
                    continue
                with zf.open(name) as f:
                    reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
                    for row in reader:
                        rows.append({
                            "timestamp": row["timestamp"],
                            "percentage": int(row["percentage"]),
                            "depth": Decimal(row["depth"]),
                            "notional": Decimal(row["notional"]),
                        })
    except Exception as e:
        logger.error("解析失败 %s: %s", fpath, e)
    return rows


def main():
    symbols = load_symbols("binance")
    logger.info("币种: %s", symbols)
    
    # 最近 10 天
    end = date.today() - timedelta(days=1)  # 昨天
    start = end - timedelta(days=9)         # 10 天前
    
    dates = [start + timedelta(days=i) for i in range(10)]
    tasks = [(sym, d) for sym in symbols for d in dates]
    
    logger.info("下载任务: %d 个 (%d 币种 x %d 天)", len(tasks), len(symbols), len(dates))
    
    downloaded = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(download_bookdepth, sym, d): (sym, d) for sym, d in tasks}
        for future in as_completed(futures):
            sym, d = futures[future]
            result = future.result()
            if result:
                downloaded.append(result)
    
    logger.info("下载完成: %d 个文件", len(downloaded))
    
    # 统计
    total_rows = 0
    for fpath in downloaded[:3]:  # 只解析前 3 个看看
        rows = parse_bookdepth(fpath)
        total_rows += len(rows)
        logger.info("  %s: %d 行", fpath.name, len(rows))
    
    logger.info("数据目录: %s", DATA_DIR)


if __name__ == "__main__":
    main()
