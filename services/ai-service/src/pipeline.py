# -*- coding: utf-8 -*-
"""
AI 分析管道
- 获取全量数据 -> 构建提示词 -> 调用 LLM -> 保存结果
- 不做数据精简，完整喂给 LLM
"""
from __future__ import annotations

import asyncio
from typing import Dict, Any

from src.data import fetch_payload
from src.prompt import build_prompt
from src.llm import call_llm
from src.utils.run_recorder import RunRecorder


async def run_analysis(symbol: str, interval: str, prompt_name: str, lang: str | None = None) -> Dict[str, Any]:
    """
    执行 AI 分析
    
    Args:
        symbol: 交易对，如 BTCUSDT
        interval: 时间周期，如 1h
        prompt_name: 提示词名称
        
    Returns:
        分析结果字典
    """
    # 1. 获取全量数据
    payload = await asyncio.to_thread(fetch_payload, symbol, interval)

    # 2. 构建提示词（完整数据，不精简）
    system_prompt, data_json = await asyncio.to_thread(build_prompt, prompt_name, payload, lang)
    
    # 根据语言调整输出要求，默认中文\n+    lang_hint = \"中文\" if not lang or lang.startswith(\"zh\") else \"English\"\n+    user_content = (\n+        f\"请基于以下交易数据进行市场分析，输出{lang_hint}结论\\n\"\n+        \"禁止原样粘贴 DATA_JSON 或长表格；只输出摘要和关键数值\\n\"\n+        \"===DATA_JSON===\\n\"\n+        f\"{data_json}\"\n+    )

    # 3. 调用 LLM
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    analysis_text, raw_response = await call_llm(messages)

    # 4. 保存结果
    recorder = RunRecorder()
    await asyncio.to_thread(
        recorder.save_run,
        symbol,
        interval,
        prompt_name,
        payload,
        system_prompt,
        analysis_text,
        messages,
    )

    return {
        "analysis": analysis_text,
        "raw_response": raw_response,
        "payload": payload,
    }


__all__ = ["run_analysis"]
