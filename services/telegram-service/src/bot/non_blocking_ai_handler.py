#!/usr/bin/env python3
"""
🚀 非阻塞AI分析处理器
解决AI分析期间用户无法使用其他功能的问题
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional
import logging
from pathlib import Path
import sys

当前目录 = Path(__file__).resolve().parent
根目录 = 当前目录.parent
if str(根目录) not in sys.path:
    sys.path.append(str(根目录))

# 导入时间相关函数
try:
    from main import format_beijing_time, get_beijing_time
except ImportError:
    # 备用函数定义，防止循环导入
    def format_beijing_time(dt_str, format_str="%Y-%m-%d %H:%M:%S"):
        return datetime.now().strftime(format_str)
    def get_beijing_time():
        from datetime import timezone, timedelta
        beijing_tz = timezone(timedelta(hours=8))
        return datetime.now(beijing_tz)

# 导入 i18n
try:
    from cards.i18n import gettext as _t, resolve_lang, lang_context
except ImportError:
    def _t(key, **kwargs):
        return key
    def resolve_lang(*_args, **_kwargs):
        return None
    class _DummyCtx:
        def __enter__(self):  # pragma: no cover - fallback
            return self
        def __exit__(self, *_args):  # pragma: no cover - fallback
            return False
    def lang_context(_lang=None):  # pragma: no cover - fallback
        return _DummyCtx()

logger = logging.getLogger(__name__)

class NonBlockingAIHandler:
    """非阻塞AI分析处理器"""

    def __init__(self):
        self.active_analyses = {}  # 存储正在进行的分析
        self.completed_analyses = {}  # 存储已完成的分析结果
        self.max_concurrent_analyses = 5  # 最大并发分析数

    async def start_ai_analysis(self, user_id: int, symbol: str, market_type: str,
                               interval: str, ai_telegram_handler, callback_query) -> str:
        """
        启动非阻塞AI分析
        返回分析ID，用户可以继续使用其他功能
        """

        lang = resolve_lang(callback_query)
        with lang_context(lang):
            # 检查并发限制
            if len(self.active_analyses) >= self.max_concurrent_analyses:
                await callback_query.edit_message_text(
                    _t("ai.busy"),
                    parse_mode='Markdown'
                )
                return None

            # 生成唯一分析ID
            analysis_id = f"ai_{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

            # 立即响应用户，告知分析已开始
            coin_name = symbol.replace('USDT', '')
            await callback_query.edit_message_text(
                _t("ai.started", symbol=coin_name, id=analysis_id[-8:]),
                parse_mode='Markdown'
            )

            # 记录分析信息
            self.active_analyses[analysis_id] = {
                'user_id': user_id,
                'symbol': symbol,
                'market_type': market_type,
                'interval': interval,
                'start_time': datetime.now(),
                'status': 'running',
                'chat_id': callback_query.message.chat_id,
                'message_id': callback_query.message.message_id
            }

            # 在后台启动分析任务
            asyncio.create_task(self._run_background_analysis(
                analysis_id, ai_telegram_handler, callback_query
            ))

            return analysis_id

    async def _run_background_analysis(self, analysis_id: str, ai_telegram_handler, callback_query):
        """在后台运行AI分析"""
        lang = resolve_lang(callback_query)
        with lang_context(lang):
            try:
                analysis_info = self.active_analyses[analysis_id]
                symbol = analysis_info['symbol']
                market_type = analysis_info['market_type']
                interval = analysis_info['interval']
                user_id = analysis_info['user_id']

                logger.info(f"开始后台AI分析: {analysis_id} - {symbol}")

                # 执行AI分析（移除超时限制）
                result = await ai_telegram_handler.query_manager.analyze_coin(
                    symbol, market_type, interval, use_ai=True
                )

                # 分析完成，更新状态
                self.active_analyses[analysis_id]['status'] = 'completed'
                self.completed_analyses[analysis_id] = {
                    'result': result,
                    'completion_time': datetime.now(),
                    'user_id': user_id
                }

                # 通知用户分析完成
                await self._notify_analysis_completion(analysis_id, result, callback_query)

            except asyncio.TimeoutError:
                # 超时处理（理论上不应该发生，因为已移除超时限制）
                logger.warning(f"AI分析异常超时: {analysis_id}")
                await self._handle_analysis_timeout(analysis_id, callback_query)

            except Exception as e:
                # 错误处理
                logger.error(f"AI分析失败: {analysis_id} - {str(e)}")
                await self._handle_analysis_error(analysis_id, str(e), callback_query)

            finally:
                # 清理活跃分析记录
                if analysis_id in self.active_analyses:
                    del self.active_analyses[analysis_id]

    async def _notify_analysis_completion(self, analysis_id: str, result: Dict, callback_query):
        """通知用户分析完成"""
        try:
            analysis_info = self.active_analyses.get(analysis_id, {})
            symbol = analysis_info.get('symbol', 'Unknown')
            coin_name = symbol.replace('USDT', '')

            # 构建完整的分析结果消息
            if not result.get('success', False):
                # 分析失败的情况
                await callback_query.message.reply_text(
                    _t("ai.failed", 
                       symbol=coin_name, 
                       id=analysis_id[-8:],
                       duration=self._calculate_duration(analysis_id),
                       error=result.get('error', 'Unknown')),
                    parse_mode='Markdown'
                )
                return

            # 分析成功的情况
            data = result.get('data', {})
            summary = data.get('summary', {})

            # 基础信息
            current_price = summary.get('current_price', 0)
            price_change = summary.get('price_change_percent', 0)
            risk_level = summary.get('risk_assessment', '未知')

            # 方向图标
            if price_change > 0:
                direction = "🟢 🔼"
                change_text = f"+{price_change:.6f}%"
            elif price_change < 0:
                direction = "🔴 🔽"
                change_text = f"{price_change:.6f}%"
            else:
                direction = "⚪ →"
                change_text = "0.00%"

            # 获取AI分析内容
            ai_analysis = data.get('ai_analysis', {})
            ai_content = ai_analysis.get('analysis', '') if ai_analysis.get('available', False) else ''

            # 构建完成通知消息
            completion_msg = _t("ai.completed",
                               symbol=coin_name,
                               id=analysis_id[-8:],
                               duration=self._calculate_duration(analysis_id),
                               price=f"{current_price:.4f}",
                               change=f"{direction} {change_text}",
                               risk=risk_level)

            # 发送完成通知
            await callback_query.message.reply_text(
                completion_msg,
                parse_mode='Markdown'
            )

            # 发送详细分析结果
            if ai_content:
                # 有AI分析内容的情况

                # 构建聊天框消息
                chat_message = f"{_t('ai.detail_title', symbol=coin_name)}\n\n"
                chat_message += f"{_t('ai.report_header', symbol=coin_name)}\n"

                # 检查是否来自缓存
                cache_indicator = ""
                if ai_analysis.get('from_cache', False):
                    cache_indicator = _t("ai.cache_indicator")

                chat_message += f"{format_beijing_time(get_beijing_time().isoformat(), '%Y-%m-%d %H:%M:%S')} | {_t('ai.period')}: {result.get('interval', '15m')}{cache_indicator}\n\n"

                chat_message += f"### {symbol}\n"
                # 根据价格大小决定小数位数
                day_suffix = "1d"
                legacy_suffix = f"{24}h"
                if current_price >= 1:
                    price_format = f"${current_price:.2f}"
                    high_format = f"${summary.get(f'high_{day_suffix}', summary.get(f'high_{legacy_suffix}', current_price)):.2f}"
                    low_format = f"${summary.get(f'low_{day_suffix}', summary.get(f'low_{legacy_suffix}', current_price)):.2f}"
                else:
                    price_format = f"${current_price:.4f}"
                    high_format = f"${summary.get(f'high_{day_suffix}', summary.get(f'high_{legacy_suffix}', current_price)):.4f}"
                    low_format = f"${summary.get(f'low_{day_suffix}', summary.get(f'low_{legacy_suffix}', current_price)):.4f}"

                chat_message += f"## {price_format}\n"
                chat_message += f"{_t('ai.1d_high')}: {high_format}\n"
                chat_message += f"{_t('ai.1d_low')}: {low_format}\n"

                # 获取技术指标
                indicators = data.get('technical_indicators', {})
                adx = indicators.get('adx', 0)
                if adx > 25:
                    trend_strength = _t("ai.trend.strong")
                elif adx > 20:
                    trend_strength = _t("ai.trend.medium")
                else:
                    trend_strength = _t("ai.trend.weak")

                chat_message += f"{_t('ai.trend_strength_label')}: {trend_strength} (ADX: {adx:.1f})\n"
                chat_message += f"{direction} {change_text}\n\n"

                # 只显示AI分析内容的前1000字符
                if len(ai_content) > 1000:
                    chat_message += ai_content[:1000] + "\n\n..."
                    chat_message += f"\n\n{_t('ai.full_report_hint')}"
                else:
                    chat_message += ai_content

                # 发送聊天框消息
                await callback_query.message.reply_text(chat_message, parse_mode='Markdown')

                # 如果内容过长，创建详细的txt文件
                if len(ai_content) > 1000:
                    try:
                        import tempfile
                        import os

                        detailed_content = f"{_t('ai.report_title', symbol=coin_name)}\n\n"
                        detailed_content += ai_content + "\n\n"

                        detailed_content += f"{_t('ai.analysis_time')}: {format_beijing_time(get_beijing_time().isoformat(), '%Y-%m-%d %H:%M:%S')}\n"

                        filename = f"{coin_name}_AI_Report_{format_beijing_time(get_beijing_time().isoformat(), '%Y%m%d_%H%M%S')}.txt"

                        # 创建临时文件
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp_file:
                            tmp_file.write(detailed_content)
                            temp_file_path = tmp_file.name

                        # 发送文件
                        with open(temp_file_path, 'rb') as file:
                            await callback_query.message.reply_document(
                                document=file,
                                filename=filename,
                                caption=_t("ai.file_caption", symbol=coin_name)
                            )

                        # 清理临时文件
                        try:
                            os.unlink(temp_file_path)
                        except Exception:
                            pass

                    except Exception as file_error:
                        logger.error(f"发送文件失败: {file_error}")
                        await callback_query.message.reply_text(_t("ai.report_failed"))

            else:
                # 没有AI分析内容的情况
                indicators = data.get('technical_indicators', {})

                # RSI信息
                rsi_value = indicators.get('rsi', 0)
                if rsi_value >= 70:
                    rsi_signal = _t("ai.rsi_overbought")
                elif rsi_value <= 30:
                    rsi_signal = _t("ai.rsi_oversold")
                else:
                    rsi_signal = _t("ai.rsi_normal")

                # 构建简化报告
                report = _t("ai.simple_report.header", symbol=coin_name) + "\n\n"
                report += _t("ai.simple_report.current_price", price=f"{current_price:.4f}") + "\n"
                report += _t("ai.simple_report.price_change", change=f"{direction} {change_text}") + "\n"
                report += _t("ai.simple_report.risk_level", risk=risk_level) + "\n\n"
                report += _t("ai.simple_report.key_indicators") + "\n"
                report += f"- RSI: {rsi_value:.1f} ({rsi_signal})\n\n"
                report += _t("ai.unavailable") + "\n"
                report += _t("ai.retry_hint")

                await callback_query.message.reply_text(report, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"发送完成通知失败: {analysis_id} - {str(e)}")
            # 如果发送结果失败，至少尝试发送错误信息
            try:
                error_display = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
                await callback_query.message.reply_text(
                    _t("ai.send_failed", symbol=coin_name, id=analysis_id[-8:], error=error_display),
                    parse_mode='Markdown'
                )
            except Exception as fallback_error:
                logger.error(f"发送错误信息也失败: {str(fallback_error)}")

    async def _handle_analysis_timeout(self, analysis_id: str, callback_query):
        """处理分析超时"""
        try:
            analysis_info = self.active_analyses.get(analysis_id, {})
            symbol = analysis_info.get('symbol', 'Unknown')
            coin_name = symbol.replace('USDT', '')

            await callback_query.message.reply_text(
                _t("ai.timeout", symbol=coin_name, id=analysis_id[-8:]),
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"发送超时通知失败: {analysis_id} - {str(e)}")

    async def _handle_analysis_error(self, analysis_id: str, error_msg: str, callback_query):
        """处理分析错误"""
        try:
            analysis_info = self.active_analyses.get(analysis_id, {})
            symbol = analysis_info.get('symbol', 'Unknown')
            coin_name = symbol.replace('USDT', '')

            # 简化错误信息
            error_display = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg

            await callback_query.message.reply_text(
                _t("ai.error", symbol=coin_name, id=analysis_id[-8:], error=error_display),
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"发送错误通知失败: {analysis_id} - {str(e)}")

    def _calculate_duration(self, analysis_id: str) -> str:
        """计算分析用时"""
        try:
            analysis_info = self.active_analyses.get(analysis_id, {})
            start_time = analysis_info.get('start_time')
            if start_time:
                duration = datetime.now() - start_time
                return _t("ai.duration.seconds", seconds=f"{duration.total_seconds():.1f}")
            return _t("ai.duration.unknown")
        except Exception:
            return _t("ai.duration.unknown")

    def get_active_analyses_count(self) -> int:
        """获取当前活跃分析数量"""
        return len(self.active_analyses)

    def get_user_active_analyses(self, user_id: int) -> list:
        """获取用户的活跃分析"""
        return [
            analysis_id for analysis_id, info in self.active_analyses.items()
            if info['user_id'] == user_id
        ]

    async def get_analysis_status(self, analysis_id: str) -> Optional[Dict]:
        """获取分析状态"""
        if analysis_id in self.active_analyses:
            return {
                'status': 'running',
                'info': self.active_analyses[analysis_id]
            }
        elif analysis_id in self.completed_analyses:
            return {
                'status': 'completed',
                'info': self.completed_analyses[analysis_id]
            }
        else:
            return None

# 全局非阻塞AI处理器实例
non_blocking_ai_handler = NonBlockingAIHandler()
