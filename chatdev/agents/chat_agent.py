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
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from tenacity import retry
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential

from camel.agents import BaseAgent
from camel.configs import ChatGPTConfig
from camel.messages import ChatMessage, MessageType, SystemMessage
from camel.model_backend import ModelBackend, ModelFactory
from camel.typing import ModelType, RoleType
from camel.utils import (
    get_model_token_limit,
    num_tokens_from_messages,
    openai_api_key_required,
)
from chatdev.utils import log_visualize
try:
    from openai.types.chat import ChatCompletion

    openai_new_api = True  # new openai api version
except ImportError:
    openai_new_api = False  # old openai api version


@dataclass(frozen=True)
class ChatAgentResponse:
    r"""ChatAgent (聊天代理) 返回的响应信息。

    属性 (Attributes):
        msgs (List[ChatMessage]): 包含零个、一个或多个消息的列表。
            如果列表为空，说明在生成消息时出现错误。
            如果列表中有一条消息，说明是正常模式。
            如果列表中有多条消息，说明此时是评论者(critic)模式。
        terminated (bool): 布尔值，表示代理是否 deciding 终止此次对话会话。
        info (Dict[str, Any]): 关于聊天消息的额外信息。
    """
    msgs: List[ChatMessage]
    terminated: bool
    info: Dict[str, Any]

    @property
    def msg(self):
        if self.terminated:
            raise RuntimeError("error in ChatAgentResponse, info:{}".format(str(self.info)))
        if len(self.msgs) > 1:
            raise RuntimeError("Property msg is only available for a single message in msgs")
        elif len(self.msgs) == 0:
            if len(self.info) > 0:
                raise RuntimeError("Empty msgs in ChatAgentResponse, info:{}".format(str(self.info)))
            else:
                # raise RuntimeError("Known issue that msgs is empty and there is no error info, to be fix")
                return None
        return self.msgs[0]


class ChatAgent(BaseAgent):
    r"""用于管理 CAMEL 聊天代理(Chat Agents)对话的类。

    参数 (Args):
        system_message (SystemMessage): 聊天代理的系统消息。
        memory(bool): 聊天代理的记忆设置。
        model (ModelType, optional): 用于生成回复的 LLM (大语言模型)。
            (默认: :obj:`ModelType.GPT_3_5_TURBO`)
        model_config (Any, optional): LLM 模型的配置选项。
            (默认: :obj:`None`)
        message_window_size (int, optional): 包含在上下文窗口中的过去消息的最大数量。
            如果为 `None`，则不进行窗口化限制。 (默认: :obj:`None`)
    """

    def __init__(
            self,
            system_message: SystemMessage,
            memory = None,
            model: Optional[ModelType] = None,
            model_config: Optional[Any] = None,
            message_window_size: Optional[int] = None,
    ) -> None:

        self.system_message: SystemMessage = system_message
        self.role_name: str = system_message.role_name
        self.role_type: RoleType = system_message.role_type
        self.model: ModelType = (model if model is not None else ModelType.GPT_3_5_TURBO)
        self.model_config: ChatGPTConfig = model_config or ChatGPTConfig()
        self.model_token_limit: int = get_model_token_limit(self.model)
        self.message_window_size: Optional[int] = message_window_size
        self.model_backend: ModelBackend = ModelFactory.create(self.model, self.model_config.__dict__)
        self.terminated: bool = False
        self.info: bool = False
        self.init_messages()
        if memory !=None and self.role_name in["Code Reviewer","Programmer","Software Test Engineer"]:
            self.memory = memory.memory_data.get("All")
        else:
            self.memory = None

    def reset(self) -> List[MessageType]:
        r"""将 :obj:`ChatAgent` 重置为其初始状态并返回存储的消息。

        返回 (Returns):
            List[MessageType]: 存储的消息。
        """
        self.terminated = False
        self.init_messages()
        return self.stored_messages

    def get_info(
            self,
            id: Optional[str],
            usage: Optional[Dict[str, int]],
            termination_reasons: List[str],
            num_tokens: int,
    ) -> Dict[str, Any]:
        r"""返回包含有关聊天会话信息的字典。

        参数 (Args):
            id (str, optional): 聊天会话的 ID。
            usage (Dict[str, int], optional): 关于 LLM 模型使用情况的信息。
            termination_reasons (List[str]): 聊天会话终止的原因。
            num_tokens (int): 聊天会话中使用的 token 数量。

        返回 (Returns):
            Dict[str, Any]: 聊天会话信息。
        """
        return {
            "id": id,
            "usage": usage,
            "termination_reasons": termination_reasons,
            "num_tokens": num_tokens,
        }

    def init_messages(self) -> None:
        r"""使用初始系统消息来初始化存储的消息列表。
        """
        self.stored_messages: List[MessageType] = [self.system_message]

    def update_messages(self, message: ChatMessage) -> List[MessageType]:
        r"""使用新消息更新存储的消息列表。

        参数 (Args):
            message (ChatMessage): 要添加到存储消息中的新消息。

        返回 (Returns):
            List[ChatMessage]: 已更新的存储消息。
        """
        self.stored_messages.append(message)
        return self.stored_messages
    def use_memory(self,input_message) -> List[MessageType]:
        if self.memory is None :
            return None
        else:
            if self.role_name == "Programmer":
                result = self.memory.memory_retrieval(input_message,"code")
                if result != None:
                    target_memory,distances, mids,task_list,task_dir_list = result
                    if target_memory != None and len(target_memory) != 0:
                        target_memory="".join(target_memory)
                        #self.stored_messages[-1].content = self.stored_messages[-1].content+"Here is some code you've previously completed:"+target_memory+"You can refer to the previous script to complement this task."
                        log_visualize(self.role_name,
                                            "thinking back and found some related code: \n--------------------------\n"
                                            + target_memory)
                else:
                    target_memory = None
                    log_visualize(self.role_name,
                                         "thinking back but find nothing useful")

            else:
                result = self.memory.memory_retrieval(input_message, "text")
                if result != None:
                    target_memory, distances, mids, task_list, task_dir_list = result
                    if target_memory != None and len(target_memory) != 0:
                        target_memory=";".join(target_memory)
                        #self.stored_messages[-1].content = self.stored_messages[-1].content+"Here are some effective and efficient instructions you have sent to the assistant :"+target_memory+"You can refer to these previous excellent instructions to better instruct assistant here."
                        log_visualize(self.role_name,
                                            "thinking back and found some related text: \n--------------------------\n"
                                            + target_memory)
                else:
                    target_memory = None
                    log_visualize(self.role_name,
                                         "thinking back but find nothing useful")

        return target_memory

    @retry(wait=wait_exponential(min=5, max=60), stop=stop_after_attempt(5))
    @openai_api_key_required
    def step(
            self,
            input_message: ChatMessage,
    ) -> ChatAgentResponse:
        r"""通过对输入消息生成回复来执行聊天会话中的单步操作。

        参数 (Args):
            input_message (ChatMessage): 给代理的输入消息。

        返回 (Returns):
            ChatAgentResponse: 包含输出消息、指示聊天会话是否已终止的布尔值
                以及有关聊天会话的信息的结构体。
        """
        messages = self.update_messages(input_message)
        if self.message_window_size is not None and len(
                messages) > self.message_window_size:
            messages = [self.system_message
                        ] + messages[-self.message_window_size:]
        openai_messages = [message.to_openai_message() for message in messages]
        num_tokens = num_tokens_from_messages(openai_messages, self.model)

        # for openai_message in openai_messages:
        #     # print("{}\t{}".format(openai_message.role, openai_message.content))
        #     print("{}\t{}\t{}".format(openai_message["role"], hash(openai_message["content"]), openai_message["content"][:60].replace("\n", "")))
        # print()

        output_messages: Optional[List[ChatMessage]]
        info: Dict[str, Any]

        if num_tokens < self.model_token_limit:
            response = self.model_backend.run(messages=openai_messages)
            if openai_new_api:
                if not isinstance(response, ChatCompletion):
                    raise RuntimeError("OpenAI returned unexpected struct")
                output_messages = []
                for choice in response.choices:
                    msg_dict = dict(choice.message)
                    kwargs = {k: v for k, v in msg_dict.items() if k in ["role", "content", "function_call", "tool_calls"] and v is not None}
                    output_messages.append(ChatMessage(role_name=self.role_name, role_type=self.role_type, meta_dict=dict(), **kwargs))
                info = self.get_info(
                    response.id,
                    response.usage,
                    [str(choice.finish_reason) for choice in response.choices],
                    num_tokens,
                )
            else:
                if not isinstance(response, dict):
                    raise RuntimeError("OpenAI returned unexpected struct")
                output_messages = []
                for choice in response["choices"]:
                    msg_dict = dict(choice["message"])
                    kwargs = {k: v for k, v in msg_dict.items() if k in ["role", "content", "function_call", "tool_calls"] and v is not None}
                    output_messages.append(ChatMessage(role_name=self.role_name, role_type=self.role_type, meta_dict=dict(), **kwargs))
                info = self.get_info(
                    response["id"],
                    response["usage"],
                    [str(choice["finish_reason"]) for choice in response["choices"]],
                    num_tokens,
                )

            # TODO strict <INFO> check, only in the beginning of the line
            # if "<INFO>" in output_messages[0].content:
            if output_messages[0].content.split("\n")[-1].startswith("<INFO>"):
                self.info = True
        else:
            self.terminated = True
            output_messages = []

            info = self.get_info(
                None,
                None,
                ["max_tokens_exceeded_by_camel"],
                num_tokens,
            )

        return ChatAgentResponse(output_messages, self.terminated, info)

    def __repr__(self) -> str:
        r"""返回 :obj:`ChatAgent` 的字符串表示形式。

        返回 (Returns):
            str: :obj:`ChatAgent` 的字符串表示形式。
        """
        return f"ChatAgent({self.role_name}, {self.role_type}, {self.model})"
