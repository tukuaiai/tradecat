# -*- coding: utf-8 -*-
"""提示词构建器"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# 提示词目录（ai-service/prompts/）
PROMPT_DIR = Path(__file__).resolve().parents[2] / "prompts"


def build_prompt(prompt_name: str, payload: Dict[str, Any], lang: Optional[str] = None) -> Tuple[str, str]:
    """
    构建提示词
    
    Args:
        prompt_name: 提示词名称（不含 .txt 后缀）
        payload: 数据负载
        
    Returns:
        (system_prompt, data_json): 系统提示词和数据 JSON
    """
    candidates = []
    if lang:
        candidates.append(PROMPT_DIR / lang / f"{prompt_name}.txt")
        if "_" in lang:
            base = lang.split("_", 1)[0]
            candidates.append(PROMPT_DIR / base / f"{prompt_name}.txt")
    candidates.append(PROMPT_DIR / f"{prompt_name}.txt")

    prompt_path = next((p for p in candidates if p.is_file()), None)
    if not prompt_path:
        raise FileNotFoundError(f"提示词不存在: {candidates[0] if candidates else prompt_name}")

    base = prompt_path.read_text(encoding="utf-8")
    data_json = json.dumps(payload, ensure_ascii=False)
    return base, data_json


__all__ = ["build_prompt"]
