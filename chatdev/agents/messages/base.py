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
from typing import Any, Dict, List, Optional, Tuple, Union

from chatdev.agents.messages import (
    OpenAIAssistantMessage,
    OpenAIChatMessage,
    OpenAIMessage,
    OpenAISystemMessage,
    OpenAIUserMessage,
)
from chatdev.agents.prompts import CodePrompt, TextPrompt
from chatdev.agents.typing import ModelType, RoleType

try:
    from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
    from openai.types.chat.chat_completion_message import FunctionCall

    openai_new_api = True  # new openai api version
except ImportError:
    openai_new_api = False  # old openai api version


@dataclass
class BaseMessage:
    r"""CAMEL 聊天系统中使用的消息对象的基类。

    参数 (Args):
        role_name (str): 用户或助手角色的名称。
        role_type (RoleType): 角色类型，可以是
            :obj:`RoleType.ASSISTANT` 或 :obj:`RoleType.USER`。
        meta_dict (Optional[Dict[str, str]]): 消息的附加元数据字典。
        role (str): 消息在 OpenAI 聊天系统中的角色，可以是
            :obj:`"system"`、:obj:`"user"` 或 :obj:`"assistant"`。
        content (str): 消息的内容。
    """
    role_name: str
    role_type: RoleType
    meta_dict: Optional[Dict[str, str]]
    role: str
    content: str
    if openai_new_api:
        function_call: Optional[FunctionCall] = None
        tool_calls: Optional[ChatCompletionMessageToolCall] = None

    def __getattribute__(self, name: str) -> Any:
        r"""获取属性的方法重写，旨在将字符串方法委托给 :obj:`content`。

        参数 (Args):
            name (str): 属性名称。

        返回 (Returns):
            Any: 属性值。
        """
        delegate_methods = [
            method for method in dir(str) if not method.startswith('_')
        ]
        if name in delegate_methods:
            content = super().__getattribute__('content')
            if isinstance(content, str):
                content_method = getattr(content, name, None)
                if callable(content_method):

                    def modify_arg(arg: Any) -> Any:
                        r"""修改委托方法的参数。

                        参数 (Args):
                            arg (Any): 参数值。

                        返回 (Returns):
                            Any: 修改后的参数值。
                        """
                        if isinstance(arg, BaseMessage):
                            return arg.content
                        elif isinstance(arg, (list, tuple)):
                            return type(arg)(modify_arg(item) for item in arg)
                        else:
                            return arg

                    def wrapper(*args: Any, **kwargs: Any) -> Any:
                        r"""委托方法的包装器函数。

                        参数 (Args):
                            *args (Any): 可变长度参数列表。
                            **kwargs (Any): 任意关键字参数。

                        返回 (Returns):
                            Any: 委托方法的执行结果。
                        """
                        modified_args = [modify_arg(arg) for arg in args]
                        modified_kwargs = {
                            k: modify_arg(v)
                            for k, v in kwargs.items()
                        }
                        output = content_method(*modified_args,
                                                **modified_kwargs)
                        return self._create_new_instance(output) if isinstance(
                            output, str) else output

                    return wrapper

        return super().__getattribute__(name)

    def _create_new_instance(self, content: str) -> "BaseMessage":
        r"""使用更新后的内容创建一个新的 :obj:`BaseMessage` 实例。

        参数 (Args):
            content (str): 新的内容值。

        返回 (Returns):
            BaseMessage: 包含新内容的新 :obj:`BaseMessage` 实例。
        """
        return self.__class__(role_name=self.role_name,
                              role_type=self.role_type,
                              meta_dict=self.meta_dict, role=self.role,
                              content=content)

    def __add__(self, other: Any) -> Union["BaseMessage", Any]:
        r"""重写 :obj:`BaseMessage` 的加法运算符。

        参数 (Args):
            other (Any): 要相加的值。

        返回 (Returns):
            Union[BaseMessage, Any]: 相加的结果。
        """
        if isinstance(other, BaseMessage):
            combined_content = self.content.__add__(other.content)
        elif isinstance(other, str):
            combined_content = self.content.__add__(other)
        else:
            raise TypeError(
                f"Unsupported operand type(s) for +: '{type(self)}' and "
                f"'{type(other)}'")
        return self._create_new_instance(combined_content)

    def __mul__(self, other: Any) -> Union["BaseMessage", Any]:
        r"""重写 :obj:`BaseMessage` 的乘法运算符。

        参数 (Args):
            other (Any): 要乘以的值。

        返回 (Returns):
            Union[BaseMessage, Any]: 相乘的结果。
        """
        if isinstance(other, int):
            multiplied_content = self.content.__mul__(other)
            return self._create_new_instance(multiplied_content)
        else:
            raise TypeError(
                f"Unsupported operand type(s) for *: '{type(self)}' and "
                f"'{type(other)}'")

    def __len__(self) -> int:
        r"""重写 :obj:`BaseMessage` 的长度运算符。

        返回 (Returns):
            int: 内容的长度。
        """
        return len(self.content)

    def __contains__(self, item: str) -> bool:
        r"""重写 :obj:`BaseMessage` 的包含 (in) 运算符。

        参数 (Args):
            item (str): 要检查是否包含的项。

        返回 (Returns):
            bool: 如果项包含在内容中，则返回 :obj:`True`，否则返回 :obj:`False`。
        """
        return item in self.content

    def token_len(self, model: ModelType = ModelType.GPT_3_5_TURBO) -> int:
        r"""计算消息在指定模型下的 token 长度。

        参数 (Args):
            model (ModelType, optional): 用于计算 token 长度的模型类型。
                (默认: :obj:`ModelType.GPT_3_5_TURBO`)

        返回 (Returns):
            int: 消息的 token 长度。
        """
        from chatdev.agents.utils import num_tokens_from_messages
        return num_tokens_from_messages([self.to_openai_chat_message()], model)

    def extract_text_and_code_prompts(
            self) -> Tuple[List[TextPrompt], List[CodePrompt]]:
        r"""从消息内容中提取文本和代码提示 (prompts)。

        返回 (Returns):
            Tuple[List[TextPrompt], List[CodePrompt]]: 一个元组，包含从内容中
                提取的文本提示列表和代码提示列表。
        """
        text_prompts: List[TextPrompt] = []
        code_prompts: List[CodePrompt] = []

        lines = self.content.split("\n")
        idx = 0
        start_idx = 0
        while idx < len(lines):
            while idx < len(lines) and (
                    not lines[idx].lstrip().startswith("```")):
                idx += 1
            text = "\n".join(lines[start_idx:idx]).strip()
            text_prompts.append(TextPrompt(text))

            if idx >= len(lines):
                break

            code_type = lines[idx].strip()[3:].strip()
            idx += 1
            start_idx = idx
            while not lines[idx].lstrip().startswith("```"):
                idx += 1
            code = "\n".join(lines[start_idx:idx]).strip()
            code_prompts.append(CodePrompt(code, code_type=code_type))

            idx += 1
            start_idx = idx

        return text_prompts, code_prompts

    def to_openai_message(self, role: Optional[str] = None) -> OpenAIMessage:
        r"""将消息对象转换为 :obj:`OpenAIMessage` 格式字典。

        参数 (Args):
            role (Optional[str]): 消息在 OpenAI 聊天系统中的角色，可以是
                :obj:`"system"`、:obj:`"user"` 或 :obj:`"assistant"`。
                (默认: :obj:`None`)

        返回 (Returns):
            OpenAIMessage: 转换后的 :obj:`OpenAIMessage` 字典对象。
        """
        role = role or self.role
        if role not in {"system", "user", "assistant"}:
            raise ValueError(f"Unrecognized role: {role}")
        return {"role": role, "content": self.content}

    def to_openai_chat_message(
        self,
        role: Optional[str] = None,
    ) -> OpenAIChatMessage:
        r"""将消息对象转换为 :obj:`OpenAIChatMessage` 格式字典。

        参数 (Args):
            role (Optional[str]): 消息在 OpenAI 聊天系统中的角色，可以是
                :obj:`"user"` 或 :obj:`"assistant"`。
                (默认: :obj:`None`)

        返回 (Returns):
            OpenAIChatMessage: 转换后的 :obj:`OpenAIChatMessage` 字典对象。
        """
        role = role or self.role
        if role not in {"user", "assistant"}:
            raise ValueError(f"Unrecognized role: {role}")
        return {"role": role, "content": self.content}

    def to_openai_system_message(self) -> OpenAISystemMessage:
        r"""将消息转换为系统角色的 :obj:`OpenAISystemMessage` 对象字典。

        返回 (Returns):
            OpenAISystemMessage: 转换后的 :obj:`OpenAISystemMessage` 字典对象。
        """
        return {"role": "system", "content": self.content}

    def to_openai_user_message(self) -> OpenAIUserMessage:
        r"""将消息转换为用户角色的 :obj:`OpenAIUserMessage` 字典对象。

        返回 (Returns):
            OpenAIUserMessage: 转换后的 :obj:`OpenAIUserMessage` 字典对象。
        """
        return {"role": "user", "content": self.content}

    def to_openai_assistant_message(self) -> OpenAIAssistantMessage:
        r"""将消息转换为助手角色的 :obj:`OpenAIAssistantMessage` 字典对象。

        返回 (Returns):
            OpenAIAssistantMessage: 转换后的 :obj:`OpenAIAssistantMessage` 字典对象。
        """
        return {"role": "assistant", "content": self.content}

    def to_dict(self) -> Dict:
        r"""将消息转换为字典格式。

        返回 (Returns):
            dict: 转换后的字典。
        """
        return {
            "role_name": self.role_name,
            "role_type": self.role_type.name,
            **(self.meta_dict or {}),
            "role": self.role,
            "content": self.content,
        }
