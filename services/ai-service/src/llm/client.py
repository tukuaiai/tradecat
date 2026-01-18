# -*- coding: utf-8 -*-
"""LLM 客户端封装

支持两种调用方式：
1. API 网关（默认）- 通过 LLM客户端 调用
2. Gemini CLI - 本地命令行调用
"""
from __future__ import annotations

import json
import os
import sys
from typing import Tuple, List, Dict

from src.config import PROJECT_ROOT, HTTP_PROXY

# 导入工具
sys.path.insert(0, str(PROJECT_ROOT)) if str(PROJECT_ROOT) not in sys.path else None

# LLM 后端选择：cli / api（默认 cli）
LLM_BACKEND = os.getenv("LLM_BACKEND", "cli")


async def call_llm(
    messages: List[Dict[str, str]],
    model: str = "gemini-3-flash-preview",
    backend: str = None,
) -> Tuple[str, str]:
    """
    调用 LLM

    Args:
        messages: OpenAI 兼容的消息列表
        model: 模型名称
        backend: 后端选择 (api/cli)，默认读取环境变量 LLM_BACKEND
        
    Returns:
        (content, raw_response): 回复内容和原始响应
    """
    backend = backend or LLM_BACKEND

    if backend == "cli":
        return await _call_gemini_cli(messages, model)
    else:
        return await _call_api(messages, model)


async def _call_api(messages: List[Dict[str, str]], model: str) -> Tuple[str, str]:
    """通过 API 网关调用"""
    try:
        from libs.common.utils.LLM客户端 import 创建LLM客户端

        if HTTP_PROXY:
            os.environ["HTTP_PROXY"] = HTTP_PROXY
            os.environ["HTTPS_PROXY"] = HTTP_PROXY

        client = 创建LLM客户端()
        resp = client.聊天(
            messages=messages,
            model=model,
            temperature=0.5,
            max_tokens=1000000,
            stream=False,
            req_timeout=600,
        )
        content = resp.get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            content = json.dumps(resp, ensure_ascii=False)
        return content, json.dumps(resp, ensure_ascii=False)
    except Exception as e:
        return f"[API_ERROR] {e}", json.dumps({"error": str(e)}, ensure_ascii=False)


async def _call_gemini_cli(messages: List[Dict[str, str]], model: str) -> Tuple[str, str]:
    """通过 Gemini CLI 无头模式调用"""
    import asyncio

    try:
        from libs.common.utils.gemini_client import call_gemini_with_system

        # 提取 system 和 user 消息
        system_prompt = None
        user_content = ""

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                system_prompt = content
            elif role == "user":
                user_content += content + "\n"

        user_content = user_content.strip()

        # 调用 Gemini CLI（同步转异步）
        loop = asyncio.get_event_loop()
        success, result = await loop.run_in_executor(
            None,
            lambda: call_gemini_with_system(
                system_prompt=system_prompt,
                user_content=user_content,
                model=model,
                timeout=300,
                use_proxy=True,  # 使用代理
            )
        )

        if success:
            return result, json.dumps({"source": "gemini_cli", "model": model}, ensure_ascii=False)
        else:
            return f"[CLI_ERROR] {result}", json.dumps({"error": result}, ensure_ascii=False)

    except ImportError as e:
        return f"[CLI_ERROR] gemini_client 未安装: {e}", json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return f"[CLI_ERROR] {e}", json.dumps({"error": str(e)}, ensure_ascii=False)


# 便捷函数
async def call_gemini(prompt: str, model: str = "gemini-3-flash-preview") -> str:
    """简单调用 Gemini（使用 CLI）"""
    messages = [{"role": "user", "content": prompt}]
    content, _ = await _call_gemini_cli(messages, model)
    return content


__all__ = ["call_llm", "call_gemini"]
