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
import warnings
from typing import Any, Optional

from chatdev.agents.prompts import TaskPromptTemplateDict, TextPrompt
from chatdev.agents.typing import RoleType, TaskType


class PromptTemplateGenerator:
    r"""用于生成任务提示模板的类。

    参数 (Args):
        task_prompt_template_dict (TaskPromptTemplateDict, optional):
            按任务类型分类的任务提示模板字典。如果没有提供，则默认使用一个空字典。
    """

    def __init__(
        self,
        task_prompt_template_dict: Optional[TaskPromptTemplateDict] = None,
    ) -> None:
        self.task_prompt_template_dict = (task_prompt_template_dict or TaskPromptTemplateDict())

    def get_prompt_from_key(self, task_type: TaskType, key: Any) -> TextPrompt:
        r"""使用指定的 :obj:`task_type` 和 :obj:`key` 生成文本提示。

        参数 (Args):
            task_type (TaskType): 任务的类型。
            key (Any): 用于生成提示的键。

        返回 (Returns):
            TextPrompt: 生成的文本提示。

        抛出异常 (Raises):
            KeyError: 如果使用指定的 :obj:`task_type` 和 :obj:`key` 生成提示失败。
        """
        try:
            print(task_type, key)
            return self.task_prompt_template_dict[task_type][key]

        except KeyError:
            raise KeyError("Failed to get generate prompt template for "
                           f"task: {task_type.value} from key: {key}.")

    def get_system_prompt(
        self,
        task_type: TaskType,
        role_type: RoleType,
    ) -> TextPrompt:
        r"""使用指定的 :obj:`task_type` 和 :obj:`role_type` 为系统角色生成文本提示。

        参数 (Args):
            task_type (TaskType): 任务的类型。
            role_type (RoleType): 角色的类型，"USER" 或 "ASSISTANT"。

        返回 (Returns):
            TextPrompt: 生成的文本提示。

        抛出异常 (Raises):
            KeyError: 如果使用指定的 :obj:`task_type` 和 :obj:`role_type` 生成提示失败。
        """
        try:
            return self.get_prompt_from_key(task_type, role_type)

        except KeyError:
            prompt = "You are a helpful assistant."

            warnings.warn("Failed to get system prompt template for "
                          f"task: {task_type.value}, role: {role_type.value}. "
                          f"Set template to: {prompt}")

        return TextPrompt(prompt)

    def get_generate_tasks_prompt(
        self,
        task_type: TaskType,
    ) -> TextPrompt:
        r"""获取针对给定任务类型用于生成子任务的提示。

        参数 (Args):
            task_type (TaskType): 任务的类型。

        返回 (Returns):
            TextPrompt: 用于生成任务的文本提示。
        """
        return self.get_prompt_from_key(task_type, "generate_tasks")

    def get_task_specify_prompt(
        self,
        task_type: TaskType,
    ) -> TextPrompt:
        r"""获取针对给定任务类型用于细化（说明）任务的提示。

        参数 (Args):
            task_type (TaskType): 任务的类型。

        返回 (Returns):
            TextPrompt: 用于说明任务的文本提示。
        """
        return self.get_prompt_from_key(task_type, "task_specify_prompt")
