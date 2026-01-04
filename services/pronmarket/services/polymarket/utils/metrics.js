/**
 * 性能指标收集器 - 阶段0埋点
 */

class Metrics {
    constructor() {
        this.timings = {};      // { stage: [durations] }
        this.counters = {};     // { name: count }
        this.startTime = Date.now();
        const rawEvery = Number(process.env.METRICS_LOG_EVERY);
        this.logEvery = Number.isFinite(rawEvery) && rawEvery > 0 ? Math.floor(rawEvery) : 1;
        this.logCounter = 0;
    }

    // 计时开始
    startTimer(stage) {
        return { stage, start: Date.now() };
    }

    // 计时结束并记录
    endTimer(timer) {
        if (!timer) return 0;
        const duration = Date.now() - timer.start;
        if (!this.timings[timer.stage]) this.timings[timer.stage] = [];
        this.timings[timer.stage].push(duration);
        // 保留最近1000条
        if (this.timings[timer.stage].length > 1000) {
            this.timings[timer.stage] = this.timings[timer.stage].slice(-1000);
        }
        return duration;
    }

    // 计数器
    increment(name, delta = 1) {
        this.counters[name] = (this.counters[name] || 0) + delta;
    }

    // 计算百分位
    percentile(arr, p) {
        if (!arr || arr.length === 0) return 0;
        const sorted = [...arr].sort((a, b) => a - b);
        const idx = Math.ceil((p / 100) * sorted.length) - 1;
        return sorted[Math.max(0, idx)];
    }

    // 获取阶段统计
    getStats(stage) {
        const arr = this.timings[stage];
        if (!arr || arr.length === 0) return null;
        return {
            count: arr.length,
            p50: this.percentile(arr, 50),
            p99: this.percentile(arr, 99),
            avg: Math.round(arr.reduce((a, b) => a + b, 0) / arr.length)
        };
    }

    // 获取命中率
    getHitRate(hitKey, totalKey) {
        const hits = this.counters[hitKey] || 0;
        const total = this.counters[totalKey] || 0;
        return total > 0 ? ((hits / total) * 100).toFixed(1) + '%' : 'N/A';
    }

    // 汇总报告
    report() {
        const stages = ['sendSignal', 'enrichMeta', 'format', 'send', 'translate'];
        const report = { uptime: Math.round((Date.now() - this.startTime) / 1000) + 's' };
        
        for (const stage of stages) {
            const stats = this.getStats(stage);
            if (stats) report[stage] = stats;
        }
        
        report.cacheHitRate = this.getHitRate('cache.hit', 'cache.total');
        report.counters = { ...this.counters };
        
        return report;
    }

    // 打印报告
    logReport() {
        return this.logReportWithOptions();
    }

    logReportWithOptions(options = {}) {
        const { force = false } = options;
        if (!force && !this.shouldLog()) {
            return;
        }
        const r = this.report();
        const stages = ['sendSignal', 'enrichMeta', 'format', 'send', 'translate'];
        const parts = [`📊 [Metrics] 运行${r.uptime} 缓存${r.cacheHitRate}`];
        for (const stage of stages) {
            const s = r[stage];
            if (s) parts.push(`${stage}:P50=${s.p50}ms/P99=${s.p99}ms(n=${s.count})`);
        }
        console.log(parts.join(' | '));
    }

    shouldLog() {
        if (this.logEvery <= 1) {
            return true;
        }
        this.logCounter += 1;
        return this.logCounter % this.logEvery === 0;
    }
}

module.exports = new Metrics();
