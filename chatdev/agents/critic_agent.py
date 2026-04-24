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
import copy
import random
import warnings
from typing import Any, Dict, Optional, Sequence

from colorama import Fore

from camel.agents import ChatAgent
from camel.messages import ChatMessage, SystemMessage
from camel.typing import ModelType
from camel.utils import get_first_int, print_text_animated


class CriticAgent(ChatAgent):
    r"""用于协助选择选项的评论者代理(critic agent)的类。

    参数 (Args):
        system_message (SystemMessage): 评论者代理的系统消息。
        model (ModelType, optional): 用于生成响应的 LLM 模型。
            (默认: :obj:`ModelType.GPT_3_5_TURBO`)
        model_config (Any, optional): LLM 模型的配置选项。
            (默认: :obj:`None`)
        message_window_size (int, optional): 包含在上下文窗口中的过去消息的最大数量。
            如果为 `None`，则不进行窗口化限制。 (默认: :obj:`6`)
        retry_attempts (int, optional): 如果评论者未能返回有效选项时的重试次数。
            (默认: :obj:`2`)
        verbose (bool, optional): 是否打印评论者的消息。
        logger_color (Any): 显示给用户的菜单选项颜色。 (默认: :obj:`Fore.MAGENTA`)
    """

    def __init__(
        self,
        system_message: SystemMessage,
        model: ModelType = ModelType.GPT_3_5_TURBO,
        model_config: Optional[Any] = None,
        message_window_size: int = 6,
        retry_attempts: int = 2,
        verbose: bool = False,
        logger_color: Any = Fore.MAGENTA,
    ) -> None:
        super().__init__(system_message, model, model_config,
                         message_window_size)
        self.options_dict: Dict[str, str] = dict()
        self.retry_attempts = retry_attempts
        self.verbose = verbose
        self.logger_color = logger_color

    def flatten_options(self, messages: Sequence[ChatMessage]) -> str:
        r"""将被评审选项展平为给评论者的字符串。

        参数 (Args):
            messages (Sequence[ChatMessage]): :obj:`ChatMessage` 对象列表。

        返回 (Returns):
            str: 格式为给评论者的展平选项的字符串。
        """
        options = [message.content for message in messages]
        flatten_options = (
            f"> Proposals from "
            f"{messages[0].role_name} ({messages[0].role_type}). "
            "Please choose an option:\n")
        for index, option in enumerate(options):
            flatten_options += f"Option {index + 1}:\n{option}\n\n"
            self.options_dict[str(index + 1)] = option
        format = (
            f"Please first enter your choice ([1-{len(self.options_dict)}]) "
            "and then your explanation and comparison: ")
        return flatten_options + format

    def get_option(self, input_message: ChatMessage) -> str:
        r"""获取评论者选择的选项。

        参数 (Args):
            input_message (ChatMessage): 代表输入消息的 :obj:`ChatMessage` 对象。

        返回 (Returns):
            str: 评论者选择的选项。
        """
        # TODO: Add support for editing options by the critic.
        msg_content = input_message.content
        i = 0
        while i < self.retry_attempts:
            critic_response = super().step(input_message)

            if critic_response.msgs is None or len(critic_response.msgs) == 0:
                raise RuntimeError("Got None critic messages.")
            if critic_response.terminated:
                raise RuntimeError("Critic step failed.")

            critic_msg = critic_response.msgs[0]
            self.update_messages(critic_msg)
            if self.verbose:
                print_text_animated(self.logger_color + "\n> Critic response: "
                                    f"\x1b[3m{critic_msg.content}\x1b[0m\n")
            choice = self.parse_critic(critic_msg)

            if choice in self.options_dict:
                return self.options_dict[choice]
            else:
                input_message = ChatMessage(
                    role_name=input_message.role_name,
                    role_type=input_message.role_type,
                    meta_dict=input_message.meta_dict,
                    role=input_message.role,
                    content="> Invalid choice. Please choose again.\n" +
                    msg_content,
                )
                i += 1
        warnings.warn("Critic failed to get a valid option. "
                      f"After {self.retry_attempts} attempts. "
                      "Returning a random option.")
        return random.choice(list(self.options_dict.values()))

    def parse_critic(self, critic_msg: ChatMessage) -> Optional[str]:
        r"""解析评论者的消息并提取做出的选择。

        参数 (Args):
            critic_msg (ChatMessage): 代表评论者回复的 :obj:`ChatMessage` 对象。

        返回 (Returns):
            Optional[str]: 评论者选择作为字符串，如果消息无法解析则返回 None。
        """
        choice = str(get_first_int(critic_msg.content))
        return choice

    def step(self, messages: Sequence[ChatMessage]) -> ChatMessage:
        r"""执行一步会话：将选项展平给评论者，获取选项，并解析选择。

        参数 (Args):
            messages (Sequence[ChatMessage]): ChatMessage 对象列表。

        返回 (Returns):
            ChatMessage: 代表评论者选择的 :obj:`ChatMessage` 对象。
        """
        meta_chat_message = ChatMessage(
            role_name=messages[0].role_name,
            role_type=messages[0].role_type,
            meta_dict=messages[0].meta_dict,
            role=messages[0].role,
            content="",
        )

        flatten_options = self.flatten_options(messages)
        if self.verbose:
            print_text_animated(self.logger_color +
                                f"\x1b[3m{flatten_options}\x1b[0m\n")
        input_msg = copy.deepcopy(meta_chat_message)
        input_msg.content = flatten_options

        option = self.get_option(input_msg.set_user_role_at_backend())
        output_msg = copy.deepcopy(meta_chat_message)
        output_msg.content = option

        return output_msg
