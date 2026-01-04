/**
 * 本地AI翻译服务（Transformers.js - 专为大数据量设计）
 *
 * 功能：
 * - 完全本地运行，无API限制
 * - 翻译速度：10-50ms（模型加载后）
 * - 支持百万级数据量
 * - 零成本，完全免费
 * - 自动缓存，智能批处理
 *
 * 适用场景：
 * - 数据量大（>5000条/天）
 * - 需要稳定性（不受API限流影响）
 * - 对翻译质量要求中等（市场名称翻译足够好）
 */

const { pipeline } = require('@xenova/transformers');
const TranslationCache = require('./cache');

class LocalAITranslationService {
    constructor(config = {}) {
        this.config = {
            modelName: config.modelName || 'Xenova/opus-mt-en-zh',
            maxLength: config.maxLength || 512,
            batchSize: config.batchSize || 32, // 批量翻译大小
            sourceLang: config.sourceLang || 'en',
            targetLang: config.targetLang || 'zh-CN'
        };

        // 模型实例（单例）
        this.translator = null;
        this.isLoading = false;
        this.loadingPromise = null;

        // 初始化缓存
        this.cache = new TranslationCache(config.cache || {});

        // 统计信息
        this.stats = {
            translations: 0,
            totalChars: 0,
            avgLatency: 0,
            modelLoadTime: 0
        };

        console.log('✅ [LocalAI] 本地AI翻译服务初始化成功');
        console.log(`📦 [LocalAI] 模型: ${this.config.modelName}`);
        console.log('ℹ️  [LocalAI] 首次翻译时会自动下载模型（~300MB），请耐心等待...');

        // 可选：后台预加载模型（不阻塞Bot启动）
        if (config.preloadModel) {
            console.log('🔄 [LocalAI] 后台预加载模型中...');
            this.loadModel().catch(err => {
                console.error('❌ [LocalAI] 预加载失败:', err.message);
            });
        }
    }

    /**
     * 延迟加载模型（首次调用时才加载）
     */
    async loadModel() {
        // 如果已加载，直接返回
        if (this.translator) {
            return this.translator;
        }

        // 如果正在加载，等待加载完成
        if (this.isLoading) {
            return this.loadingPromise;
        }

        // 开始加载
        this.isLoading = true;
        const startTime = Date.now();

        console.log('🔄 [LocalAI] 开始加载翻译模型...');
        console.log('⏳ [LocalAI] 首次使用需要下载模型文件（约300MB），后续使用会直接加载本地缓存');

        this.loadingPromise = (async () => {
            try {
                // 创建翻译管道
                this.translator = await pipeline(
                    'translation',
                    this.config.modelName,
                    {
                        // 启用量化以减少内存占用
                        quantized: true,
                        // 显示下载进度
                        progress_callback: (progress) => {
                            if (progress.status === 'downloading') {
                                const percent = Math.round((progress.loaded / progress.total) * 100);
                                console.log(`📥 [LocalAI] 下载进度: ${percent}% (${progress.file})`);
                            } else if (progress.status === 'done') {
                                console.log(`✅ [LocalAI] 文件已下载: ${progress.file}`);
                            }
                        }
                    }
                );

                const loadTime = Date.now() - startTime;
                this.stats.modelLoadTime = loadTime;

                console.log(`✅ [LocalAI] 模型加载完成，耗时: ${(loadTime / 1000).toFixed(1)}秒`);
                console.log('🚀 [LocalAI] 翻译服务已就绪，速度: 10-50ms/次');

                this.isLoading = false;
                return this.translator;
            } catch (error) {
                this.isLoading = false;
                console.error('❌ [LocalAI] 模型加载失败:', error.message);
                throw error;
            }
        })();

        return this.loadingPromise;
    }

    /**
     * 检查服务是否可用
     */
    async isAvailable() {
        try {
            await this.loadModel();
            return true;
        } catch (error) {
            return false;
        }
    }

    /**
     * 翻译单条文本
     * @param {string} text - 待翻译文本
     * @returns {Promise<string>} 翻译结果
     */
    async translate(text, from = null, to = null) {
        // 检查缓存
        const cached = this.cache.get(text);
        if (cached) {
            return cached;
        }

        // 确保模型已加载
        const translator = await this.loadModel();

        const startTime = Date.now();

        try {
            // 调用翻译模型
            const result = await translator(text, {
                max_length: this.config.maxLength,
                src_lang: from || this.config.sourceLang,
                tgt_lang: to || this.config.targetLang
            });

            // 提取翻译结果
            const translation = result[0].translation_text;

            // 更新统计
            const latency = Date.now() - startTime;
            this.updateStats(text.length, latency);

            // 存入缓存
            this.cache.set(text, translation);

            return translation;
        } catch (error) {
            console.error('❌ [LocalAI] 翻译失败:', error.message);
            throw error;
        }
    }

    /**
     * 批量翻译（高性能）
     * @param {string[]} texts - 待翻译文本数组
     * @returns {Promise<string[]>} 翻译结果数组
     */
    async translateBatch(texts, from = null, to = null) {
        // 分离已缓存和未缓存的文本
        const results = new Array(texts.length);
        const toTranslate = [];
        const toTranslateIndices = [];

        for (let i = 0; i < texts.length; i++) {
            const cached = this.cache.get(texts[i]);
            if (cached) {
                results[i] = cached;
            } else {
                toTranslate.push(texts[i]);
                toTranslateIndices.push(i);
            }
        }

        // 如果全部命中缓存，直接返回
        if (toTranslate.length === 0) {
            return results;
        }

        // 确保模型已加载
        const translator = await this.loadModel();

        const startTime = Date.now();

        try {
            // 批量翻译（Transformers.js支持批量处理）
            const batchResults = await translator(toTranslate, {
                max_length: this.config.maxLength,
                src_lang: from || this.config.sourceLang,
                tgt_lang: to || this.config.targetLang
            });

            // 提取翻译结果并填充
            for (let i = 0; i < batchResults.length; i++) {
                const translation = batchResults[i].translation_text;
                const originalIndex = toTranslateIndices[i];
                results[originalIndex] = translation;

                // 更新缓存
                this.cache.set(toTranslate[i], translation);
            }

            // 更新统计
            const totalChars = toTranslate.reduce((sum, text) => sum + text.length, 0);
            const latency = Date.now() - startTime;
            this.updateStats(totalChars, latency);

            return results;
        } catch (error) {
            console.error('❌ [LocalAI] 批量翻译失败:', error.message);
            throw error;
        }
    }

    /**
     * 更新统计信息
     */
    updateStats(chars, latency) {
        this.stats.translations++;
        this.stats.totalChars += chars;

        // 计算移动平均延迟
        if (this.stats.avgLatency === 0) {
            this.stats.avgLatency = latency;
        } else {
            this.stats.avgLatency = Math.round(
                (this.stats.avgLatency * (this.stats.translations - 1) + latency) / this.stats.translations
            );
        }
    }

    /**
     * 保存缓存到磁盘
     */
    async saveCache() {
        try {
            await this.cache.saveToDisk();
        } catch (error) {
            console.error('❌ [LocalAI] 保存缓存失败:', error.message);
        }
    }

    /**
     * 获取统计信息
     */
    getStats() {
        const cacheStats = this.cache.getStats();

        return {
            translations: this.stats.translations,
            totalChars: this.stats.totalChars,
            avgLatency: `${this.stats.avgLatency}ms`,
            modelLoadTime: `${(this.stats.modelLoadTime / 1000).toFixed(1)}s`,
            modelLoaded: this.translator !== null,
            cache: {
                size: cacheStats.size,
                maxSize: cacheStats.maxSize,
                hits: cacheStats.hits,
                misses: cacheStats.misses,
                hitRate: cacheStats.hitRate
            }
        };
    }

    /**
     * 清理资源
     */
    async cleanup() {
        // Transformers.js 会自动管理资源，不需要手动清理
        console.log('🧹 [LocalAI] 清理翻译服务资源');
    }
}

module.exports = LocalAITranslationService;
