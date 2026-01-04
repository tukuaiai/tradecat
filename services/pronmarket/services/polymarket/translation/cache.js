/**
 * 多级缓存管理器
 *
 * 功能：
 * - L1: 内存缓存 (Map) - 访问延迟 <1ms
 * - L2: 磁盘缓存 (JSON) - 访问延迟 <10ms
 * - 自动持久化和恢复
 * - LRU淘汰策略（超出容量时删除最旧的）
 */

const fs = require('fs').promises;
const path = require('path');

class TranslationCache {
    constructor(config = {}) {
        this.maxSize = config.maxSize || 100000;  // 增加到10万条
        this.persistToDisk = config.persistToDisk !== false;
        this.filePath = config.filePath || path.join(__dirname, '../data/translation-cache.json');

        // L1: 内存缓存
        this.memoryCache = new Map();

        // 统计信息
        this.stats = {
            hits: 0,
            misses: 0,
            saves: 0
        };

        // 启动时加载磁盘缓存
        this.loadFromDisk();
    }

    /**
     * 从磁盘加载缓存
     */
    async loadFromDisk() {
        if (!this.persistToDisk) return;

        try {
            const data = await fs.readFile(this.filePath, 'utf-8');
            const cache = JSON.parse(data);

            // 加载到内存
            Object.entries(cache).forEach(([key, value]) => {
                this.memoryCache.set(key, {
                    translation: value,
                    timestamp: Date.now()
                });
            });

            console.log(`📦 [Cache] 从磁盘加载了 ${this.memoryCache.size} 条缓存`);
        } catch (error) {
            if (error.code !== 'ENOENT') {
                console.error('❌ [Cache] 加载磁盘缓存失败:', error.message);
            }
        }
    }

    /**
     * 保存缓存到磁盘
     */
    async saveToDisk() {
        if (!this.persistToDisk) return;

        try {
            // 确保目录存在
            await fs.mkdir(path.dirname(this.filePath), { recursive: true });

            // 转换为普通对象
            const cache = {};
            this.memoryCache.forEach((value, key) => {
                cache[key] = value.translation;
            });

            await fs.writeFile(this.filePath, JSON.stringify(cache, null, 2), 'utf-8');
            this.stats.saves++;

            console.log(`💾 [Cache] 保存了 ${this.memoryCache.size} 条缓存到磁盘`);
        } catch (error) {
            console.error('❌ [Cache] 保存磁盘缓存失败:', error.message);
        }
    }

    /**
     * 获取缓存
     * @param {string} text - 原文
     * @returns {string|null} 翻译结果，未找到返回null
     */
    get(text) {
        const key = this.normalizeKey(text);
        const cached = this.memoryCache.get(key);

        if (cached) {
            this.stats.hits++;
            // 更新访问时间（LRU）
            cached.timestamp = Date.now();
            return cached.translation;
        }

        this.stats.misses++;
        return null;
    }

    /**
     * 设置缓存
     * @param {string} text - 原文
     * @param {string} translation - 译文
     */
    set(text, translation) {
        const key = this.normalizeKey(text);

        // 检查容量，超出则删除最旧的
        if (this.memoryCache.size >= this.maxSize) {
            this.evictOldest();
        }

        this.memoryCache.set(key, {
            translation,
            timestamp: Date.now()
        });
    }

    /**
     * 批量设置缓存
     * @param {Array<{text: string, translation: string}>} items
     */
    setMany(items) {
        items.forEach(({ text, translation }) => {
            this.set(text, translation);
        });
    }

    /**
     * 淘汰最旧的缓存项（LRU）
     */
    evictOldest() {
        let oldestKey = null;
        let oldestTime = Infinity;

        this.memoryCache.forEach((value, key) => {
            if (value.timestamp < oldestTime) {
                oldestTime = value.timestamp;
                oldestKey = key;
            }
        });

        if (oldestKey) {
            this.memoryCache.delete(oldestKey);
            console.log(`🗑️ [Cache] 淘汰旧缓存: ${oldestKey.substring(0, 30)}...`);
        }
    }

    /**
     * 标准化缓存键（去除多余空格，转小写）
     */
    normalizeKey(text) {
        return text.trim().toLowerCase();
    }

    /**
     * 清空缓存
     */
    clear() {
        this.memoryCache.clear();
        console.log('🧹 [Cache] 已清空所有缓存');
    }

    /**
     * 获取缓存统计
     */
    getStats() {
        const total = this.stats.hits + this.stats.misses;
        const hitRate = total > 0 ? (this.stats.hits / total * 100).toFixed(1) : 0;

        return {
            size: this.memoryCache.size,
            maxSize: this.maxSize,
            hits: this.stats.hits,
            misses: this.stats.misses,
            hitRate: `${hitRate}%`,
            saves: this.stats.saves
        };
    }

    /**
     * 打印缓存统计
     */
    printStats() {
        const stats = this.getStats();
        console.log('📊 [Cache] 统计信息:');
        console.log(`   容量: ${stats.size}/${stats.maxSize}`);
        console.log(`   命中率: ${stats.hitRate} (${stats.hits} hits / ${stats.misses} misses)`);
        console.log(`   持久化次数: ${stats.saves}`);
    }
}

module.exports = TranslationCache;
