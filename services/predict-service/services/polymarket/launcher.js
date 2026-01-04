#!/usr/bin/env node

/**
 * Polymarket Signal Bot - 命令行启动器
 * 可打包成 EXE 的版本
 */

const path = require('path');
const fs = require('fs');

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('🤖 Polymarket Signal Bot');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

// 检查配置文件
const envPath = path.join(__dirname, '.env');
if (!fs.existsSync(envPath)) {
    console.log('⚠️  首次运行检测');
    console.log('');
    console.log('请先配置 .env 文件:');
    console.log('1. 从 @BotFather 获取 Telegram Bot Token');
    console.log('2. 获取你的 Chat ID');
    console.log('3. 编辑 bot/.env 文件填入配置');
    console.log('');
    console.log('详见: bot/.env.example');
    console.log('');

    // 创建示例配置
    const examplePath = path.join(__dirname, '.env.example');
    if (fs.existsSync(examplePath)) {
        fs.copyFileSync(examplePath, envPath);
        console.log('✅ 已创建 .env 文件模板');
        console.log('路径:', envPath);
    }

    console.log('');
    console.log('配置完成后,请重新运行本程序');
    console.log('');
    process.exit(0);
}

// 启动 Bot
console.log('🚀 启动中...\n');

try {
    require('./src/bot.js');
} catch (error) {
    console.error('❌ 启动失败:', error.message);
    console.error('');
    console.error('详细错误:');
    console.error(error.stack);
    process.exit(1);
}
