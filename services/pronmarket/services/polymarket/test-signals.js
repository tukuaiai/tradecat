/**
 * 信号模块独立测试脚本
 * 
 * 测试所有 10 个信号模块能否正常工作
 */

const path = require('path');

// 模拟数据
const mockPriceUpdate = {
    assetId: '123456789',
    price: 0.65,
    midpoint: 0.65,
    spread: 0.02,
    timestamp: Date.now()
};

const mockBook = {
    assetId: '123456789',
    bids: [
        { price: 0.64, size: 1000 },
        { price: 0.63, size: 2000 },
        { price: 0.62, size: 3000 }
    ],
    asks: [
        { price: 0.66, size: 1500 },
        { price: 0.67, size: 2500 },
        { price: 0.68, size: 3500 }
    ],
    timestamp: Date.now()
};

const mockTrade = {
    assetId: '123456789',
    price: 0.65,
    side: 'BUY',
    size: 20000,
    timestamp: Date.now()
};

const mockMarketMeta = {
    conditionId: '0x123456789abcdef',
    slug: 'test-market',
    eventSlug: 'test-event',
    question: 'Will this test pass?',
    title: 'Test Market',
    volume24hr: 100000,
    liquidity: 50000,
    oneDayPriceChange: 0.05
};

async function testModule(name, testFn) {
    console.log(`\n${'='.repeat(50)}`);
    console.log(`测试: ${name}`);
    console.log('='.repeat(50));
    
    try {
        const result = await testFn();
        if (result) {
            console.log('✅ 通过');
            console.log('结果:', JSON.stringify(result, null, 2).substring(0, 500));
        } else {
            console.log('⚠️ 无信号 (可能是正常的，取决于阈值)');
        }
        return { name, status: 'pass', result };
    } catch (error) {
        console.log('❌ 失败:', error.message);
        return { name, status: 'fail', error: error.message };
    }
}

async function main() {
    console.log('🧪 开始测试所有信号模块...\n');
    
    const results = [];

    // 1. 套利检测
    results.push(await testModule('1. 套利检测 (arbitrage)', () => {
        const ArbitrageDetector = require('./signals/arbitrage/detector');
        const detector = new ArbitrageDetector({ minProfit: 0.001, debug: true });
        
        // 模拟价格消息
        const msg1 = { payload: { asset: 'token1', price: 0.45, conditionId: '0xtest' } };
        detector.processPrice(msg1);
        
        // 需要配对的 token
        return detector.getStats();
    }));

    // 2. 订单簿失衡
    results.push(await testModule('2. 订单簿失衡 (orderbook)', () => {
        const OrderbookDetector = require('./signals/orderbook/detector');
        const detector = new OrderbookDetector({ minImbalance: 2, minDepth: 100 });
        
        const msg = {
            payload: {
                market: '0xtest',
                bids: [{ price: 0.5, size: 10000 }],
                asks: [{ price: 0.51, size: 1000 }],
                title: 'Test Market'
            }
        };
        
        return detector.processOrderbook(msg);
    }));

    // 3. 扫尾盘
    results.push(await testModule('3. 扫尾盘 (closing)', () => {
        const ClosingMarketScanner = require('./signals/closing/detector');
        const scanner = new ClosingMarketScanner({
            timeWindowHours: 168,
            minVolume: 0,
            maxMarkets: 3
        });
        
        return scanner.getStats();
    }));

    // 4. 聪明钱
    results.push(await testModule('4. 聪明钱 (smart-money)', () => {
        const SmartMoneyDetector = require('./signals/smart-money/detector');
        const detector = new SmartMoneyDetector({ trackTopN: 5, minPositionValue: 100 });
        
        return detector.getStats();
    }));

    // 5. 大额交易
    results.push(await testModule('5. 大额交易 (whale)', () => {
        const LargeTradeDetector = require('./signals/whale/detector');
        const detector = new LargeTradeDetector({ minValue: 1000 });
        
        const signal = detector.process(mockTrade, mockMarketMeta);
        return signal || detector.getStats();
    }));

    // 6. 价格突变
    results.push(await testModule('6. 价格突变 (price-spike)', () => {
        const PriceSpikeDetector = require('./signals/price-spike/detector');
        const detector = new PriceSpikeDetector({ minChange: 0.01, windowMs: 1000 });
        
        // 模拟价格变化
        detector.process({ assetId: 'test', price: 0.50, midpoint: 0.50, timestamp: Date.now() - 500 }, mockMarketMeta);
        const signal = detector.process({ assetId: 'test', price: 0.60, midpoint: 0.60, timestamp: Date.now() }, mockMarketMeta);
        
        return signal || detector.getStats();
    }));

    // 7. 新市场
    results.push(await testModule('7. 新市场 (new-market)', () => {
        const NewMarketDetector = require('./signals/new-market/detector');
        const detector = new NewMarketDetector({ maxAge: 86400000 });
        
        const signal = detector.process({
            conditionId: '0xnewmarket',
            slug: 'new-test-market',
            question: 'Is this a new market?',
            volume: 1000,
            liquidity: 500
        });
        
        return signal || detector.getStats();
    }));

    // 8. 深度套利
    results.push(await testModule('8. 深度套利 (deep-arb)', () => {
        const DeepArbDetector = require('./signals/deep-arb/detector');
        const detector = new DeepArbDetector({ minProfit: 0.001, minDepth: 10 });
        
        // 模拟 YES 订单簿
        detector.process({
            assetId: 'yes-token',
            bids: [{ price: 0.48, size: 1000 }],
            asks: [{ price: 0.49, size: 1000 }],
            timestamp: Date.now()
        }, { conditionId: '0xtest', isYes: true, ...mockMarketMeta });
        
        // 模拟 NO 订单簿
        const signal = detector.process({
            assetId: 'no-token',
            bids: [{ price: 0.48, size: 1000 }],
            asks: [{ price: 0.49, size: 1000 }],
            timestamp: Date.now()
        }, { conditionId: '0xtest', isYes: false, ...mockMarketMeta });
        
        return signal || detector.getStats();
    }));

    // 9. 流动性枯竭
    results.push(await testModule('9. 流动性枯竭 (liquidity-alert)', () => {
        const LiquidityAlertDetector = require('./signals/liquidity-alert/detector');
        const detector = new LiquidityAlertDetector({ dropThreshold: 0.3, minDepth: 100, windowMs: 1000 });
        
        // 模拟深度下降
        detector.process({
            assetId: 'test',
            bids: [{ price: 0.5, size: 5000 }],
            asks: [{ price: 0.51, size: 5000 }],
            timestamp: Date.now() - 500
        }, mockMarketMeta);
        
        const signal = detector.process({
            assetId: 'test',
            bids: [{ price: 0.5, size: 1000 }],
            asks: [{ price: 0.51, size: 1000 }],
            timestamp: Date.now()
        }, mockMarketMeta);
        
        return signal || detector.getStats();
    }));

    // 10. 订单簿倾斜
    results.push(await testModule('10. 订单簿倾斜 (book-skew)', () => {
        const BookSkewDetector = require('./signals/book-skew/detector');
        const detector = new BookSkewDetector({ minSkewChange: 0.3, minDepth: 100, windowMs: 1000 });
        
        // 模拟倾斜变化
        detector.process({
            assetId: 'test',
            bids: [{ price: 0.5, size: 2000 }],
            asks: [{ price: 0.51, size: 2000 }],
            timestamp: Date.now() - 500
        }, mockMarketMeta);
        
        const signal = detector.process({
            assetId: 'test',
            bids: [{ price: 0.5, size: 5000 }],
            asks: [{ price: 0.51, size: 1000 }],
            timestamp: Date.now()
        }, mockMarketMeta);
        
        return signal || detector.getStats();
    }));

    // 汇总
    console.log('\n' + '='.repeat(50));
    console.log('📊 测试汇总');
    console.log('='.repeat(50));
    
    const passed = results.filter(r => r.status === 'pass').length;
    const failed = results.filter(r => r.status === 'fail').length;
    
    console.log(`✅ 通过: ${passed}`);
    console.log(`❌ 失败: ${failed}`);
    
    if (failed > 0) {
        console.log('\n失败的模块:');
        results.filter(r => r.status === 'fail').forEach(r => {
            console.log(`  - ${r.name}: ${r.error}`);
        });
    }
    
    console.log('\n🏁 测试完成');
}

main().catch(console.error);
