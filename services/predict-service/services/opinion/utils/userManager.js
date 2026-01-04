/**
 * 用户管理器
 *
 * 功能：
 * - 记录所有使用bot的用户
 * - 管理用户订阅状态
 * - 持久化用户数据
 */

const fs = require('fs');
const path = require('path');
const fsPromises = fs.promises;
// [Security Fix] 阈值配置统一 - 从 settings.js 读取，避免重复定义
const settings = require('../config/settings');

class UserManager {
    constructor(dataFile = null) {
        // 用户数据存储路径
        this.dataFile = dataFile || path.join(__dirname, '../data/users.json');

        // 用户列表：Map<chatId, userInfo>
        this.users = new Map();

        // 异步持久化控制（避免同步I/O阻塞）
        this.saveDebounceMs = 600; // 写盘节流窗口，毫秒
        this.saveTimer = null;     // setTimeout 标识
        this.pendingUserSnapshot = null; // 等待写入的用户快照
        this.writeQueue = Promise.resolve(); // 串行化写盘任务
        this.debug = process.env.DEBUG === 'true';

        // 加载已保存的用户数据
        this.loadUsers();

        console.log('✅ 用户管理器初始化完成');
    }

    /**
     * 注册新用户（或更新现有用户）
     */
    registerUser(chatId, userInfo = {}) {
        const now = Date.now();

        const profile = this.normalizeUserInfo(userInfo);

        if (this.users.has(chatId)) {
            const existing = this.users.get(chatId);
            const updated = {
                ...existing,
                ...profile,
                lastActive: now,
                visitCount: (existing.visitCount || 0) + 1
            };

            const shouldPersist = this.hasMeaningfulChange(existing, updated);
            this.users.set(chatId, updated);

            if (this.debug) {
                console.debug(`🔄 用户活跃: ${chatId} (访问${updated.visitCount}次)`);
            }

            if (shouldPersist) {
                this.saveUsers();
            }
        } else {
            const newUser = {
                chatId: chatId,
                subscribed: true,
                notifications: {
                    arbitrage: true,
                    orderbook: true,
                    closing: true,
                    whale: true,
                    priceSpike: true,
                    newMarket: false
                },
                thresholds: {
                    arbitrage: 1,
                    orderbook: 1,
                    closing: 1,
                    priceSpike: 1,
                    whale: 1,
                    largeTrade: 1,
                    smartMoney: 1
                },
                displayMode: 'detailed',  // 'detailed' | 'compact'
                lang: 'en',  // 'zh-CN' | 'en'
                registeredAt: now,
                lastActive: now,
                visitCount: 1,
                username: profile.username,
                firstName: profile.firstName,
                lastName: profile.lastName
            };

            this.users.set(chatId, newUser);

            if (this.debug) {
                console.debug(`✅ 新用户注册: ${chatId}${profile.username ? ' (@' + profile.username + ')' : ''}`);
            }

            this.saveUsers();
        }

        return this.users.get(chatId);
    }

    /**
     * 订阅
     */
    subscribe(chatId) {
        if (!this.users.has(chatId)) {
            this.registerUser(chatId);
        }

        const user = this.users.get(chatId);
        if (!user.subscribed) {
            user.subscribed = true;
            user.lastActive = Date.now();
            this.saveUsers();

            if (this.debug) {
                console.debug(`✅ 用户订阅: ${chatId}`);
            }
        }

        user.lastActive = Date.now();

        return true;
    }

    /**
     * 取消订阅
     */
    unsubscribe(chatId) {
        if (!this.users.has(chatId)) {
            return false;
        }

        const user = this.users.get(chatId);
        if (user.subscribed) {
            user.subscribed = false;
            user.lastActive = Date.now();
            this.saveUsers();

            if (this.debug) {
                console.debug(`❌ 用户取消订阅: ${chatId}`);
            }
        }

        user.lastActive = Date.now();

        return true;
    }

    /**
     * 检查用户是否已订阅
     */
    isSubscribed(chatId) {
        const user = this.users.get(chatId);
        return user ? user.subscribed : false;
    }

    /**
     * 获取所有已订阅用户的chatId列表
     */
    getSubscribedUsers() {
        const subscribedUsers = [];
        for (const [chatId, user] of this.users.entries()) {
            if (user.subscribed) {
                subscribedUsers.push(chatId);
            }
        }
        return subscribedUsers;
    }

    /**
     * 获取用户信息
     */
    getUserInfo(chatId) {
        return this.users.get(chatId) || null;
    }

    /**
     * 获取用户语言
     */
    getLang(chatId) {
        const user = this.users.get(chatId);
        const lang = user?.lang;
        return ['zh-CN', 'en'].includes(lang) ? lang : 'zh-CN';
    }

    /**
     * 设置用户语言
     */
    setLang(chatId, lang) {
        // 白名单校验
        const validLang = ['zh-CN', 'en'].includes(lang) ? lang : 'zh-CN';
        
        if (!this.users.has(chatId)) {
            this.registerUser(chatId);
        }
        const user = this.users.get(chatId);
        if (user.lang !== validLang) {
            user.lang = validLang;
            user.lastActive = Date.now();
            this.saveUsers();
        }
        return user;
    }

    /**
     * 获取统计信息
     */
    getStats() {
        const total = this.users.size;
        const subscribed = this.getSubscribedUsers().length;
        const unsubscribed = total - subscribed;

        return {
            total,
            subscribed,
            unsubscribed
        };
    }

    /**
     * 从文件加载用户数据
     */
    loadUsers() {
        try {
            // 确保目录存在
            const dir = path.dirname(this.dataFile);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }

            // 加载数据
            if (fs.existsSync(this.dataFile)) {
                const data = fs.readFileSync(this.dataFile, 'utf8');
                const usersArray = JSON.parse(data);

                // 转换为Map，补上缺失的 displayMode/lang 字段
                this.users = new Map(usersArray.map(user => {
                    if (!user.displayMode) user.displayMode = 'detailed';
                    if (!user.lang) user.lang = 'zh-CN';
                    return [user.chatId, user];
                }));

                console.log(`📂 已加载 ${this.users.size} 个用户`);
            } else {
                console.log('📂 未找到用户数据文件，从空开始');
            }
        } catch (error) {
            console.error('❌ 加载用户数据失败:', error.message);
            this.users = new Map();
        }
    }

    /**
     * 保存用户数据到文件
     */
    saveUsers() {
        try {
            // 更新待写入快照
            this.pendingUserSnapshot = Array.from(this.users.values());

            // 已有定时器则只更新快照
            if (this.saveTimer) {
                return;
            }

            this.saveTimer = setTimeout(() => {
                this.saveTimer = null;

                const snapshot = this.pendingUserSnapshot || Array.from(this.users.values());
                this.pendingUserSnapshot = null;

                if (!snapshot) {
                    return;
                }

                this.enqueueUserWrite(snapshot);
            }, this.saveDebounceMs);
        } catch (error) {
            console.error('❌ 保存用户数据失败:', error.message);
        }
    }

    enqueueUserWrite(snapshot) {
        const payload = JSON.stringify(snapshot, null, 2);

        this.writeQueue = this.writeQueue
            .then(() => this.writeUserPayload(payload))
            .catch(() => {});
    }

    async writeUserPayload(payload) {
        try {
            const dir = path.dirname(this.dataFile);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }

            await fsPromises.writeFile(this.dataFile, payload, 'utf8');
        } catch (error) {
            console.error('❌ 保存用户数据失败:', error.message);
        }
    }

    async flushPendingWrites() {
        if (this.saveTimer) {
            clearTimeout(this.saveTimer);
            this.saveTimer = null;
        }

        const snapshot = this.pendingUserSnapshot || Array.from(this.users.values());
        this.pendingUserSnapshot = null;

        this.enqueueUserWrite(snapshot);

        await this.writeQueue;
    }

    /**
     * 移除用户
     */
    removeUser(chatId) {
        if (this.users.has(chatId)) {
            this.users.delete(chatId);
            this.saveUsers();
            if (this.debug) {
                console.debug(`🗑️ 用户已移除: ${chatId}`);
            }
            return true;
        }
        return false;
    }

    /**
     * 切换通知类型（套利/订单簿/扫尾盘）
     */
    toggleNotification(chatId, type) {
        if (!this.users.has(chatId)) {
            return false;
        }

        const user = this.users.get(chatId);

        // 确保notifications对象存在
        if (!user.notifications) {
            user.notifications = {
                arbitrage: true,
                orderbook: true,
                closing: true,
                whale: true,
                priceSpike: true,
                newMarket: false
            };
        } else {
            let changed = false;
            if (user.notifications.arbitrage === undefined) {
                user.notifications.arbitrage = true;
                changed = true;
            }
            if (user.notifications.orderbook === undefined) {
                user.notifications.orderbook = true;
                changed = true;
            }
            if (user.notifications.closing === undefined) {
                user.notifications.closing = true;
                changed = true;
            }
            if (user.notifications.whale === undefined) {
                user.notifications.whale = true;
                changed = true;
            }
            if (user.notifications.priceSpike === undefined) {
                user.notifications.priceSpike = true;
                changed = true;
            }
            if (user.notifications.newMarket === undefined) {
                user.notifications.newMarket = true;
                changed = true;
            }
            if (user.notifications.largeTrade === undefined) {
                user.notifications.largeTrade = true;
                changed = true;
            }
            if (user.notifications.smartMoney === undefined) {
                user.notifications.smartMoney = true;
                changed = true;
            }
            if (changed) {
                this.saveUsers();
            }
        }

        // 切换指定类型的通知
        if (type === 'arbitrage' || type === 'orderbook' || type === 'closing' || type === 'whale' || type === 'priceSpike' || type === 'newMarket' || type === 'largeTrade' || type === 'smartMoney') {
            user.notifications[type] = !user.notifications[type];
            this.saveUsers();
            if (this.debug) {
                console.debug(`🔔 用户 ${chatId} ${type} 通知: ${user.notifications[type] ? '开启' : '关闭'}`);
            }
            return true;
        }

        return false;
    }

    /**
     * 获取用户的通知偏好
     */
    getNotificationSettings(chatId) {
        const user = this.users.get(chatId);
        if (!user) {
            return null;
        }

        // 兼容旧用户数据
        if (!user.notifications) {
            user.notifications = {
                arbitrage: true,
                orderbook: true,
                closing: true,
                whale: true,
                priceSpike: true,
                newMarket: false,
                largeTrade: true,
                smartMoney: true
            };
            this.saveUsers();
        } else {
            let changed = false;
            if (user.notifications.arbitrage === undefined) {
                user.notifications.arbitrage = true;
                changed = true;
            }
            if (user.notifications.orderbook === undefined) {
                user.notifications.orderbook = true;
                changed = true;
            }
            if (user.notifications.closing === undefined) {
                user.notifications.closing = true;
                changed = true;
            }
            if (user.notifications.whale === undefined) {
                user.notifications.whale = true;
                changed = true;
            }
            if (user.notifications.priceSpike === undefined) {
                user.notifications.priceSpike = true;
                changed = true;
            }
            if (user.notifications.newMarket === undefined) {
                user.notifications.newMarket = true;
                changed = true;
            }
            if (user.notifications.largeTrade === undefined) {
                user.notifications.largeTrade = true;
                changed = true;
            }
            if (user.notifications.smartMoney === undefined) {
                user.notifications.smartMoney = true;
                changed = true;
            }
            if (changed) {
                this.saveUsers();
            }
        }

        return user.notifications;
    }

    /**
     * 检查用户是否启用了特定类型的通知
     */
    isNotificationEnabled(chatId, type) {
        const settings = this.getNotificationSettings(chatId);
        if (!settings) {
            return false; // 用户不存在，不发送
        }
        return settings[type] === true;
    }

    /**
     * 设置用户的阈值档位
     * @param {string} chatId - 用户ID
     * @param {string} type - 信号类型 ('arbitrage' | 'orderbook' | 'closing')
     * @param {number} level - 档位 (1=宽松, 2=中等, 3=严格)
     */
    setThreshold(chatId, type, level) {
        const user = this.users.get(chatId);
        if (!user) {
            if (this.debug) {
                console.debug(`❌ 用户不存在: ${chatId}`);
            }
            return false;
        }

        // 确保thresholds对象存在
        if (!user.thresholds) {
            user.thresholds = {
                arbitrage: 1,
                orderbook: 1,
                closing: 1,
                priceSpike: 1,
                whale: 1,
                largeTrade: 1,
                smartMoney: 1
            };
        } else {
            let changed = false;
            if (user.thresholds.arbitrage === undefined) {
                user.thresholds.arbitrage = 1;
                changed = true;
            }
            if (user.thresholds.orderbook === undefined) {
                user.thresholds.orderbook = 1;
                changed = true;
            }
            if (user.thresholds.closing === undefined) {
                user.thresholds.closing = 1;
                changed = true;
            }
            if (user.thresholds.priceSpike === undefined) {
                user.thresholds.priceSpike = 1;
                changed = true;
            }
            if (user.thresholds.whale === undefined) {
                user.thresholds.whale = 1;
                changed = true;
            }
            if (user.thresholds.largeTrade === undefined) {
                user.thresholds.largeTrade = 1;
                changed = true;
            }
            if (user.thresholds.smartMoney === undefined) {
                user.thresholds.smartMoney = 1;
                changed = true;
            }
            if (changed) {
                this.saveUsers();
            }
        }

        // 验证档位参数
        if (![1, 2, 3].includes(level)) {
            if (this.debug) {
                console.debug(`❌ 无效的阈值档位: ${level}`);
            }
            return false;
        }

        // 验证类型参数
        const allowedTypes = ['arbitrage', 'orderbook', 'closing', 'priceSpike', 'whale', 'largeTrade', 'smartMoney'];
        if (!allowedTypes.includes(type)) {
            if (this.debug) {
                console.debug(`❌ 无效的信号类型: ${type}`);
            }
            return false;
        }

        // 设置阈值
        if (user.thresholds[type] !== level) {
            user.thresholds[type] = level;
            this.saveUsers();

            if (this.debug) {
                const levelNames = { 1: '🟢 宽松', 2: '🟡 中等', 3: '🔴 严格' };
                console.debug(`🎚️ 用户 ${chatId} ${type} 阈值设为: ${levelNames[level]}`);
            }
        }
        return true;
    }

    /**
     * 获取用户的阈值档位
     * @param {string} chatId - 用户ID
     * @param {string} type - 信号类型 ('arbitrage' 或 'orderbook')
     * @returns {number} 档位 (1/2/3)，默认返回1
     */
    getThreshold(chatId, type) {
        const user = this.users.get(chatId);
        if (!user) {
            return 1; // 用户不存在，返回默认宽松档位（可接收所有信号）
        }

        // 兼容旧用户数据
        if (!user.thresholds) {
            user.thresholds = {
                arbitrage: 1,
                orderbook: 1,
                closing: 1,
                priceSpike: 1,
                whale: 1
            };
            this.saveUsers();
        } else {
            let changed = false;
            if (user.thresholds.arbitrage === undefined) {
                user.thresholds.arbitrage = 1;
                changed = true;
            }
            if (user.thresholds.orderbook === undefined) {
                user.thresholds.orderbook = 1;
                changed = true;
            }
            if (user.thresholds.closing === undefined) {
                user.thresholds.closing = 1;
                changed = true;
            }
            if (user.thresholds.priceSpike === undefined) {
                user.thresholds.priceSpike = 1;
                changed = true;
            }
            if (user.thresholds.whale === undefined) {
                user.thresholds.whale = 1;
                changed = true;
            }
            if (user.thresholds.largeTrade === undefined) {
                user.thresholds.largeTrade = 2;
                changed = true;
            }
            if (user.thresholds.newMarket === undefined) {
                user.thresholds.newMarket = 1;
                changed = true;
            }
            if (user.thresholds.smartMoney === undefined) {
                user.thresholds.smartMoney = 2;
                changed = true;
            }
            if (changed) {
                this.saveUsers();
            }
        }

        return user.thresholds[type] || 1;
    }

    /**
     * 获取用户显示模式
     */
    getDisplayMode(chatId) {
        const user = this.users.get(chatId);
        return user?.displayMode || 'detailed';
    }

    /**
     * 设置用户显示模式
     */
    setDisplayMode(chatId, mode) {
        const user = this.users.get(chatId);
        if (user) {
            user.displayMode = mode;
            this.saveUsers();
        }
    }

    /**
     * 切换用户显示模式
     */
    toggleDisplayMode(chatId) {
        const current = this.getDisplayMode(chatId);
        const newMode = current === 'detailed' ? 'compact' : 'detailed';
        this.setDisplayMode(chatId, newMode);
        return newMode;
    }

    /**
     * 检查套利信号是否符合用户的阈值要求
     * @param {object} signal - 套利信号对象
     * @param {number} userLevel - 用户的阈值档位 (1/2/3)
     * @returns {boolean} 是否通过阈值检查
     */
    checkArbitrageThreshold(signal, userLevel) {
        // 阈值配置
        const thresholds = {
            1: 2.0,   // 档位1: 净利润 ≥ 2%
            2: 4.0,   // 档位2: 净利润 ≥ 4%
            3: 8.0    // 档位3: 净利润 ≥ 8%
        };

        // 从信号中提取净利润百分比
        let netProfit = 0;
        if (signal.netProfitPercent !== undefined) {
            netProfit = parseFloat(signal.netProfitPercent);
        } else if (signal.netProfit !== undefined) {
            // 如果只有净利润金额，尝试计算百分比
            const invested = parseFloat(signal.buyPrice) || 1;
            netProfit = (parseFloat(signal.netProfit) / invested) * 100;
        }

        const threshold = thresholds[userLevel] || thresholds[1];
        const pass = netProfit >= threshold;

        if (!pass) {
            console.log(`⏭️ 套利信号未达档位${userLevel}阈值: ${netProfit.toFixed(2)}% < ${threshold}%`);
        }

        return pass;
    }

    /**
     * 检查订单簿信号是否符合用户的阈值要求
     * @param {object} signal - 订单簿信号对象
     * @param {number} userLevel - 用户的阈值档位 (1/2/3)
     * @returns {boolean} 是否通过阈值检查
     */
    checkOrderbookThreshold(signal, userLevel) {
        // 阈值配置
        const thresholds = {
            1: { minImbalance: 3.0, minLiquidity: 20000 },    // 档位1: 3倍 + $20K
            2: { minImbalance: 6.0, minLiquidity: 100000 },   // 档位2: 6倍 + $100K
            3: { minImbalance: 12.0, minLiquidity: 200000 }   // 档位3: 12倍 + $200K
        };

        // 从信号中提取失衡倍数
        const imbalance = parseFloat(signal.imbalance) || 0;

        // 从信号中提取流动性（买方+卖方）
        const buyDepth = this.parseAmountString(signal.buyDepth || signal.buyAmount || '0');
        const sellDepth = this.parseAmountString(signal.sellDepth || signal.sellAmount || '0');
        const totalLiquidity = buyDepth + sellDepth;

        const threshold = thresholds[userLevel] || thresholds[1];

        // 必须同时满足失衡和流动性两个条件
        const passImbalance = imbalance >= threshold.minImbalance;
        const passLiquidity = totalLiquidity >= threshold.minLiquidity;
        const pass = passImbalance && passLiquidity;

        if (!pass) {
            console.log(`⏭️ 订单簿信号未达档位${userLevel}阈值: ` +
                `失衡${imbalance.toFixed(1)}x ${passImbalance ? '✓' : '✗ (需' + threshold.minImbalance + 'x)'}, ` +
                `流动性$${(totalLiquidity / 1000).toFixed(0)}K ${passLiquidity ? '✓' : '✗ (需$' + (threshold.minLiquidity / 1000) + 'K)'}`);
        }

        return pass;
    }

    /**
     * 检查扫尾盘信号是否符合用户的阈值要求
     * @param {object} signal - 扫尾盘信号对象
     * @param {number} userLevel - 用户档位 (1/2/3)
     * @returns {boolean}
     */
    checkClosingThreshold(signal, userLevel) {
        if (!signal || !Array.isArray(signal.markets)) {
            return false;
        }

        // 空列表直接跳过，不推送
        if (signal.markets.length === 0) {
            return false;
        }

        const rank = signal.maxConfidenceRank || 0;

        if (userLevel <= 1) {
            return true;
        }

        if (userLevel === 2) {
            const pass = rank >= 2;
            if (!pass) {
                console.log('⏭️ 扫尾盘信号未达档位2阈值：需至少中等置信度');
            }
            return pass;
        }

        const pass = rank >= 3;
        if (!pass) {
            console.log('⏭️ 扫尾盘信号未达档位3阈值：需高置信度市场');
        }
        return pass;
    }

    normalizeUserInfo(userInfo = {}) {
        return {
            username: userInfo.username || null,
            firstName: userInfo.first_name || userInfo.firstName || null,
            lastName: userInfo.last_name || userInfo.lastName || null
        };
    }

    hasMeaningfulChange(previous, next) {
        if (!previous) {
            return true;
        }

        if (previous.subscribed !== next.subscribed) {
            return true;
        }

        if (!this.shallowEqual(previous.notifications, next.notifications)) {
            return true;
        }

        if (!this.shallowEqual(previous.thresholds, next.thresholds)) {
            return true;
        }

        if ((previous.username || null) !== (next.username || null)) {
            return true;
        }

        if ((previous.firstName || null) !== (next.firstName || null)) {
            return true;
        }

        if ((previous.lastName || null) !== (next.lastName || null)) {
            return true;
        }

        return false;
    }

    shallowEqual(a = {}, b = {}) {
        const keysA = Object.keys(a || {});
        const keysB = Object.keys(b || {});

        if (keysA.length !== keysB.length) {
            return false;
        }

        for (const key of keysA) {
            if ((a[key] || null) !== (b[key] || null)) {
                return false;
            }
        }

        return true;
    }

    /**
     * 解析金额字符串（支持 $1K, $2.5M 等格式）
     * @param {string|number} amountStr - 金额字符串或数字
     * @returns {number} 解析后的数字
     */
    parseAmountString(amountStr) {
        if (typeof amountStr === 'number') {
            return amountStr;
        }

        if (typeof amountStr !== 'string') {
            return 0;
        }

        // 移除 $ 符号和空格
        let str = amountStr.replace(/[\$\s]/g, '');

        // 处理 K (千) 和 M (百万)
        if (str.endsWith('K')) {
            return parseFloat(str.slice(0, -1)) * 1000;
        } else if (str.endsWith('M')) {
            return parseFloat(str.slice(0, -1)) * 1000000;
        } else {
            return parseFloat(str) || 0;
        }
    }

    /**
     * 统一检查信号是否符合用户阈值（自动判断信号类型）
     * @param {object} signal - 信号对象
     * @param {string} moduleName - 模块名称 ('arbitrage' 或 'orderbook')
     * @param {number} userLevel - 用户的阈值档位
     * @returns {boolean} 是否通过阈值检查
     */
    checkSignalThreshold(signal, moduleName, userLevel) {
        if (moduleName === 'arbitrage') {
            return this.checkArbitrageThreshold(signal, userLevel);
        } else if (moduleName === 'orderbook') {
            return this.checkOrderbookThreshold(signal, userLevel);
        } else if (moduleName === 'closing') {
            return this.checkClosingThreshold(signal, userLevel);
        } else if (moduleName === 'priceSpike') {
            return this.checkPriceSpikeThreshold(signal, userLevel);
        } else if (moduleName === 'whale') {
            return this.checkWhaleThreshold(signal, userLevel);
        } else if (moduleName === 'largeTrade') {
            return this.checkLargeTradeThreshold(signal, userLevel);
        } else if (moduleName === 'newMarket') {
            return true; // 新市场无阈值，始终通过
        } else if (moduleName === 'smartMoney') {
            return this.checkSmartMoneyThreshold(signal, userLevel);
        } else {
            console.log(`⚠️ 未知的模块类型: ${moduleName}`);
            return true; // 未知类型默认通过
        }
    }

    /**
     * 获取用户的阈值设置摘要
     * @param {string} chatId - 用户ID
     * @returns {object} 阈值设置摘要
     */
    getThresholdSummary(chatId) {
        const user = this.users.get(chatId);
        if (!user) {
            return null;
        }

        // 确保thresholds存在
        if (!user.thresholds) {
            user.thresholds = { arbitrage: 1, orderbook: 1, closing: 1, priceSpike: 1, whale: 1, largeTrade: 2, newMarket: 1, smartMoney: 2 };
            this.saveUsers();
        } else {
            let changed = false;
            if (user.thresholds.priceSpike === undefined) { user.thresholds.priceSpike = 1; changed = true; }
            if (user.thresholds.whale === undefined) { user.thresholds.whale = 1; changed = true; }
            if (user.thresholds.largeTrade === undefined) { user.thresholds.largeTrade = 2; changed = true; }
            if (user.thresholds.newMarket === undefined) { user.thresholds.newMarket = 1; changed = true; }
            if (user.thresholds.smartMoney === undefined) { user.thresholds.smartMoney = 2; changed = true; }
            if (changed) this.saveUsers();
        }

        const levelNames = {
            1: { icon: '🟢', name: '宽松' },
            2: { icon: '🟡', name: '中等' },
            3: { icon: '🔴', name: '严格' }
        };

        const arbitrageLevel = user.thresholds.arbitrage;
        const orderbookLevel = user.thresholds.orderbook;
        const closingLevel = user.thresholds.closing || 1;
        const priceSpikeLevel = user.thresholds.priceSpike || 1;
        const whaleLevel = user.thresholds.whale || 1;
        const largeTradeLevel = user.thresholds.largeTrade || 2;
        const newMarketLevel = user.thresholds.newMarket || 1;
        const smartMoneyLevel = user.thresholds.smartMoney || 2;

        return {
            arbitrage: {
                level: arbitrageLevel,
                icon: levelNames[arbitrageLevel].icon,
                name: levelNames[arbitrageLevel].name,
                threshold: [2.0, 4.0, 8.0][arbitrageLevel - 1] + '%'
            },
            orderbook: {
                level: orderbookLevel,
                icon: levelNames[orderbookLevel].icon,
                name: levelNames[orderbookLevel].name,
                threshold: ['3x + $20K', '6x + $100K', '12x + $200K'][orderbookLevel - 1]
            },
            closing: {
                level: closingLevel,
                icon: levelNames[closingLevel].icon,
                name: levelNames[closingLevel].name,
                threshold: ['全部市场', '仅中/高置信度', '仅高置信度'][closingLevel - 1]
            },
            priceSpike: {
                level: priceSpikeLevel,
                icon: levelNames[priceSpikeLevel].icon,
                name: levelNames[priceSpikeLevel].name,
                threshold: ['3%Δ', '5%Δ', '8%Δ'][priceSpikeLevel - 1]
            },
            whale: {
                level: whaleLevel,
                icon: levelNames[whaleLevel].icon,
                name: levelNames[whaleLevel].name,
                threshold: ['$10K', '$25K', '$50K'][whaleLevel - 1]
            },
            largeTrade: {
                level: largeTradeLevel,
                icon: levelNames[largeTradeLevel].icon,
                name: levelNames[largeTradeLevel].name,
                threshold: ['$2K', '$5K', '$10K'][largeTradeLevel - 1]
            },
            newMarket: {
                level: newMarketLevel,
                icon: '',
                name: '',
                threshold: ''
            },
            smartMoney: {
                level: smartMoneyLevel,
                icon: levelNames[smartMoneyLevel].icon,
                name: levelNames[smartMoneyLevel].name,
                threshold: ['$100', '$500', '$2K'][smartMoneyLevel - 1]
            }
        };
    }

    checkPriceSpikeThreshold(signal, userLevel) {
        const thresholds = { 1: 0.03, 2: 0.05, 3: 0.08 }; // 3%、5%、8%
        const change = typeof signal.change === 'number' ? signal.change : parseFloat(signal.change);
        if (!Number.isFinite(change)) return true;
        const min = thresholds[userLevel] || thresholds[1];
        return change >= min;
    }

    checkWhaleThreshold(signal, userLevel) {
        const thresholds = { 1: 10000, 2: 25000, 3: 50000 };
        const value = typeof signal.value === 'number' ? signal.value : parseFloat(signal.value);
        if (!Number.isFinite(value)) return true;
        const min = thresholds[userLevel] || thresholds[1];
        return value >= min;
    }

    // [Security Fix] 阈值配置统一 - 从 settings.js 读取
    checkLargeTradeThreshold(signal, userLevel) {
        const thresholds = settings.largeTrade?.thresholds || { 1: 2000, 2: 5000, 3: 10000 };
        const value = typeof signal.value === 'number' ? signal.value : parseFloat(signal.value);
        if (!Number.isFinite(value)) return true;
        const min = thresholds[userLevel] || thresholds[2];
        return value >= min;
    }

    // [Security Fix] 阈值配置统一 - 从 settings.js 读取
    checkSmartMoneyThreshold(signal, userLevel) {
        const thresholds = settings.smartMoney?.thresholds || { 1: 100, 2: 500, 3: 2000 };
        const value = typeof signal.value === 'number' ? signal.value : parseFloat(signal.value);
        if (!Number.isFinite(value)) return true;
        const min = thresholds[userLevel] || thresholds[2];
        return value >= min;
    }
}

module.exports = UserManager;
