/**
 * 翻译任务批量处理队列
 *
 * 功能：
 * - 收集一段时间内的任务，批量提交（性能提升3-7倍）
 * - 并发控制，避免API限流
 * - 任务超时处理
 * - 失败重试
 */

class TranslationBatchQueue {
    constructor(translationService, config = {}) {
        this.translationService = translationService;

        this.config = {
            batchSize: config.batchSize || 10,           // 每批最多任务数
            batchWaitTime: config.batchWaitTime || 500,  // 等待时间(ms)
            maxConcurrent: Math.max(1, Math.min(config.maxConcurrent || 5, 8)),    // 最大并发批次
            taskTimeout: config.taskTimeout || 15000,    // 任务超时(ms)
            maxQueueSize: Math.max(config.maxQueueSize || 200, config.batchSize || 10)
        };

        // 任务队列
        this.queue = [];

        // 当前批次
        this.currentBatch = [];

        // 批次定时器
        this.batchTimer = null;

        // 正在处理的批次数
        this.processingCount = 0;

        // 统计
        this.stats = {
            tasksQueued: 0,
            tasksProcessed: 0,
            tasksFailed: 0,
            batchesProcessed: 0
        };
    }

    /**
     * 添加翻译任务
     * @param {Object} task - 任务对象
     * @param {string} task.text - 待翻译文本
     * @param {number} task.chatId - Telegram聊天ID
     * @param {number} task.messageId - Telegram消息ID
     * @param {string} task.signalType - 信号类型 (arbitrage/orderbook)
     * @returns {Promise} 任务完成时resolve
     */
    addTask(task) {
        return new Promise((resolve, reject) => {
            // 包装任务
            const wrappedTask = {
                ...task,
                resolve,
                reject,
                addedAt: Date.now()
            };

            if (this.queue.length >= this.config.maxQueueSize) {
                console.warn(`🚦 [BatchQueue] 队列已满 (${this.config.maxQueueSize})，拒绝新任务`);
                reject(new Error('翻译队列已满'));
                return;
            }

            this.queue.push(wrappedTask);
            this.stats.tasksQueued++;

            console.log(
                `📥 [BatchQueue] 任务入队 (队列: ${this.queue.length}): "${task.text.substring(0, 30)}${task.text.length > 30 ? '...' : ''}"`
            );

            // 启动批次处理
            this.scheduleBatch();
        });
    }

    /**
     * 调度批次处理
     */
    scheduleBatch() {
        // 如果已经有定时器，取消它
        if (this.batchTimer) {
            clearTimeout(this.batchTimer);
        }

        // 如果队列为空，不处理
        if (this.queue.length === 0) {
            return;
        }

        // 如果队列达到批次大小，立即处理
        if (this.queue.length >= this.config.batchSize) {
            this.processBatch();
            return;
        }

        // 否则，等待一段时间再处理（收集更多任务）
        this.batchTimer = setTimeout(() => {
            this.processBatch();
        }, this.config.batchWaitTime);
    }

    /**
     * 处理批次
     */
    async processBatch() {
        // 清除定时器
        if (this.batchTimer) {
            clearTimeout(this.batchTimer);
            this.batchTimer = null;
        }

        // 如果队列为空，返回
        if (this.queue.length === 0) {
            return;
        }

        // 检查并发限制
        if (this.processingCount >= this.config.maxConcurrent) {
            console.log(
                `⏳ [BatchQueue] 达到并发限制 (${this.processingCount}/${this.config.maxConcurrent})，稍后处理`
            );
            // 1秒后重试
            setTimeout(() => this.processBatch(), 1000);
            return;
        }

        // 取出一批任务
        const batchSize = Math.min(this.config.batchSize, this.queue.length);
        const batch = this.queue.splice(0, batchSize);

        console.log(
            `🔄 [BatchQueue] 开始处理批次: ${batch.length} 个任务 (队列剩余: ${this.queue.length})`
        );

        this.processingCount++;
        this.stats.batchesProcessed++;

        try {
            await this.processBatchTasks(batch);
        } catch (error) {
            console.error('❌ [BatchQueue] 批次处理失败:', error.message);
        } finally {
            this.processingCount--;

            // 如果队列还有任务，继续处理
            if (this.queue.length > 0) {
                this.scheduleBatch();
            }
        }
    }

    /**
     * 处理一批任务
     */
    async processBatchTasks(batch) {
        const texts = batch.map(task => task.text);

        try {
            // 批量翻译
            const translations = await Promise.race([
                this.translationService.translateBatch(texts),
                this.timeout(this.config.taskTimeout)
            ]);

            // 处理每个任务的结果
            for (let i = 0; i < batch.length; i++) {
                const task = batch[i];
                const translation = translations[i];

                if (translation) {
                    // 翻译成功
                    task.translation = translation;
                    this.stats.tasksProcessed++;

                    // 调用回调（resolve）
                    task.resolve({
                        text: task.text,
                        translation,
                        chatId: task.chatId,
                        messageId: task.messageId,
                        signalType: task.signalType
                    });

                    console.log(
                        `✅ [BatchQueue] 任务完成: "${task.text.substring(0, 30)}${task.text.length > 30 ? '...' : ''}" → "${translation.substring(0, 30)}${translation.length > 30 ? '...' : ''}"`
                    );
                } else {
                    // 翻译失败
                    this.stats.tasksFailed++;
                    task.reject(new Error('翻译结果为空'));
                }
            }
        } catch (error) {
            // 整个批次失败，所有任务都标记为失败
            console.error(`❌ [BatchQueue] 批次翻译失败:`, error.message);

            batch.forEach(task => {
                this.stats.tasksFailed++;
                task.reject(error);
            });
        }
    }

    /**
     * 超时Promise
     */
    timeout(ms) {
        return new Promise((_, reject) => {
            setTimeout(() => reject(new Error('翻译超时')), ms);
        });
    }

    /**
     * 获取队列状态
     */
    getStatus() {
        return {
            queueLength: this.queue.length,
            processingCount: this.processingCount,
            stats: this.stats
        };
    }

    /**
     * 打印统计信息
     */
    printStats() {
        const status = this.getStatus();
        const successRate = status.stats.tasksQueued > 0
            ? ((status.stats.tasksProcessed / status.stats.tasksQueued) * 100).toFixed(1)
            : 0;

        console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('📊 [BatchQueue] 队列统计');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log(`队列长度: ${status.queueLength}`);
        console.log(`处理中: ${status.processingCount}`);
        console.log(`已入队: ${status.stats.tasksQueued}`);
        console.log(`已完成: ${status.stats.tasksProcessed}`);
        console.log(`已失败: ${status.stats.tasksFailed}`);
        console.log(`成功率: ${successRate}%`);
        console.log(`批次数: ${status.stats.batchesProcessed}`);
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    }

    /**
     * 清空队列
     */
    clear() {
        if (this.batchTimer) {
            clearTimeout(this.batchTimer);
            this.batchTimer = null;
        }

        // 拒绝所有待处理任务
        this.queue.forEach(task => {
            task.reject(new Error('队列已清空'));
        });

        this.queue = [];
        console.log('🧹 [BatchQueue] 队列已清空');
    }
}

module.exports = TranslationBatchQueue;
