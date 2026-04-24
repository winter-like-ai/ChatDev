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
from typing import Any, Dict

from chatdev.agents.prompts import (
    TextPromptDict,
)
from chatdev.agents.typing import TaskType


class TaskPromptTemplateDict(Dict[Any, TextPromptDict]):
    r"""以任务类型为键的任务提示模板字典 (:obj:`Dict[Any, TextPromptDict]`)。
    该字典用于将任务类型映射到其对应的提示模板字典。

    参数 (Args):
        *args: 传递给 :obj:`dict` 构造函数的位置参数。
        **kwargs: 传递给 :obj:`dict` 构造函数的关键字参数。
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.update({
            TaskType.AI_SOCIETY: AISocietyPromptTemplateDict(),
            TaskType.CODE: CodePromptTemplateDict(),
            TaskType.MISALIGNMENT: MisalignmentPromptTemplateDict(),
            TaskType.TRANSLATION: TranslationPromptTemplateDict(),
            TaskType.EVALUATION: EvaluationPromptTemplateDict(),
            TaskType.SOLUTION_EXTRACTION: SolutionExtractionPromptTemplateDict(),
        })
