/**
 * 代理配置模块
 * 为 Telegram Bot 和其他网络请求配置代理
 */

const { HttpsProxyAgent } = require('https-proxy-agent');
const { SocksProxyAgent } = require('socks-proxy-agent');

/**
 * 获取代理配置
 */
function getProxyConfig() {
    // 从环境变量读取代理配置
    const proxy = process.env.HTTPS_PROXY
        || process.env.https_proxy
        || process.env.HTTP_PROXY
        || process.env.http_proxy
        || process.env.PROXY;

    if (!proxy) {
        console.log('⚠️  未配置代理,可能无法访问 Telegram API');
        return null;
    }

    console.log(`✅ 检测到代理配置: ${proxy}`);
    return proxy;
}

/**
 * 创建 HTTP/HTTPS 代理 Agent
 */
function createHttpProxyAgent(proxyUrl) {
    if (!proxyUrl) {
        proxyUrl = getProxyConfig();
    }

    if (!proxyUrl) {
        return null;
    }

    try {
        // 支持 socks5://
        if (proxyUrl.startsWith('socks')) {
            console.log('✅ 使用 SOCKS 代理');
            return new SocksProxyAgent(proxyUrl);
        }

        // 支持 http:// 和 https://
        console.log('✅ 使用 HTTP 代理');
        return new HttpsProxyAgent(proxyUrl);
    } catch (error) {
        console.error('❌ 创建代理 Agent 失败:', error.message);
        return null;
    }
}

/**
 * 为 Telegram Bot 配置代理
 */
function getTelegramBotOptions() {
    const proxyUrl = getProxyConfig();

    if (!proxyUrl) {
        return {
            polling: true
        };
    }

    // Telegram polling 必须走代理，避免直连被阻断
    if (proxyUrl.startsWith('socks')) {
        return {
            polling: true,
            request: {
                agentClass: SocksProxyAgent,
                agentOptions: proxyUrl
            }
        };
    }

    return {
        polling: true,
        request: {
            proxy: proxyUrl
        }
    };
}

/**
 * 为 fetch/axios 配置代理
 */
function getFetchProxyOptions() {
    const agent = createHttpProxyAgent();

    if (!agent) {
        return {};
    }

    return {
        agent: agent,
        timeout: 30000
    };
}

/**
 * 测试代理连接
 */
async function testProxyConnection() {
    const https = require('https');
    const http = require('http');
    const proxyUrl = getProxyConfig();

    if (!proxyUrl) {
        console.log('⚠️  无代理配置,跳过测试');
        return { success: false, message: '无代理配置' };
    }

    return new Promise((resolve) => {
        const agent = createHttpProxyAgent(proxyUrl);

        const options = {
            hostname: 'api.telegram.org',
            port: 443,
            path: '/bot',
            method: 'GET',
            agent: agent,
            timeout: 10000
        };

        const req = https.request(options, (res) => {
            console.log(`✅ 代理连接测试成功 (状态码: ${res.statusCode})`);
            resolve({ success: true, statusCode: res.statusCode });
        });

        req.on('error', (error) => {
            console.error('❌ 代理连接测试失败:', error.message);
            resolve({ success: false, error: error.message });
        });

        req.on('timeout', () => {
            console.error('❌ 代理连接超时');
            req.destroy();
            resolve({ success: false, error: '连接超时' });
        });

        req.end();
    });
}

/**
 * 为 WebSocket 配置代理
 */
function getWebSocketProxyOptions() {
    const proxyUrl = getProxyConfig();

    if (!proxyUrl) {
        return {};
    }

    const agent = createHttpProxyAgent(proxyUrl);

    return {
        agent: agent,
        headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    };
}

module.exports = {
    getProxyConfig,
    createHttpProxyAgent,
    getTelegramBotOptions,
    getFetchProxyOptions,
    getWebSocketProxyOptions,
    testProxyConnection
};
