"""
历史指标回填脚本
根据 RETENTION 配置，为每个币种每个周期计算并写入历史指标数据
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from src.db.reader import writer, reader
from src.indicators.base import get_batch_indicators
from src.core.async_full_engine import get_high_priority_symbols_fast

# 保留条数配置（与 reader.py 一致）
RETENTION = {
    '1m': 120,
    '5m': 120,
    '15m': 96,
    '1h': 144,
    '4h': 84,
    '1d': 120,
    '1w': 48,
}

INTERVALS = ['1m', '5m', '15m', '1h', '4h', '1d', '1w']


def backfill_symbol_interval(symbol: str, interval: str, indicators: dict, retention: int):
    """为单个币种单个周期回填历史指标"""
    max(ind.meta.lookback for ind in indicators.values())

    # 获取尽可能多的K线数据
    klines = reader.get_klines([symbol], interval, 10000)
    df = klines.get(symbol)
    if df is None or len(df) < 10:
        return 0

    total_bars = len(df)
    computed = 0

    for name, ind_cls in indicators.items():
        indicator = ind_cls()
        lookback = indicator.meta.lookback
        min_data = getattr(indicator.meta, 'min_data', 5)

        results = []
        # 从能计算的最早位置开始
        for end_idx in range(min_data, total_bars + 1):
            window_df = df.iloc[max(0, end_idx - lookback):end_idx].copy()

            if len(window_df) < min_data:
                continue

            try:
                result = indicator.compute(window_df, symbol, interval)
                if result is not None and not result.empty:
                    results.append(result)
            except Exception:
                continue

        if results:
            all_results = pd.concat(results, ignore_index=True)
            all_results = all_results.drop_duplicates(
                subset=['交易对', '周期', '数据时间'],
                keep='last'
            ).tail(retention)

            writer.write(indicator.meta.name, all_results, interval)
            computed += len(all_results)

    return computed


def backfill_all(symbols: list = None, intervals: list = None, indicator_names: list = None):
    """回填所有历史指标"""
    if symbols is None:
        symbols = get_high_priority_symbols_fast(top_n=50) or []
        if not symbols:
            print("无法获取币种列表")
            return

    if intervals is None:
        intervals = INTERVALS

    indicators = get_batch_indicators()
    if indicator_names:
        indicators = {k: v for k, v in indicators.items() if k in indicator_names}

    print(f"开始回填: {len(symbols)} 币种, {len(intervals)} 周期, {len(indicators)} 指标")
    print(f"保留配置: {RETENTION}")
    print("-" * 60)

    total_start = time.time()
    total_computed = 0

    for interval in intervals:
        retention = RETENTION.get(interval, 60)
        print(f"\n[{interval}] 保留 {retention} 条")

        for i, symbol in enumerate(symbols):
            t0 = time.time()
            computed = backfill_symbol_interval(symbol, interval, indicators, retention)
            total_computed += computed

            if computed > 0:
                print(f"  {symbol}: {computed} 条, {time.time()-t0:.1f}s")

            # 进度
            if (i + 1) % 10 == 0:
                print(f"  进度: {i+1}/{len(symbols)}")

    print("-" * 60)
    print(f"完成! 总计 {total_computed} 条, 耗时 {time.time()-total_start:.1f}s")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="历史指标回填")
    parser.add_argument("-s", "--symbols", nargs="+", help="指定币种")
    parser.add_argument("-i", "--intervals", nargs="+", help="指定周期")
    parser.add_argument("-n", "--indicators", nargs="+", help="指定指标")
    parser.add_argument("--top", type=int, default=50, help="高优先级币种数量")
    args = parser.parse_args()

    symbols = args.symbols
    if not symbols:
        symbols = get_high_priority_symbols_fast(top_n=args.top)

    backfill_all(symbols, args.intervals, args.indicators)
