"""
计算引擎（高性能版）

核心优化：
1. 多周期并行读取数据
2. 多进程并行计算（按周期+币种分片）
3. 使用 pickle 协议5 优化序列化
4. 进程池复用
5. 一次性写入所有结果
6. 可观测性：日志、指标、Tracing、告警
"""
import logging
import time
import pickle
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from typing import Dict, List, Tuple, Any
import pandas as pd

from ..config import config
from ..indicators.base import get_all_indicators, get_batch_indicators, get_incremental_indicators
from ..utils.precision import trim_dataframe
from ..observability import get_logger, log_context, metrics, trace, alert, AlertLevel

LOG = get_logger("indicator_service")

# 指标定义
_compute_total = metrics.counter("indicator_compute_total", "指标计算总次数")
_compute_errors = metrics.counter("indicator_compute_errors", "指标计算错误次数")
_compute_duration = metrics.histogram("indicator_compute_duration_seconds", "指标计算耗时", (0.5, 1, 2, 5, 10, 30, 60))
_db_read_duration = metrics.histogram("db_read_duration_seconds", "数据库读取耗时", (0.5, 1, 2, 5, 10, 30))
_db_write_duration = metrics.histogram("db_write_duration_seconds", "数据库写入耗时", (0.1, 0.5, 1, 2, 5))
_active_symbols = metrics.gauge("active_symbols", "活跃交易对数量")
_last_compute_ts = metrics.gauge("last_compute_timestamp", "最后计算时间戳")

# 全局进程池（复用）
_executor: ProcessPoolExecutor = None


def _get_executor(max_workers: int) -> ProcessPoolExecutor:
    """获取或创建进程池"""
    global _executor
    if _executor is None:
        _executor = ProcessPoolExecutor(max_workers=max_workers)
    return _executor


def _compute_batch(args: Tuple) -> Dict[str, List[dict]]:
    """计算一批 (symbol, interval, df_bytes) 的所有指标"""
    import pandas as pd
    import pickle
    import sys
    import os
    
    # 确保能找到模块
    service_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if service_root not in sys.path:
        sys.path.insert(0, service_root)
    
    from src.indicators.base import get_all_indicators
    
    batch, indicator_names, futures_cache = args
    
    # 设置期货缓存
    if futures_cache:
        try:
            from src.indicators.incremental.futures_sentiment import set_metrics_cache
            set_metrics_cache(futures_cache)
        except ImportError:
            pass
    
    indicators = get_all_indicators()
    if indicator_names:
        indicators = {k: v for k, v in indicators.items() if k in indicator_names}
    
    results = {name: [] for name in indicators}
    
    for symbol, interval, df_bytes in batch:
        # 反序列化 DataFrame（兼容已序列化和未序列化）
        df = pickle.loads(df_bytes) if isinstance(df_bytes, bytes) else df_bytes
        last_ts = df.index[-1].isoformat() if len(df) > 0 and hasattr(df.index[-1], 'isoformat') else None
        
        for name, cls in indicators.items():
            ind = cls()
            placeholder = [{"交易对": symbol, "周期": interval, "数据时间": last_ts, "指标": None}]
            
            if len(df) < ind.meta.lookback // 2:
                if last_ts:
                    results[name].append(placeholder)
                continue
            try:
                result = ind.compute(df, symbol, interval)
                if result is not None and not result.empty:
                    results[name].append(result.to_dict('records'))
                elif last_ts:
                    results[name].append(placeholder)
            except:
                if last_ts:
                    results[name].append(placeholder)
    
    return results


class Engine:
    """指标计算引擎（高性能版）"""
    
    def __init__(
        self,
        symbols: List[str] = None,
        intervals: List[str] = None,
        indicators: List[str] = None,
        lookback: int = None,
        max_workers: int = None,
        compute_backend: str = None,
    ):
        self.symbols = symbols
        self.intervals = intervals or config.intervals
        self.indicator_names = indicators
        self.lookback = lookback or config.default_lookback
        self.max_workers = max_workers or min(cpu_count(), 8)
        self.compute_backend = (compute_backend or config.compute_backend or "thread").lower()
    
    def run(self, mode: str = "all"):
        """运行计算 - 使用缓存，只读取一次"""
        import pickle
        from ..db.cache import get_cache, init_cache
        
        with trace("engine.run", mode=mode) as span:
            start = time.time()
            
            # 使用传入的币种，或自动获取高优先级
            if self.symbols:
                symbols = self.symbols
            else:
                from .async_full_engine import get_high_priority_symbols_fast
                t_priority = time.time()
                high_symbols = get_high_priority_symbols_fast(top_n=15)
                if not high_symbols:
                    LOG.warning("无高优先级币种")
                    alert(AlertLevel.WARNING, "无高优先级币种", "获取高优先级币种失败，计算终止")
                    return
                symbols = list(high_symbols)
                LOG.info(f"高优先级币种: {len(symbols)} 个, 耗时 {time.time()-t_priority:.1f}s")
            
            _active_symbols.set(len(symbols))
            span.set_tag("symbols_count", len(symbols))
            
            if mode == "batch":
                indicators = get_batch_indicators()
            elif mode == "incremental":
                indicators = get_incremental_indicators()
            else:
                indicators = get_all_indicators()
            
            if self.indicator_names:
                indicators = {k: v for k, v in indicators.items() if k in self.indicator_names}
            
            if not indicators:
                LOG.warning("无指标需要计算")
                return
            
            max_lookback = max(ind.meta.lookback for ind in indicators.values())
            span.set_tag("indicators_count", len(indicators))
            
            LOG.info(f"开始计算: {len(symbols)} 币种, {len(self.intervals)} 周期, {len(indicators)} 指标, {self.max_workers} 进程")
            
            # 使用缓存 - 检查是否需要初始化或更新
            with trace("db.read") as read_span:
                t0 = time.time()
                cache = get_cache()
                symbols_set = set(symbols)
                
                # 检查缓存是否已初始化且包含所需周期
                need_init = not cache._initialized or not all(iv in cache._initialized for iv in self.intervals)
                if need_init:
                    cache = init_cache(symbols, self.intervals, max_lookback)
                else:
                    # 增量更新已有缓存
                    for iv in self.intervals:
                        cache.update_interval(symbols, iv)
                
                # 从缓存获取数据
                all_klines = {}
                for interval in self.intervals:
                    klines = cache.get_klines(interval)
                    for sym, df in klines.items():
                        if sym in symbols_set:
                            all_klines[(sym, interval)] = df
                
                t_read = time.time() - t0
                _db_read_duration.observe(t_read)
                read_span.set_tag("klines_count", len(all_klines))
            
            LOG.info(f"数据读取完成: {len(all_klines)} 组, 耗时 {t_read:.1f}s")
            
            if not all_klines:
                LOG.warning("无K线数据")
                alert(AlertLevel.WARNING, "无K线数据", "数据库中无可用K线数据")
                return
            
            # 准备计算任务 - 线程模式直接传 DataFrame，进程模式使用 pickle
            use_pickle = self.compute_backend == "process"
            task_list = [
                (sym, iv, pickle.dumps(df, protocol=5) if use_pickle else df)
                for (sym, iv), df in all_klines.items()
            ]
            
            # 预加载期货缓存
            try:
                from src.indicators.incremental.futures_sentiment import get_metrics_cache
                futures_cache = get_metrics_cache()
            except ImportError:
                futures_cache = None
            
            # 分片并行计算
            with trace("compute") as compute_span:
                t1 = time.time()
                indicator_names = list(indicators.keys())
                
                if len(task_list) <= 20:
                    all_results = _compute_batch((task_list, indicator_names, futures_cache))
                else:
                    all_results = self._compute_parallel(
                        task_list,
                        indicator_names,
                        indicators,
                        futures_cache,
                        backend=self.compute_backend,
                    )
                
                t_compute = time.time() - t1
                _compute_duration.observe(t_compute)
                compute_span.set_tag("duration_s", round(t_compute, 2))
            
            # 写入数据库
            with trace("db.write") as write_span:
                t2 = time.time()
                # 写入 market_data.db（每个指标一张表，全量覆盖）
                self._write_simple_db(all_results)
                t_write = time.time() - t2
                _db_write_duration.observe(t_write)
                write_span.set_tag("duration_s", round(t_write, 2))
            
            total_rows = sum(len(recs) for recs_list in all_results.values() for recs in recs_list)
            total_time = time.time() - start
            
            # 更新指标
            _compute_total.inc(total_rows)
            _last_compute_ts.set(time.time())
            
            span.set_tag("total_rows", total_rows)
            span.set_tag("total_time_s", round(total_time, 2))
            
            LOG.info(f"计算完成: 读取={t_read:.1f}s, 计算={t_compute:.1f}s, 写入={t_write:.2f}s, {total_rows}行, 总耗时 {total_time:.2f}s")
            
            # 慢计算告警
            if total_time > 120:
                alert(AlertLevel.WARNING, "计算耗时过长", f"总耗时 {total_time:.1f}s 超过阈值", symbols=len(symbols), rows=total_rows)
    
    def _build_symbol_data(self, all_results: Dict[str, list]) -> Dict[str, Dict[str, Any]]:
        """构建按币种聚合的数据结构（保留用于调试）"""
        symbol_data = {}
        for indicator_name, records_list in all_results.items():
            for records in records_list:
                for r in records:
                    symbol = r.get("交易对")
                    interval = r.get("周期")
                    if not symbol or not interval:
                        continue
                    if symbol not in symbol_data:
                        symbol_data[symbol] = {}
                    if interval not in symbol_data[symbol]:
                        symbol_data[symbol][interval] = {}
                    fields = {k: v for k, v in r.items() if k not in ("交易对", "周期")}
                    symbol_data[symbol][interval][indicator_name.replace('.py', '')] = fields
        return symbol_data
    
    def _write_simple_db(self, all_results: Dict[str, list]):
        """写入 market_data.db - 每个指标一张表，全量覆盖"""
        from ..db.reader import writer as sqlite_writer
        import pandas as pd
        
        for indicator_name, records_list in all_results.items():
            if not records_list:
                continue
            # 合并所有记录
            all_records = []
            for records in records_list:
                if isinstance(records, list):
                    all_records.extend(records)
                elif isinstance(records, dict):
                    all_records.append(records)
            
            if all_records:
                df = pd.DataFrame(all_records)
                sqlite_writer.write(indicator_name, df)
        
        # 全局计算：市场占比
        self._update_market_share()
        
        # 清理期货表的1m数据（期货无1m粒度）
        self._cleanup_futures_1m()
    
    def _update_market_share(self):
        """更新期货情绪聚合表的市场占比字段（基于全市场持仓总额）"""
        import sqlite3
        import psycopg
        from ..config import config
        
        try:
            # 1. 从 PostgreSQL 获取全市场各周期持仓总额（只取最新时间点）
            totals = {}
            with psycopg.connect(config.db_url) as conn:
                with conn.cursor() as cur:
                    # 5m 从原始表（取每个币种最新一条）
                    cur.execute("""
                        SELECT SUM(oiv) FROM (
                            SELECT DISTINCT ON (symbol) sum_open_interest_value as oiv
                            FROM market_data.binance_futures_metrics_5m
                            WHERE create_time > NOW() - INTERVAL '1 hour'
                            ORDER BY symbol, create_time DESC
                        ) t
                    """)
                    row = cur.fetchone()
                    if row and row[0]:
                        totals['5m'] = float(row[0])
                    
                    # 其他周期从物化视图（取最新 bucket）
                    for interval in ['15m', '1h', '4h', '1d', '1w']:
                        cur.execute(f"""
                            SELECT SUM(sum_open_interest_value)
                            FROM market_data.binance_futures_metrics_{interval}_last
                            WHERE bucket = (SELECT MAX(bucket) FROM market_data.binance_futures_metrics_{interval}_last)
                        """)
                        row = cur.fetchone()
                        if row and row[0]:
                            totals[interval] = float(row[0])
            
            if not totals:
                return
            
            # 2. 更新 SQLite 市场占比
            sqlite_conn = sqlite3.connect(str(config.sqlite_path))
            for interval, total in totals.items():
                if total > 0:
                    sqlite_conn.execute(f"""
                        UPDATE '期货情绪聚合表.py' 
                        SET 市场占比 = ROUND(CAST(持仓金额 AS REAL) * 100.0 / {total}, 4)
                        WHERE 周期 = ? AND 持仓金额 IS NOT NULL AND 持仓金额 != ''
                    """, (interval,))
            sqlite_conn.commit()
            sqlite_conn.close()
        except Exception:
            pass  # 静默失败
    
    def _cleanup_futures_1m(self):
        """清理期货表的1m数据（期货无1m粒度）"""
        import sqlite3
        from ..config import config
        try:
            conn = sqlite3.connect(str(config.sqlite_path))
            conn.execute("DELETE FROM '期货情绪聚合表.py' WHERE 周期='1m'")
            conn.execute("DELETE FROM '期货情绪元数据.py' WHERE 周期='1m'")
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    def _compute_parallel(
        self,
        task_list: list,
        indicator_names: list,
        indicators: dict,
        futures_cache: dict = None,
        backend: str = "process",
    ) -> Dict[str, list]:
        """并行计算 (backend: thread | process)"""
        batch_size = max(1, len(task_list) // self.max_workers)
        batches = []
        for i in range(0, len(task_list), batch_size):
            batch = task_list[i:i + batch_size]
            batches.append((batch, indicator_names, futures_cache))
        
        all_results = {name: [] for name in indicators}
        
        if backend == "thread":
            executor: Any
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(_compute_batch, batch) for batch in batches]
                for future in as_completed(futures):
                    try:
                        batch_results = future.result()
                        for name, records_list in batch_results.items():
                            all_results[name].extend(records_list)
                    except Exception as e:
                        _compute_errors.inc(1, backend="thread")
                        LOG.error(f"计算失败: {e}")
                        alert(AlertLevel.ERROR, "批次计算失败", str(e), backend="thread")
        else:
            executor = _get_executor(self.max_workers)
            futures = [executor.submit(_compute_batch, batch) for batch in batches]
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    for name, records_list in batch_results.items():
                        all_results[name].extend(records_list)
                except Exception as e:
                    _compute_errors.inc(1, backend="process")
                    LOG.error(f"计算失败: {e}")
                    alert(AlertLevel.ERROR, "批次计算失败", str(e), backend="process")
        
        return all_results
    
    def run_single(self, symbol: str, interval: str, indicator_name: str):
        """单次增量计算 - 走缓存"""
        from ..db.cache import get_cache
        
        ind_cls = get_all_indicators().get(indicator_name)
        if not ind_cls:
            return
        
        indicator = ind_cls()
        cache = get_cache()
        klines = cache.get_klines(interval, symbol)
        if symbol not in klines:
            return
        
        result = indicator.compute(klines[symbol], symbol, interval)
        if result is not None and not result.empty:
            result = trim_dataframe(result)
            writer.write(indicator.meta.name, result, interval)
