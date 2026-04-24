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
from typing import Dict, Optional

from chatdev.agents.messages import BaseMessage
from chatdev.agents.typing import RoleType

try:
    from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
    from openai.types.chat.chat_completion_message import FunctionCall

    openai_new_api = True  # new openai api version
except ImportError:
    openai_new_api = False  # old openai api version


@dataclass
class ChatMessage(BaseMessage):
    r"""CAMEL 聊天系统中使用的聊天消息的基类。

    参数 (Args):
        role_name (str): 用户或助手角色的名称。
        role_type (RoleType): 角色类型，可以是
            :obj:`RoleType.ASSISTANT` 或 :obj:`RoleType.USER`。
        meta_dict (Optional[Dict[str, str]]): 消息的附加元数据字典。
        role (str): 消息在 OpenAI 聊天系统中的角色。
        content (str): 消息的内容。 (默认: :obj:`""`)
        refusal (str): 用于构建拒绝回复的参数。
        audio (object): 包含模型音频回复数据的音频对象。
    """
    role_name: str
    role_type: RoleType
    meta_dict: Optional[Dict[str, str]]
    role: str
    content: str = ""
    refusal: str = None
    audio: object = None
    if openai_new_api:
        function_call: Optional[FunctionCall] = None
        tool_calls: Optional[ChatCompletionMessageToolCall] = None

    def set_user_role_at_backend(self: BaseMessage):
        return self.__class__(
            role_name=self.role_name,
            role_type=self.role_type,
            meta_dict=self.meta_dict,
            role="user",
            content=self.content,
            refusal=self.refusal,
        )


@dataclass
class AssistantChatMessage(ChatMessage):
    r"""CAMEL 聊天系统中助手(Assistant)角色的聊天消息类。

    属性 (Attributes):
        role_name (str): 助手角色的名称。
        role_type (RoleType): 角色类型，始终为 :obj:`RoleType.ASSISTANT`。
        meta_dict (Optional[Dict[str, str]]): 消息的附加元数据字典。
        role (str): 消息在 OpenAI 聊天系统中的角色。
            (默认: :obj:`"assistant"`)
        content (str): 消息的内容。 (默认: :obj:`""`)
        refusal (str): 用于构建拒绝回复的参数。
        audio (object): 包含模型音频回复数据的音频对象。
    """
    role_name: str
    role_type: RoleType = RoleType.ASSISTANT
    meta_dict: Optional[Dict[str, str]] = None
    role: str = "user"
    content: str = ""
    refusal: str = None
    audio: object = None


@dataclass
class UserChatMessage(ChatMessage):
    r"""CAMEL 聊天系统中用户(User)角色的聊天消息类。

    参数 (Args):
        role_name (str): 用户角色的名称。
        role_type (RoleType): 角色类型，始终为 :obj:`RoleType.USER`。
        meta_dict (Optional[Dict[str, str]]): 消息的附加元数据字典。
        role (str): 消息在 OpenAI 聊天系统中的角色。
            (默认: :obj:`"user"`)
        content (str): 消息的内容。 (默认: :obj:`""`)
        refusal (str): 用于构建拒绝回复的参数。
        audio (object): 包含模型音频回复数据的音频对象。
    """
    role_name: str
    role_type: RoleType = RoleType.USER
    meta_dict: Optional[Dict[str, str]] = None
    role: str = "user"
    content: str = ""
    refusal: str = None
    audio: object = None
