/**
 * Google Cloud Translation API 服务封装
 *
 * 功能：
 * - 单例模式，连接复用
 * - 支持单条和批量翻译
 * - 自动重试机制
 * - 集成缓存
 * - 详细的错误处理和日志
 */

const { Translate } = require('@google-cloud/translate').v2;
const TranslationCache = require('./cache');

class GoogleTranslationService {
    constructor(config = {}) {
        this.config = {
            projectId: config.projectId || process.env.GOOGLE_CLOUD_PROJECT,
            keyFilename: config.keyFilename || process.env.GOOGLE_APPLICATION_CREDENTIALS,
            timeout: config.timeout || 8000,
            retryAttempts: config.retryAttempts || 3,
            retryDelay: config.retryDelay || 1000,
            sourceLang: config.sourceLang || 'en',
            targetLang: config.targetLang || 'zh-CN'
        };

        // 初始化 Google Translate 客户端（单例）
        this.client = null;
        this.initClient();

        // 初始化缓存
        this.cache = new TranslationCache(config.cache || {});

        // 统计信息
        this.stats = {
            apiCalls: 0,
            successes: 0,
            failures: 0,
            totalChars: 0
        };

        // 错误计数器（用于降级）
        this.consecutiveFailures = 0;
        this.maxConsecutiveFailures = config.maxFailures || 5;
        this.isDisabled = false;
        this.disabledUntil = 0;
        this.recoverAfter = config.recoverAfter || 300000; // 5分钟
    }

    /**
     * 初始化 Google Translate 客户端
     */
    initClient() {
        try {
            const options = {};

            if (this.config.projectId) {
                options.projectId = this.config.projectId;
            }

            if (this.config.keyFilename) {
                options.keyFilename = this.config.keyFilename;
            }

            this.client = new Translate(options);
            console.log('✅ [GoogleTranslate] 客户端初始化成功');
        } catch (error) {
            console.error('❌ [GoogleTranslate] 客户端初始化失败:', error.message);
            this.client = null;
        }
    }

    /**
     * 检查服务是否可用
     */
    isAvailable() {
        // 检查是否被禁用
        if (this.isDisabled) {
            const now = Date.now();
            if (now < this.disabledUntil) {
                return false;
            } else {
                // 恢复服务
                console.log('🔄 [GoogleTranslate] 服务恢复，重置错误计数');
                this.isDisabled = false;
                this.consecutiveFailures = 0;
            }
        }

        return this.client !== null;
    }

    /**
     * 翻译单条文本
     * @param {string} text - 待翻译文本
     * @param {string} from - 源语言（可选）
     * @param {string} to - 目标语言（可选）
     * @returns {Promise<string>} 翻译结果
     */
    async translate(text, from = null, to = null) {
        if (!text || typeof text !== 'string') {
            throw new Error('翻译文本不能为空');
        }

        // 检查服务是否可用
        if (!this.isAvailable()) {
            throw new Error('翻译服务暂时不可用');
        }

        // 检查缓存
        const cached = this.cache.get(text);
        if (cached) {
            return cached;
        }

        const sourceLang = from || this.config.sourceLang;
        const targetLang = to || this.config.targetLang;

        // 调用 API
        try {
            const result = await this.translateWithRetry(text, sourceLang, targetLang);

            // 保存到缓存
            this.cache.set(text, result);

            // 重置错误计数
            this.consecutiveFailures = 0;

            return result;
        } catch (error) {
            this.handleError(error);
            throw error;
        }
    }

    /**
     * 批量翻译
     * @param {Array<string>} texts - 待翻译文本数组
     * @param {string} from - 源语言
     * @param {string} to - 目标语言
     * @returns {Promise<Array<string>>} 翻译结果数组
     */
    async translateBatch(texts, from = null, to = null) {
        if (!Array.isArray(texts) || texts.length === 0) {
            return [];
        }

        // 检查服务是否可用
        if (!this.isAvailable()) {
            throw new Error('翻译服务暂时不可用');
        }

        const sourceLang = from || this.config.sourceLang;
        const targetLang = to || this.config.targetLang;

        // 分离已缓存和未缓存的文本
        const results = new Array(texts.length);
        const toTranslate = [];
        const indices = [];

        texts.forEach((text, index) => {
            const cached = this.cache.get(text);
            if (cached) {
                results[index] = cached;
            } else {
                toTranslate.push(text);
                indices.push(index);
            }
        });

        // 如果都有缓存，直接返回
        if (toTranslate.length === 0) {
            return results;
        }

        console.log(`🔄 [GoogleTranslate] 批量翻译: ${toTranslate.length}/${texts.length} 需要调用API`);

        // 调用批量翻译 API
        try {
            const translations = await this.translateBatchWithRetry(
                toTranslate,
                sourceLang,
                targetLang
            );

            // 填充结果并保存到缓存
            translations.forEach((translation, i) => {
                const originalIndex = indices[i];
                results[originalIndex] = translation;
                this.cache.set(toTranslate[i], translation);
            });

            // 重置错误计数
            this.consecutiveFailures = 0;

            return results;
        } catch (error) {
            this.handleError(error);
            throw error;
        }
    }

    /**
     * 带重试的单条翻译
     */
    async translateWithRetry(text, from, to) {
        let lastError;

        for (let attempt = 1; attempt <= this.config.retryAttempts; attempt++) {
            try {
                const startTime = Date.now();

                const [translation] = await this.client.translate(text, {
                    from,
                    to,
                    timeout: this.config.timeout
                });

                const duration = Date.now() - startTime;

                // 更新统计
                this.stats.apiCalls++;
                this.stats.successes++;
                this.stats.totalChars += text.length;

                console.log(
                    `✅ [GoogleTranslate] 翻译成功 (${duration}ms, ${text.length}字符): "${text.substring(0, 30)}${text.length > 30 ? '...' : ''}"`
                );

                return translation;
            } catch (error) {
                lastError = error;
                console.warn(
                    `⚠️ [GoogleTranslate] 翻译失败 (尝试 ${attempt}/${this.config.retryAttempts}):`,
                    error.message
                );

                // 如果不是最后一次尝试，等待后重试
                if (attempt < this.config.retryAttempts) {
                    await this.sleep(this.config.retryDelay * attempt);
                }
            }
        }

        // 所有重试都失败
        this.stats.apiCalls++;
        this.stats.failures++;
        throw lastError;
    }

    /**
     * 带重试的批量翻译
     */
    async translateBatchWithRetry(texts, from, to) {
        let lastError;

        for (let attempt = 1; attempt <= this.config.retryAttempts; attempt++) {
            try {
                const startTime = Date.now();

                const [translations] = await this.client.translate(texts, {
                    from,
                    to,
                    timeout: this.config.timeout
                });

                const duration = Date.now() - startTime;
                const totalChars = texts.reduce((sum, t) => sum + t.length, 0);

                // 更新统计
                this.stats.apiCalls++;
                this.stats.successes++;
                this.stats.totalChars += totalChars;

                console.log(
                    `✅ [GoogleTranslate] 批量翻译成功 (${duration}ms, ${texts.length}条, ${totalChars}字符)`
                );

                return translations;
            } catch (error) {
                lastError = error;
                console.warn(
                    `⚠️ [GoogleTranslate] 批量翻译失败 (尝试 ${attempt}/${this.config.retryAttempts}):`,
                    error.message
                );

                if (attempt < this.config.retryAttempts) {
                    await this.sleep(this.config.retryDelay * attempt);
                }
            }
        }

        this.stats.apiCalls++;
        this.stats.failures++;
        throw lastError;
    }

    /**
     * 处理错误（降级逻辑）
     */
    handleError(error) {
        this.consecutiveFailures++;

        if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
            this.isDisabled = true;
            this.disabledUntil = Date.now() + this.recoverAfter;

            console.error(
                `🚨 [GoogleTranslate] 连续失败${this.consecutiveFailures}次，服务已禁用${this.recoverAfter / 1000}秒`
            );
        }
    }

    /**
     * 保存缓存到磁盘
     */
    async saveCache() {
        await this.cache.saveToDisk();
    }

    /**
     * 获取统计信息
     */
    getStats() {
        const successRate = this.stats.apiCalls > 0
            ? (this.stats.successes / this.stats.apiCalls * 100).toFixed(1)
            : 0;

        return {
            apiCalls: this.stats.apiCalls,
            successes: this.stats.successes,
            failures: this.stats.failures,
            successRate: `${successRate}%`,
            totalChars: this.stats.totalChars,
            cache: this.cache.getStats(),
            isDisabled: this.isDisabled
        };
    }

    /**
     * 打印统计信息
     */
    printStats() {
        const stats = this.getStats();
        console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('📊 [GoogleTranslate] 统计信息');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log(`API调用: ${stats.apiCalls} (成功率: ${stats.successRate})`);
        console.log(`翻译字符: ${stats.totalChars}`);
        console.log(`服务状态: ${stats.isDisabled ? '🔴 已禁用' : '🟢 正常'}`);
        console.log(`\n缓存统计:`);
        console.log(`  容量: ${stats.cache.size}/${stats.cache.maxSize}`);
        console.log(`  命中率: ${stats.cache.hitRate}`);
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    }

    /**
     * 睡眠函数
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

module.exports = GoogleTranslationService;
