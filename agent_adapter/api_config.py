# =========== Agent Adapter - 统一 API 配置模块 ===========
# 支持 OpenAI / DeepSeek API Key 自动回退
# ========================================================

"""
api_config — 统一 API Key 与 Base URL 配置
==========================================

本模块提供统一的 API 密钥和基础 URL 解析逻辑，支持以下优先级:

1. 若环境变量 ``DEEPSEEK_API_KEY`` 存在（通过 .env 文件或环境变量）→
   自动设置 ``base_url = "https://api.deepseek.com"`` 并映射模型名称
2. 若不存在但 ``OPENAI_API_KEY`` 环境变量存在 → 使用 OpenAI（``BASE_URL`` 可选覆盖）
3. 两者都不存在 → 抛出明确错误提示

环境变量通过 ``python-dotenv`` 从项目根目录的 ``.env`` 文件加载。

使用示例::

    from agent_adapter.api_config import get_api_key, get_base_url, get_model_name

    api_key = get_api_key()               # 自动选择可用的 Key
    base_url = get_base_url()             # 返回对应的 Base URL 或 None
    model = get_model_name("gpt-4o")      # DeepSeek 模式下自动映射为 "deepseek-chat"
"""

import os
import logging
from pathlib import Path
from enum import Enum
from typing import Optional

# 使用 dotenv 从 .env 文件加载环境变量
try:
    from dotenv import load_dotenv

    # 从项目根目录（ChatDev/）加载 .env 文件
    _project_root = Path(__file__).resolve().parent.parent
    _env_path = _project_root / ".env"
    if _env_path.exists():
        load_dotenv(dotenv_path=str(_env_path), override=False)
        logging.info(f"[api_config] 已从 {_env_path} 加载环境变量")
    else:
        # 也尝试从当前工作目录加载
        load_dotenv(override=False)
except ImportError:
    logging.warning(
        "[api_config] python-dotenv 未安装，无法从 .env 文件加载密钥。"
        "请运行: pip install python-dotenv"
    )


class APIProvider(Enum):
    """API 提供商枚举"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    UNKNOWN = "unknown"


# ========================
# DeepSeek 模型名称映射表
# ========================
# 当使用 DeepSeek API 时，将 OpenAI 模型名称映射为对应的 DeepSeek 模型
DEEPSEEK_MODEL_MAP: dict[str, str] = {
    # GPT-3.5 系列 → DeepSeek Chat
    "gpt-3.5-turbo": "deepseek-chat",
    "gpt-3.5-turbo-16k": "deepseek-chat",
    "gpt-3.5-turbo-0613": "deepseek-chat",
    "gpt-3.5-turbo-16k-0613": "deepseek-chat",
    # GPT-4 系列 → DeepSeek Chat（通用对话）
    "gpt-4": "deepseek-chat",
    "gpt-4-0613": "deepseek-chat",
    "gpt-4-32k": "deepseek-chat",
    "gpt-4-turbo": "deepseek-chat",
    "gpt-4o": "deepseek-chat",
    "gpt-4o-mini": "deepseek-chat",
    # DeepSeek 原生模型名（透传）
    "deepseek-chat": "deepseek-chat",
    "deepseek-reasoner": "deepseek-reasoner",
}

# DeepSeek 默认 Base URL
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# DeepSeek 模型的最大 Token 限制
DEEPSEEK_MAX_TOKEN_MAP: dict[str, int] = {
    "deepseek-chat": 8192,
    "deepseek-reasoner": 8192,
}


def _detect_provider() -> APIProvider:
    """
    检测当前可用的 API 提供商。

    返回:
        APIProvider: 检测到的提供商枚举值

    检测优先级:
        1. DEEPSEEK_API_KEY 环境变量（支持 .env 文件）— 大陆开发者优先
        2. OPENAI_API_KEY 环境变量

    注意:
        优先检测 DEEPSEEK_API_KEY 是因为：如果用户在 .env 中明确配置了
        DeepSeek Key，说明其意图是使用 DeepSeek。而 OPENAI_API_KEY 可能
        是系统中遗留的无效值，不应自动覆盖用户的明确配置。
    """
    if os.environ.get("DEEPSEEK_API_KEY"):
        return APIProvider.DEEPSEEK
    elif os.environ.get("OPENAI_API_KEY"):
        return APIProvider.OPENAI
    return APIProvider.UNKNOWN


def get_provider() -> APIProvider:
    """
    获取当前 API 提供商。

    返回:
        APIProvider: 当前活跃的 API 提供商

    异常:
        EnvironmentError: 当没有找到任何可用的 API Key 时
    """
    provider = _detect_provider()
    if provider == APIProvider.UNKNOWN:
        raise EnvironmentError(
            "未找到可用的 API Key！请设置以下环境变量之一：\n"
            "  1. OPENAI_API_KEY — 用于 OpenAI API\n"
            "  2. DEEPSEEK_API_KEY — 用于 DeepSeek API（可写入项目根目录的 .env 文件）\n\n"
            "示例 .env 文件内容:\n"
            '  DEEPSEEK_API_KEY=sk-your-deepseek-key\n\n'
            "或在终端中设置:\n"
            '  export OPENAI_API_KEY="sk-your-openai-key"\n'
            '  $env:OPENAI_API_KEY="sk-your-openai-key"  # PowerShell'
        )
    return provider


def get_api_key() -> str:
    """
    获取当前可用的 API Key。

    返回:
        str: API Key 字符串

    异常:
        EnvironmentError: 当没有找到任何可用的 API Key 时

    优先级:
        DEEPSEEK_API_KEY > OPENAI_API_KEY
    """
    provider = get_provider()
    if provider == APIProvider.OPENAI:
        key = os.environ["OPENAI_API_KEY"]
        logging.info("[api_config] 使用 OpenAI API Key")
        return key
    elif provider == APIProvider.DEEPSEEK:
        key = os.environ["DEEPSEEK_API_KEY"]
        logging.info("[api_config] 使用 DeepSeek API Key（自动回退）")
        return key
    # 不会到达这里，get_provider() 已处理 UNKNOWN
    raise EnvironmentError("无法获取 API Key")


def get_base_url() -> Optional[str]:
    """
    获取当前应使用的 API Base URL。

    返回:
        Optional[str]: Base URL 字符串，或 None（使用 OpenAI 默认端点）

    逻辑:
        - OpenAI 模式: 返回 BASE_URL 环境变量（如有），否则 None
        - DeepSeek 模式: 始终返回 "https://api.deepseek.com"
    """
    provider = get_provider()
    if provider == APIProvider.OPENAI:
        base_url = os.environ.get("BASE_URL")
        if base_url:
            logging.info(f"[api_config] 使用自定义 Base URL: {base_url}")
        return base_url
    elif provider == APIProvider.DEEPSEEK:
        # DeepSeek 也允许通过 BASE_URL 覆盖（例如使用代理）
        custom_url = os.environ.get("BASE_URL")
        url = custom_url if custom_url else DEEPSEEK_BASE_URL
        logging.info(f"[api_config] 使用 DeepSeek Base URL: {url}")
        return url
    return None


def get_model_name(original_model: str) -> str:
    """
    根据当前 API 提供商，将模型名称映射为对应的实际模型名。

    参数:
        original_model: 原始模型名（如 "gpt-4o"）

    返回:
        str: 实际应传给 API 的模型名称

    示例:
        - OpenAI 模式: "gpt-4o" → "gpt-4o"（原样返回）
        - DeepSeek 模式: "gpt-4o" → "deepseek-chat"（自动映射）
    """
    provider = _detect_provider()
    if provider == APIProvider.DEEPSEEK:
        mapped = DEEPSEEK_MODEL_MAP.get(original_model, "deepseek-chat")
        if mapped != original_model:
            logging.info(
                f"[api_config] 模型名称映射: {original_model} → {mapped}"
            )
        return mapped
    # OpenAI 或其他: 原样返回
    return original_model


def get_max_tokens_for_model(model_name: str) -> int:
    """
    获取指定模型的最大 Token 数。

    参数:
        model_name: 模型名称（已经过映射的实际名称）

    返回:
        int: 最大 Token 数，未知模型默认返回 4096
    """
    # 合并 OpenAI 和 DeepSeek 的 Token 表
    combined_map = {
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16384,
        "gpt-3.5-turbo-0613": 4096,
        "gpt-3.5-turbo-16k-0613": 16384,
        "gpt-4": 8192,
        "gpt-4-0613": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 100000,
        "gpt-4o": 4096,
        "gpt-4o-mini": 16384,
        **DEEPSEEK_MAX_TOKEN_MAP,
    }
    return combined_map.get(model_name, 4096)


def create_openai_client():
    """
    创建并返回一个配置好的 OpenAI 客户端实例。

    该函数自动根据可用的 API Key 选择提供商，并配置正确的 base_url。

    返回:
        openai.OpenAI: 配置好的客户端实例

    异常:
        EnvironmentError: 当没有找到任何可用的 API Key 时
        ImportError: 当 openai 包未安装时
    """
    import openai

    api_key = get_api_key()
    base_url = get_base_url()

    if base_url:
        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
    else:
        client = openai.OpenAI(
            api_key=api_key,
        )

    return client


# ========================
# 模块加载时的诊断信息
# ========================
def print_api_status():
    """打印当前 API 配置状态（用于调试）"""
    try:
        provider = get_provider()
        key = get_api_key()
        base_url = get_base_url()
        masked_key = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
        print(f"[api_config] 提供商: {provider.value}")
        print(f"[api_config] API Key: {masked_key}")
        print(f"[api_config] Base URL: {base_url or '(默认)'}")
    except EnvironmentError as e:
        print(f"[api_config] ⚠️ {e}")


if __name__ == "__main__":
    print_api_status()
