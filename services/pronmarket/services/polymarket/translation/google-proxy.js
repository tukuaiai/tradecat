/**
 * Google 翻译 - 支持代理版本
 * 直接调用 Google Translate API，支持 HTTP 代理
 */

const https = require('https');
const { HttpsProxyAgent } = require('https-proxy-agent');

class GoogleTranslateProxy {
  constructor(proxyUrl = null) {
    this.proxyUrl = proxyUrl || process.env.HTTPS_PROXY || process.env.HTTP_PROXY;
    if (this.proxyUrl) {
      this.agent = new HttpsProxyAgent(this.proxyUrl);
    }
  }

  async translate(text, from = 'en', to = 'zh-CN') {
    if (!text || text.length < 2) return text;

    const url = `https://translate.google.com/translate_a/single?client=gtx&sl=${from}&tl=${to}&dt=t&q=${encodeURIComponent(text)}`;

    return new Promise((resolve, reject) => {
      const options = {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        timeout: 10000,
        agent: this.agent
      };

      https.get(url, options, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try {
            const json = JSON.parse(data);
            if (json && json[0] && json[0][0] && json[0][0][0]) {
              resolve(json[0][0][0]);
            } else {
              reject(new Error('解析失败'));
            }
          } catch (e) {
            reject(new Error('JSON解析失败'));
          }
        });
      }).on('error', reject).on('timeout', function() {
        this.destroy();
        reject(new Error('超时'));
      });
    });
  }
}

module.exports = GoogleTranslateProxy;
