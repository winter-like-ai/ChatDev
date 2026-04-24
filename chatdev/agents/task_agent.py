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
from typing import Any, Dict, Optional, Union

from camel.agents import ChatAgent
from camel.configs import ChatGPTConfig
from camel.messages import SystemMessage, UserChatMessage
from camel.prompts import PromptTemplateGenerator, TextPrompt
from camel.typing import ModelType, RoleType, TaskType


class TaskSpecifyAgent(ChatAgent):
    r"""一个通过提示用户提供更多详细信息来细化给定任务提示词的代理(agent)。

    属性 (Attributes):
        DEFAULT_WORD_LIMIT (int): 任务提示词的默认字数限制。
        task_specify_prompt (TextPrompt): 用于细化任务的提示词。

    参数 (Args):
        model (ModelType): 代理使用的模型类型。
            (默认: :obj:`ModelType.GPT_3_5_TURBO`)
        task_type (TaskType): 要生成提示词的任务类型。
            (默认: :obj:`TaskType.AI_SOCIETY`)
        model_config (Any): 模型的配置信息。
            (默认: :obj:`None`)
        task_specify_prompt (Optional[TextPrompt]): 用于说明任务的提示词。
            (默认: :obj:`None`)
        word_limit (int): 任务提示词的字数限制。
            (默认: :obj:`50`)
    """
    DEFAULT_WORD_LIMIT = 50

    def __init__(
        self,
        model: Optional[ModelType] = None,
        task_type: TaskType = TaskType.AI_SOCIETY,
        model_config: Optional[Any] = None,
        task_specify_prompt: Optional[Union[str, TextPrompt]] = None,
        word_limit: int = DEFAULT_WORD_LIMIT,
    ) -> None:

        if task_specify_prompt is None:
            task_specify_prompt_template = PromptTemplateGenerator(
            ).get_task_specify_prompt(task_type)

            self.task_specify_prompt = task_specify_prompt_template.format(
                word_limit=word_limit)
        else:
            self.task_specify_prompt = task_specify_prompt

        model_config = model_config or ChatGPTConfig(temperature=1.0)

        system_message = SystemMessage(
            role_name="Task Specifier",
            role_type=RoleType.ASSISTANT,
            content="You can make a task more specific.",
        )
        super().__init__(system_message, model, model_config)

    def step(
        self,
        original_task_prompt: Union[str, TextPrompt],
        meta_dict: Optional[Dict[str, Any]] = None,
    ) -> TextPrompt:
        r"""通过提供更多细节以说明（细化）给定的任务提示词。

        参数 (Args):
            original_task_prompt (Union[str, TextPrompt]): 原始的任务提示词。
            meta_dict (Optional[Dict[str, Any]]): 包含要包含在提示词中的
                其他信息的字典。 (默认: :obj:`None`)

        返回 (Returns):
            TextPrompt: 已说明（细化）的任务提示词。
        """
        self.reset()
        self.task_specify_prompt = self.task_specify_prompt.format(
            task=original_task_prompt)

        if meta_dict is not None:
            self.task_specify_prompt = (self.task_specify_prompt.format(
                **meta_dict))

        task_msg = UserChatMessage(role_name="Task Specifier",
                                   content=self.task_specify_prompt)
        specifier_response = super().step(task_msg)
        if (specifier_response.msgs is None
                or len(specifier_response.msgs) == 0):
            raise RuntimeError("Task specification failed.")
        specified_task_msg = specifier_response.msgs[0]

        if specifier_response.terminated:
            raise RuntimeError("Task specification failed.")

        return TextPrompt(specified_task_msg.content)


class TaskPlannerAgent(ChatAgent):
    r"""一个根据输入的任务提示词帮助将任务划分为若干子任务的代理(agent)。

    属性 (Attributes):
        task_planner_prompt (TextPrompt): 代理用来将任务划分为子任务的提示词。

    参数 (Args):
        model (ModelType): 代理使用的模型类型。
            (默认: :obj:`ModelType.GPT_3_5_TURBO`)
        model_config (Any): 模型的配置信息。
            (默认: :obj:`None`)
    """

    def __init__(
        self,
        model: Optional[ModelType] = None,
        model_config: Any = None,
    ) -> None:

        self.task_planner_prompt = TextPrompt(
            "Divide this task into subtasks: {task}. Be concise.")

        system_message = SystemMessage(
            role_name="Task Planner",
            role_type=RoleType.ASSISTANT,
            content="You are a helpful task planner.",
        )
        super().__init__(system_message, model, model_config)

    def step(
        self,
        task_prompt: Union[str, TextPrompt],
    ) -> TextPrompt:
        r"""基于输入的任务提示词生成子任务。

        参数 (Args):
            task_prompt (Union[str, TextPrompt]): 要被划分为子任务的任务提示词。

        返回 (Returns):
            TextPrompt: 代表代理生成的子任务提示词。
        """
        # TODO: Maybe include roles information.
        self.reset()
        self.task_planner_prompt = self.task_planner_prompt.format(
            task=task_prompt)

        task_msg = UserChatMessage(role_name="Task Planner",
                                   content=self.task_planner_prompt)
        # sub_tasks_msgs, terminated, _
        task_tesponse = super().step(task_msg)

        if task_tesponse.msgs is None:
            raise RuntimeError("Got None Subtasks messages.")
        if task_tesponse.terminated:
            raise RuntimeError("Task planning failed.")

        sub_tasks_msg = task_tesponse.msgs[0]
        return TextPrompt(sub_tasks_msg.content)
