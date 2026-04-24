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


@dataclass
class SystemMessage(BaseMessage):
    r"""CAMEL 聊天系统中使用的系统消息(System messages)的基础类。

    参数 (Args):
        role_name (str): 用户或助手角色的名称。
        role_type (RoleType): 角色类型，可以是
            :obj:`RoleType.ASSISTANT` 或 :obj:`RoleType.USER`。
        meta_dict (Optional[Dict[str, str]]): 消息的附加元数据字典。
        role (str): 消息在 OpenAI 聊天系统中的角色。
            (默认: :obj:`"system"`)
        content (str): 消息的内容。 (默认: :obj:`""`)
    """
    role_name: str
    role_type: RoleType
    meta_dict: Optional[Dict[str, str]] = None
    role: str = "system"
    content: str = ""


@dataclass
class AssistantSystemMessage(SystemMessage):
    r"""CAMEL 聊天系统中来自助手的系统消息类。

    参数 (Args):
        role_name (str): 助手角色的名称。
        role_type (RoleType): 角色类型，始终为 :obj:`RoleType.ASSISTANT`。
        meta_dict (Optional[Dict[str, str]]): 消息的附加元数据字典。
        role (str): 消息在 OpenAI 聊天系统中的角色。
            (默认: :obj:`"system"`)
        content (str): 消息的内容。 (默认: :obj:`""`)
    """
    role_name: str
    role_type: RoleType = RoleType.ASSISTANT
    meta_dict: Optional[Dict[str, str]] = None
    role: str = "system"
    content: str = ""


@dataclass
class UserSystemMessage(SystemMessage):
    r"""CAMEL 聊天系统中来自用户的系统消息类。

    参数 (Args):
        role_name (str): 用户角色的名称。
        role_type (RoleType): 角色类型，始终为 :obj:`RoleType.USER`。
        meta_dict (Optional[Dict[str, str]]): 消息的附加元数据字典。
        role (str): 消息在 OpenAI 聊天系统中的角色。
            (默认: :obj:`"system"`)
        content (str): 消息的内容。 (默认: :obj:`""`)
    """
    role_name: str
    role_type: RoleType = RoleType.USER
    meta_dict: Optional[Dict[str, str]] = None
    role: str = "system"
    content: str = ""
