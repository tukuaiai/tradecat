#!/usr/bin/env python3
"""
信号系统测试脚本
"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.signals import (
    RULES_BY_TABLE, RULES_BY_CATEGORY,
    RULE_COUNT, TABLE_COUNT,
    get_engine, get_formatter
)


def test_rules():
    """测试规则加载"""
    print("=" * 60)
    print("规则系统测试")
    print("=" * 60)

    print(f"\n📊 总规则数: {RULE_COUNT}")
    print(f"📋 覆盖表数: {TABLE_COUNT}")

    print("\n📁 按分类统计:")
    for cat, rules in RULES_BY_CATEGORY.items():
        print(f"  {cat}: {len(rules)}条")

    print("\n📋 按表统计 (前10):")
    for i, (table, rules) in enumerate(sorted(RULES_BY_TABLE.items(), key=lambda x: -len(x[1]))):
        if i >= 10:
            break
        print(f"  {table}: {len(rules)}条")

    print("\n✅ 规则加载测试通过")


def test_engine():
    """测试引擎"""
    print("\n" + "=" * 60)
    print("引擎测试")
    print("=" * 60)

    engine = get_engine()
    print(f"\n📊 启用规则数: {len(engine.enabled_rules)}")
    print(f"📋 数据库路径: {engine.db_path}")

    # 运行一次检查（只加载基线）
    print("\n🔄 加载基线...")
    signals = engine.run_once()
    print(f"  基线大小: {len(engine.baseline)}")
    print(f"  信号数: {len(signals)} (首次应为0)")

    # 再运行一次
    print("\n🔄 第二次检查...")
    signals = engine.run_once()
    print(f"  信号数: {len(signals)}")

    stats = engine.get_stats()
    print("\n📈 统计:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n✅ 引擎测试通过")


def test_formatter():
    """测试格式化器"""
    print("\n" + "=" * 60)
    print("格式化器测试")
    print("=" * 60)

    fmt = get_formatter()

    # 简化版测试
    msg = fmt.format_simple(
        symbol="BTCUSDT",
        direction="BUY",
        rule_name="RSI进入超卖区",
        timeframe="4h",
        strength=70,
        price=97500,
        message="RSI从中性区进入超卖区"
    )

    print("\n📝 简化版消息:")
    print(msg)
    print(f"字符数: {len(msg)}")

    print("\n✅ 格式化器测试通过")


def main():
    print("\n🚀 信号系统测试开始\n")

    test_rules()
    test_formatter()
    test_engine()

    print("\n" + "=" * 60)
    print("🎉 所有测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    main()
