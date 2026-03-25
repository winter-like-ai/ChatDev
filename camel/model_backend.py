# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
from abc import ABC, abstractmethod
from typing import Any, Dict

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

import os

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
if 'BASE_URL' in os.environ:
    BASE_URL = os.environ['BASE_URL']
else:
    BASE_URL = None

# ========== Replay 模式状态 ==========
_replay_records = None   # 预加载的 JSONL 记录列表
_replay_index = 0        # 当前回放游标
_replay_used = set()     # 已使用的记录索引集合（防止重复匹配）


def _normalize_messages(messages):
    """将 messages 标准化为可比较的元组列表，只保留 role 和 content"""
    return tuple((m.get("role", ""), m.get("content", "")) for m in messages)


def _find_replay_record(current_messages):
    """在预加载的 JSONL 中查找与 current_messages 匹配的记录"""
    global _replay_records, _replay_index, _replay_used
    import json

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

    def run(self, *args, **kwargs):
        import json as _json

        # ========== Replay 模式分支 ==========
        replay_jsonl = os.environ.get("CHATDEV_REPLAY_JSONL")
        if replay_jsonl:
            global _replay_records, _replay_index
            # 首次调用时预加载全部记录
            if _replay_records is None:
                _replay_records = []
                with open(replay_jsonl, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            _replay_records.append(_json.loads(line))
                log_visualize(f"**[Replay Mode]** 已加载 {len(_replay_records)} 条快照记录")

            current_messages = kwargs.get("messages", [])
            record = _find_replay_record(current_messages)

            if record is None:
                raise RuntimeError(
                    f"[Replay] 未找到匹配的快照记录！当前输入 messages 数量: {len(current_messages)}, "
                    f"已用记录: {len(_replay_used)}/{len(_replay_records)}"
                )

            # 重构 ChatCompletion 对象
            output_data = record["output"]
            if openai_new_api:
                response = ChatCompletion.model_validate(output_data)
            else:
                response = output_data  # 旧版 API 直接返回 dict

            # 打印 replay 信息
            if isinstance(output_data, dict) and "usage" in output_data:
                usage = output_data["usage"]
                cost = prompt_cost(
                    self.model_type.value,
                    num_prompt_tokens=usage.get("prompt_tokens", 0),
                    num_completion_tokens=usage.get("completion_tokens", 0)
                )
                log_visualize(
                    "**[Replay]**\nprompt_tokens: {}\ncompletion_tokens: {}\ntotal_tokens: {}\ncost: ${:.6f}\n".format(
                        usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0),
                        usage.get("total_tokens", 0), cost))

            return response

        # ========== Snapshot 模式（原有逻辑） ==========
        string = "\n".join([message["content"] for message in kwargs["messages"]])
        encoding = tiktoken.encoding_for_model(self.model_type.value)
        num_prompt_tokens = len(encoding.encode(string))
        gap_between_send_receive = 15 * len(kwargs["messages"])
        num_prompt_tokens += gap_between_send_receive

        if openai_new_api:
            # Experimental, add base_url
            if BASE_URL:
                client = openai.OpenAI(
                    api_key=OPENAI_API_KEY,
                    base_url=BASE_URL,
                )
            else:
                client = openai.OpenAI(
                    api_key=OPENAI_API_KEY
                )

            num_max_token_map = {
                "gpt-3.5-turbo": 4096,
                "gpt-3.5-turbo-16k": 16384,
                "gpt-3.5-turbo-0613": 4096,
                "gpt-3.5-turbo-16k-0613": 16384,
                "gpt-4": 8192,
                "gpt-4-0613": 8192,
                "gpt-4-32k": 32768,
                "gpt-4-turbo": 100000,
                "gpt-4o": 4096, #100000
                "gpt-4o-mini": 16384, #100000
            }
            num_max_token = num_max_token_map[self.model_type.value]
            num_max_completion_tokens = num_max_token - num_prompt_tokens
            self.model_config_dict['max_tokens'] = num_max_completion_tokens

            import subprocess
            import json
            import time

            workspace = os.environ.get("CHATDEV_WORKSPACE")
            record_file = os.path.join(workspace, "api_records.jsonl") if workspace else None
            record = {}

            if workspace and os.path.exists(workspace):
                # 获取ChatDev的工作目录（agent向这个目录写入代码），先向git提交代码
                if not os.path.exists(os.path.join(workspace, ".git")):
                    subprocess.run(["git", "init"], cwd=workspace, capture_output=True)
                subprocess.run(["git", "add", "."], cwd=workspace, capture_output=True)
                subprocess.run(["git", "commit", "-m", f"API Snapshot Pre-Request {time.time()}"], cwd=workspace, capture_output=True)

                # 向大模型记录者json文件写入，本次请求api的输入（按照json格式）
                record = {
                    "timestamp": time.time(),
                    "model": getattr(self.model_type, 'value', str(self.model_type)),
                    "config": self.model_config_dict,
                    "input": kwargs.get("messages", [])
                }

            # 请求api
            response = client.chat.completions.create(*args, **kwargs, model=self.model_type.value,
                                                      **self.model_config_dict)

            # 向大模型记录者json文件写入，本次请求api的输出（按照json格式）
            if workspace and os.path.exists(workspace):
                try:
                    record["output"] = json.loads(response.model_dump_json()) if hasattr(response, 'model_dump_json') else (response.model_dump() if hasattr(response, 'model_dump') else dict(response))
                except Exception:
                    record["output"] = str(response)
                
                with open(record_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
            cost = prompt_cost(
                self.model_type.value,
                num_prompt_tokens=response.usage.prompt_tokens,
                num_completion_tokens=response.usage.completion_tokens
            )

            log_visualize(
                "**[OpenAI_Usage_Info Receive]**\nprompt_tokens: {}\ncompletion_tokens: {}\ntotal_tokens: {}\ncost: ${:.6f}\n".format(
                    response.usage.prompt_tokens, response.usage.completion_tokens,
                    response.usage.total_tokens, cost))
            if not isinstance(response, ChatCompletion):
                raise RuntimeError("Unexpected return from OpenAI API")
            return response
        else:
            num_max_token_map = {
                "gpt-3.5-turbo": 4096,
                "gpt-3.5-turbo-16k": 16384,
                "gpt-3.5-turbo-0613": 4096,
                "gpt-3.5-turbo-16k-0613": 16384,
                "gpt-4": 8192,
                "gpt-4-0613": 8192,
                "gpt-4-32k": 32768,
                "gpt-4-turbo": 100000,
                "gpt-4o": 4096, #100000
                "gpt-4o-mini": 16384, #100000
            }
            num_max_token = num_max_token_map[self.model_type.value]
            num_max_completion_tokens = num_max_token - num_prompt_tokens
            self.model_config_dict['max_tokens'] = num_max_completion_tokens

            import subprocess
            import json
            import time

            workspace = os.environ.get("CHATDEV_WORKSPACE")
            record_file = os.path.join(workspace, "api_records.jsonl") if workspace else None
            record = {}

            if workspace and os.path.exists(workspace):
                if not os.path.exists(os.path.join(workspace, ".git")):
                    subprocess.run(["git", "init"], cwd=workspace, capture_output=True)
                subprocess.run(["git", "add", "."], cwd=workspace, capture_output=True)
                subprocess.run(["git", "commit", "-m", f"API Snapshot Pre-Request {time.time()}"], cwd=workspace, capture_output=True)

                record = {
                    "timestamp": time.time(),
                    "model": getattr(self.model_type, 'value', str(self.model_type)),
                    "config": self.model_config_dict,
                    "input": kwargs.get("messages", [])
                }

            response = openai.ChatCompletion.create(*args, **kwargs, model=self.model_type.value,
                                                    **self.model_config_dict)

            if workspace and os.path.exists(workspace):
                try:
                    record["output"] = dict(response)
                except Exception:
                    record["output"] = str(response)
                
                with open(record_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

            cost = prompt_cost(
                self.model_type.value,
                num_prompt_tokens=response["usage"]["prompt_tokens"],
                num_completion_tokens=response["usage"]["completion_tokens"]
            )

            log_visualize(
                "**[OpenAI_Usage_Info Receive]**\nprompt_tokens: {}\ncompletion_tokens: {}\ntotal_tokens: {}\ncost: ${:.6f}\n".format(
                    response["usage"]["prompt_tokens"], response["usage"]["completion_tokens"],
                    response["usage"]["total_tokens"], cost))
            if not isinstance(response, Dict):
                raise RuntimeError("Unexpected return from OpenAI API")
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

        # log_visualize("Model Type: {}".format(model_type))
        inst = model_class(model_type, model_config_dict)
        return inst
