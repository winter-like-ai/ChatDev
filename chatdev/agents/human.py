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
from typing import Any, Dict, Sequence

from colorama import Fore

from chatdev.agents.messages import ChatMessage
from chatdev.agents.utils import print_text_animated


class Human:
    r"""代表人类用户的类。

    参数 (Args):
        name (str): 人类用户的名称。
            (默认: :obj:`"Kill Switch Engineer"`).
        logger_color (Any): 显示给用户的菜单选项的颜色。
            (默认: :obj:`Fore.MAGENTA`)

    属性 (Attributes):
        name (str): 人类用户的名称。
        logger_color (Any): 显示给用户的菜单选项的颜色。
        input_button (str): 用于输入按钮的显示文本。
        kill_button (str): 用于终止(Kill)按钮的显示文本。
        options_dict (Dict[str, str]): 包含显示给用户的可用选项字典。
    """

    def __init__(self, name: str = "Kill Switch Engineer",
                 logger_color: Any = Fore.MAGENTA) -> None:
        self.name = name
        self.logger_color = logger_color
        self.input_button = f"Input by {self.name}."
        self.kill_button = "Stop!!!"
        self.options_dict: Dict[str, str] = dict()

    def display_options(self, messages: Sequence[ChatMessage]) -> None:
        r"""向用户显示交互选项。

        参数 (Args):
            messages (Sequence[ChatMessage]): 包含 ChatMessage 对象的列表。

        返回 (Returns):
            None
        """
        options = [message.content for message in messages]
        options.append(self.input_button)
        options.append(self.kill_button)
        print_text_animated(
            self.logger_color + "\n> Proposals from "
            f"{messages[0].role_name} ({messages[0].role_type}). "
            "Please choose an option:\n")
        for index, option in enumerate(options):
            print_text_animated(
                self.logger_color +
                f"\x1b[3mOption {index + 1}:\n{option}\x1b[0m\n")
            self.options_dict[str(index + 1)] = option

    def get_input(self) -> str:
        r"""获取人类用户的输入。

        返回 (Returns):
            str: 用户的输入字符串。
        """
        while True:
            human_input = input(
                self.logger_color +
                f"Please enter your choice ([1-{len(self.options_dict)}]): ")
            print("\n")
            if human_input in self.options_dict:
                break
            print_text_animated(self.logger_color +
                                "\n> Invalid choice. Please try again.\n")

        return human_input

    def parse_input(self, human_input: str,
                    meta_chat_message: ChatMessage) -> ChatMessage:
        r"""解析用户的输入，并返回对应的 ChatMessage 对象。

        参数 (Args):
            human_input (str): 用户的输入信息。
            meta_chat_message (ChatMessage): 一个基础的 ChatMessage 对象。

        返回 (Returns):
            ChatMessage: 携带人类回复内容的 ChatMessage 对象。
        """
        if self.options_dict[human_input] == self.input_button:
            meta_chat_message.content = input(self.logger_color +
                                              "Please enter your message: ")
            return meta_chat_message
        elif self.options_dict[human_input] == self.kill_button:
            exit(self.logger_color + f"Killed by {self.name}.")
        else:
            meta_chat_message.content = self.options_dict[human_input]
            return meta_chat_message

    def step(self, messages: Sequence[ChatMessage]) -> ChatMessage:
        r"""执行一次会话交互：向用户显示选项，获取输入，并解析用户的选择。

        参数 (Args):
            messages (Sequence[ChatMessage]): 一组 ChatMessage 对象列表。

        返回 (Returns):
            ChatMessage: 代表用户最终选择结果的 ChatMessage 对象。
        """
        meta_chat_message = ChatMessage(
            role_name=messages[0].role_name,
            role_type=messages[0].role_type,
            meta_dict=messages[0].meta_dict,
            role=messages[0].role,
            content="",
        )
        self.display_options(messages)
        human_input = self.get_input()
        return self.parse_input(human_input, meta_chat_message)
