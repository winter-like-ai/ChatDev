# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict
import json
import os
import subprocess
import time

import openai
import tiktoken

from camel.typing import ModelType
from chatdev.statistics import prompt_cost
from chatdev.utils import log_visualize

try:
    from openai.types.chat import ChatCompletion

    openai_new_api = True  # new openai api version
except ImportError:
    openai_new_api = False  # old openai api version

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
if 'BASE_URL' in os.environ:
    BASE_URL = os.environ['BASE_URL']
else:
    BASE_URL = None


# ========== 运行模式枚举 ==========
class RunMode(Enum):
    """ChatDev 运行模式枚举

    - DEFAULT:  原始 ChatDev 模式，纯 API 调用，无 git 快照，无 JSONL 记录
    - SNAPSHOT: 快照模式，真实 API 调用 + git 追踪 + JSONL 记录
    - REPLAY:   回放模式，从 JSONL 文件重放，不调用真实 API
    - HYBRID:   混合模式，先从 JSONL 回放前 k-1 个节点，从第 k 个节点开始调用真实 API
    """
    DEFAULT = "default"
    SNAPSHOT = "snapshot"
    REPLAY = "replay"
    HYBRID = "hybrid"


def _get_run_mode() -> RunMode:
    """从环境变量 CHATDEV_RUN_MODE 获取当前运行模式"""
    mode_str = os.environ.get("CHATDEV_RUN_MODE", "default")
    try:
        return RunMode(mode_str)
    except ValueError:
        log_visualize(f"**[Warning]** 未知运行模式 '{mode_str}'，回退到默认模式")
        return RunMode.DEFAULT


# ========== 全局模式状态 ==========
_replay_records = None   # 预加载的 JSONL 记录列表
_replay_index = 0        # 当前回放游标
_replay_used = set()     # 已使用的记录索引集合（防止重复匹配）
_call_counter = 0        # 全局 API 调用计数器（用于 hybrid 模式节点定位）


def _normalize_messages(messages):
    """将 messages 标准化为可比较的元组列表，只保留 role 和 content"""
    return tuple((m.get("role", ""), m.get("content", "")) for m in messages)


def _load_replay_records(jsonl_path):
    """从 JSONL 文件加载所有记录"""
    global _replay_records
    if _replay_records is None:
        _replay_records = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    _replay_records.append(json.loads(line))
        log_visualize(f"**[Loaded]** 已加载 {len(_replay_records)} 条快照记录 from {jsonl_path}")
    return _replay_records


def _find_replay_record(current_messages):
    """在预加载的 JSONL 中查找与 current_messages 匹配的记录"""
    global _replay_records, _replay_index, _replay_used

    current_norm = _normalize_messages(current_messages)

    # 优先尝试游标位置
    if _replay_index < len(_replay_records) and _replay_index not in _replay_used:
        record = _replay_records[_replay_index]
        saved_norm = _normalize_messages(record.get("input", []))
        if current_norm == saved_norm:
            _replay_used.add(_replay_index)
            _replay_index += 1
            return record

    # 游标不匹配，全量搜索
    for i, record in enumerate(_replay_records):
        if i in _replay_used:
            continue
        saved_norm = _normalize_messages(record.get("input", []))
        if current_norm == saved_norm:
            _replay_used.add(i)
            _replay_index = i + 1
            return record

    # 未找到匹配
    return None


def _git_snapshot(workspace, commit_msg):
    """在工作区中执行 git add + commit"""
    if not workspace or not os.path.exists(workspace):
        return
    if not os.path.exists(os.path.join(workspace, ".git")):
        subprocess.run(["git", "init"], cwd=workspace, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=workspace, capture_output=True)
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=workspace, capture_output=True)


def _write_record_to_jsonl(record_file, record):
    """将一条记录追加写入 JSONL 文件"""
    with open(record_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _serialize_response(response):
    """将 API response 序列化为可 JSON 存储的 dict"""
    try:
        if hasattr(response, 'model_dump_json'):
            return json.loads(response.model_dump_json())
        elif hasattr(response, 'model_dump'):
            return response.model_dump()
        else:
            return dict(response)
    except Exception:
        return str(response)


class ModelBackend(ABC):
    r"""Base class for different model backends.
    May be OpenAI API, a local LLM, a stub for unit tests, etc."""

    @abstractmethod
    def run(self, *args, **kwargs):
        r"""Runs the query to the backend model.

        Raises:
            RuntimeError: if the return value from OpenAI API
            is not a dict that is expected.

        Returns:
            Dict[str, Any]: All backends must return a dict in OpenAI format.
        """
        pass


class OpenAIModel(ModelBackend):
    r"""OpenAI API in a unified ModelBackend interface."""

    def __init__(self, model_type: ModelType, model_config_dict: Dict) -> None:
        super().__init__()
        self.model_type = model_type
        self.model_config_dict = model_config_dict

    def _recall_from_records(self, current_messages):
        """
        从快照记录中查找匹配的 response 并返回重建的对象。
        这是一个纯粹的「API 代理」—— 只负责输入→输出的映射，不做任何日志、git、JSONL 操作。
        对 ChatDev 来说，这个方法和真实 API 调用是完全透明等价的。
        """
        record = _find_replay_record(current_messages)
        if record is None:
            raise RuntimeError(
                f"[Replay] 未找到匹配的快照记录！当前输入 messages 数量: {len(current_messages)}, "
                f"已用记录: {len(_replay_used)}/{len(_replay_records)}"
            )

        output_data = record["output"]

        # 重构 ChatCompletion 对象
        if openai_new_api:
            response = ChatCompletion.model_validate(output_data)
        else:
            response = output_data

        return response

    def _call_api(self, *args, **kwargs):
        """
        执行真实的 OpenAI API 调用，返回 response 对象。
        纯粹的 API 调用，不含任何日志输出、git 操作或 JSONL 记录。
        """
        current_messages = kwargs.get("messages", [])
        string = "\n".join([message["content"] for message in current_messages])
        encoding = tiktoken.encoding_for_model(self.model_type.value)
        num_prompt_tokens = len(encoding.encode(string))
        gap_between_send_receive = 15 * len(current_messages)
        num_prompt_tokens += gap_between_send_receive

        num_max_token_map = {
            "gpt-3.5-turbo": 4096, "gpt-3.5-turbo-16k": 16384,
            "gpt-3.5-turbo-0613": 4096, "gpt-3.5-turbo-16k-0613": 16384,
            "gpt-3.5-turbo-0125": 4096,
            "gpt-4": 8192, "gpt-4-0613": 8192, "gpt-4-32k": 32768,
            "gpt-4-turbo": 100000, "gpt-4o": 4096, "gpt-4o-mini": 16384,
        }
        num_max_token = num_max_token_map[self.model_type.value]
        num_max_completion_tokens = num_max_token - num_prompt_tokens
        self.model_config_dict['max_tokens'] = num_max_completion_tokens

        if openai_new_api:
            if BASE_URL:
                client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url=BASE_URL)
            else:
                client = openai.OpenAI(api_key=OPENAI_API_KEY)

            response = client.chat.completions.create(
                *args, **kwargs, model=self.model_type.value, **self.model_config_dict)

            if not isinstance(response, ChatCompletion):
                raise RuntimeError("Unexpected return from OpenAI API")
            return response
        else:
            response = openai.ChatCompletion.create(
                *args, **kwargs, model=self.model_type.value, **self.model_config_dict)

            if not isinstance(response, Dict):
                raise RuntimeError("Unexpected return from OpenAI API")
            return response

    def _log_usage(self, response):
        """
        统一的 token/cost 日志输出，所有模式共享。
        无论 response 来自真实 API 还是快照记录，日志格式完全一致，
        时间戳由 logging 框架在写入时自动生成（即当前真实时间）。
        """
        if openai_new_api:
            cost = prompt_cost(
                self.model_type.value,
                num_prompt_tokens=response.usage.prompt_tokens,
                num_completion_tokens=response.usage.completion_tokens
            )
            log_visualize(
                "**[OpenAI_Usage_Info Receive]**\n"
                "prompt_tokens: {}\ncompletion_tokens: {}\ntotal_tokens: {}\ncost: ${:.6f}\n".format(
                    response.usage.prompt_tokens, response.usage.completion_tokens,
                    response.usage.total_tokens, cost))
        else:
            cost = prompt_cost(
                self.model_type.value,
                num_prompt_tokens=response["usage"]["prompt_tokens"],
                num_completion_tokens=response["usage"]["completion_tokens"]
            )
            log_visualize(
                "**[OpenAI_Usage_Info Receive]**\n"
                "prompt_tokens: {}\ncompletion_tokens: {}\ntotal_tokens: {}\ncost: ${:.6f}\n".format(
                    response["usage"]["prompt_tokens"], response["usage"]["completion_tokens"],
                    response["usage"]["total_tokens"], cost))

    def _get_record_file(self):
        """获取 JSONL 记录文件路径。
        优先使用用户指定的 CHATDEV_SNAPSHOT_OUTPUT，否则使用 workspace/api_records.jsonl。
        """
        custom_output = os.environ.get("CHATDEV_SNAPSHOT_OUTPUT")
        if custom_output:
            return custom_output
        workspace = os.environ.get("CHATDEV_WORKSPACE")
        if workspace:
            return os.path.join(workspace, "api_records.jsonl")
        return None

    def _do_git_and_record(self, current_messages, response):
        """
        执行 git 快照并将完整 IO 写入 JSONL 记录。
        snapshot 和 hybrid 模式共享此方法。
        """
        workspace = os.environ.get("CHATDEV_WORKSPACE")
        record_file = self._get_record_file()

        if workspace and os.path.exists(workspace):
            _git_snapshot(workspace, f"API Node {_call_counter} @ {time.time()}")

            if record_file:
                record = {
                    "timestamp": time.time(),
                    "node_index": _call_counter,
                    "model": getattr(self.model_type, 'value', str(self.model_type)),
                    "config": self.model_config_dict,
                    "input": current_messages,
                    "output": _serialize_response(response)
                }
                _write_record_to_jsonl(record_file, record)

    def run(self, *args, **kwargs):
        """根据运行模式分发 API 调用。

        设计原则：replay 是 API 调用的透明代理。
        所有模式共享相同的日志格式（_log_usage），时间戳由 logging 框架实时生成。
        唯一的区别是 response 的来源（真实 API vs 快照记录）以及是否记录 git/JSONL。

        四种模式（互斥）：
        - DEFAULT:  纯 API 调用，无快照无记录
        - SNAPSHOT: 真实 API + git 快照 + JSONL 记录
        - REPLAY:   从 JSONL 回放（透明代理，日志与 DEFAULT 一致）
        - HYBRID:   前 k-1 个节点回放 + git/JSONL，从第 k 个节点开始实时 API + git/JSONL
        """
        global _call_counter
        mode = _get_run_mode()
        current_messages = kwargs.get("messages", [])

        # ========== 默认模式：纯 API 调用 ==========
        if mode == RunMode.DEFAULT:
            response = self._call_api(*args, **kwargs)
            self._log_usage(response)

        # ========== 快照模式：API + git + JSONL ==========
        elif mode == RunMode.SNAPSHOT:
            response = self._call_api(*args, **kwargs)
            self._log_usage(response)
            self._do_git_and_record(current_messages, response)

        # ========== 回放模式：透明代理，日志格式与真实调用一致 ==========
        elif mode == RunMode.REPLAY:
            jsonl_path = os.environ.get("CHATDEV_REPLAY_JSONL")
            if not jsonl_path:
                raise RuntimeError("[Replay] 未设置 CHATDEV_REPLAY_JSONL 环境变量")
            _load_replay_records(jsonl_path)
            response = self._recall_from_records(current_messages)
            self._log_usage(response)

        # ========== 混合模式：先回放后实时，全程 git + JSONL ==========
        elif mode == RunMode.HYBRID:
            jsonl_path = os.environ.get("CHATDEV_HYBRID_JSONL")
            if not jsonl_path:
                raise RuntimeError("[Hybrid] 未设置 CHATDEV_HYBRID_JSONL 环境变量")
            hybrid_node = int(os.environ.get("CHATDEV_HYBRID_NODE", "1"))
            _load_replay_records(jsonl_path)

            # hybrid_node 是 1-based：前 hybrid_node-1 个节点回放，从第 hybrid_node 个开始实时
            # _call_counter 是 0-based：replay 阶段 counter = 0 .. hybrid_node-2
            if _call_counter < hybrid_node - 1:
                log_visualize(
                    f"**[Hybrid Replay]** 节点 {_call_counter + 1}/{hybrid_node - 1} (回放中)")
                response = self._recall_from_records(current_messages)
            else:
                if _call_counter == hybrid_node - 1:
                    log_visualize(
                        f"**[Hybrid Switch]** 到达第 {hybrid_node} 个节点，切换为实时 API 调用模式")
                log_visualize(
                    f"**[Hybrid Live]** 节点 {_call_counter + 1} (LIVE API)")
                response = self._call_api(*args, **kwargs)

            self._log_usage(response)
            self._do_git_and_record(current_messages, response)

        else:
            raise ValueError(f"未知运行模式: {mode}")

        _call_counter += 1
        return response


class StubModel(ModelBackend):
    r"""A dummy model used for unit tests."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

    def run(self, *args, **kwargs) -> Dict[str, Any]:
        ARBITRARY_STRING = "Lorem Ipsum"

        return dict(
            id="stub_model_id",
            usage=dict(),
            choices=[
                dict(finish_reason="stop",
                     message=dict(content=ARBITRARY_STRING, role="assistant"))
            ],
        )


class ModelFactory:
    r"""Factory of backend models.

    Raises:
        ValueError: in case the provided model type is unknown.
    """

    @staticmethod
    def create(model_type: ModelType, model_config_dict: Dict) -> ModelBackend:
        default_model_type = ModelType.GPT_3_5_TURBO

        if model_type in {
            ModelType.GPT_3_5_TURBO,
            ModelType.GPT_3_5_TURBO_NEW,
            ModelType.GPT_4,
            ModelType.GPT_4_32k,
            ModelType.GPT_4_TURBO,
            ModelType.GPT_4_TURBO_V,
            ModelType.GPT_4O,
            ModelType.GPT_4O_MINI,
            None
        }:
            model_class = OpenAIModel
        elif model_type == ModelType.STUB:
            model_class = StubModel
        else:
            raise ValueError("Unknown model")

        if model_type is None:
            model_type = default_model_type

        inst = model_class(model_type, model_config_dict)
        return inst
