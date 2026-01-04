/**
 * 代理配置
 */

const { HttpsProxyAgent } = require('https-proxy-agent');

function getProxyAgent() {
  const proxyUrl = process.env.HTTPS_PROXY || process.env.HTTP_PROXY;
  if (proxyUrl) {
    return new HttpsProxyAgent(proxyUrl);
  }
  return undefined;
}

module.exports = { getProxyAgent };
