#!/usr/bin/env python3
"""
Gemini API 客户端封装
用于章节分析、字幕翻译、文案生成（替代 Claude Code 内联推理）

配置：在 skill 根目录的 .env 文件中设置
  GEMINI_API_KEY=你的_API_KEY
  GEMINI_MODEL=gemini-2.5-pro（可选，默认 gemini-2.5-pro）

获取 API Key: https://aistudio.google.com/apikey
"""

import os
import sys
import json
import re
import time
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent


def _load_env():
    """从 skill 根目录的 .env 加载环境变量（如果存在）"""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_path = _SCRIPT_DIR.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)


_load_env()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro").strip()

_client = None


def is_configured() -> bool:
    """是否已配置 GEMINI_API_KEY"""
    return bool(GEMINI_API_KEY)


def get_client():
    """惰性初始化并返回 google-genai Client"""
    global _client
    if _client is not None:
        return _client

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY 未设置。请在 .env 文件中配置：\n"
            "  GEMINI_API_KEY=your_api_key\n"
            "获取 API Key: https://aistudio.google.com/apikey"
        )

    try:
        from google import genai
    except ImportError:
        print("❌ Error: google-genai not installed")
        print("请安装: pip install google-genai")
        sys.exit(1)

    _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _extract_json(text: str) -> str:
    """从模型输出中提取 JSON（去除 markdown 代码块围栏等）"""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def generate_json(prompt: str, retries: int = 3, temperature: float = 0.4) -> Any:
    """
    调用 Gemini 生成结构化 JSON 输出

    Args:
        prompt: 提示词
        retries: 失败重试次数
        temperature: 采样温度

    Returns:
        解析后的 JSON 对象（dict 或 list）
    """
    from google.genai import types

    client = get_client()
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
            )
            return json.loads(_extract_json(response.text))
        except Exception as e:
            last_error = e
            print(f"   ⚠️  Gemini 调用失败（第 {attempt}/{retries} 次）: {e}")
            if attempt < retries:
                time.sleep(2 * attempt)

    raise RuntimeError(f"Gemini 调用在 {retries} 次尝试后仍失败: {last_error}")


def generate_text(prompt: str, retries: int = 3, temperature: float = 0.7) -> str:
    """
    调用 Gemini 生成纯文本输出（如 Markdown 文案）

    Args:
        prompt: 提示词
        retries: 失败重试次数
        temperature: 采样温度

    Returns:
        str: 生成的文本
    """
    from google.genai import types

    client = get_client()
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=temperature),
            )
            return response.text.strip()
        except Exception as e:
            last_error = e
            print(f"   ⚠️  Gemini 调用失败（第 {attempt}/{retries} 次）: {e}")
            if attempt < retries:
                time.sleep(2 * attempt)

    raise RuntimeError(f"Gemini 调用在 {retries} 次尝试后仍失败: {last_error}")
