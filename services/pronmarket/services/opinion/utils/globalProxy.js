/**
 * 全局代理注入 - 在入口文件最开头 require 此文件
 */
const { HttpsProxyAgent } = require('https-proxy-agent');
const http = require('http');
const https = require('https');

const proxy = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || 'http://127.0.0.1:9910';
const agent = new HttpsProxyAgent(proxy);

// 覆盖全局 agent
http.globalAgent = agent;
https.globalAgent = agent;

console.log(`🌐 全局代理已启用: ${proxy}`);
