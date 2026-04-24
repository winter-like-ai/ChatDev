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
import os
import re
import zipfile
from functools import wraps
from typing import Any, Callable, List, Optional, Set, TypeVar

import requests
import tiktoken

from chatdev.agents.messages import OpenAIMessage
from chatdev.agents.typing import ModelType, TaskType

F = TypeVar('F', bound=Callable[..., Any])

import time


def count_tokens_openai_chat_models(
        messages: List[OpenAIMessage],
        encoding: Any,
) -> int:
    r"""基于给定的消息列表计算生成 OpenAI 聊天请求所需的 token 数量。

    参数 (Args):
        messages (List[OpenAIMessage]): 消息列表。
        encoding (Any): 使用的编码方法。

    返回 (Returns):
        int: 所需的 token 数量。
    """
    num_tokens = 0
    for message in messages:
        # message follows <im_start>{role/name}\n{content}<im_end>\n
        num_tokens += 4
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always 1 token
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


def num_tokens_from_messages(
        messages: List[OpenAIMessage],
        model: ModelType,
) -> int:
    r"""返回一个消息列表使用的 token 数量。

    参数 (Args):
        messages (List[OpenAIMessage]): 要计算 token 数量的消息列表。
        model (ModelType): 用于对消息进行编码的 OpenAI 模型。

    返回 (Returns):
        int: 消息使用的总 token 数量。

    抛出异常 (Raises):
        NotImplementedError: 如果指定的 `model` 尚未实现此功能。

    参考文献 (References):
        - https://github.com/openai/openai-python/blob/main/chatml.md
        - https://platform.openai.com/docs/models/gpt-4
        - https://platform.openai.com/docs/models/gpt-3-5
    """
    try:
        value_for_tiktoken = model.value_for_tiktoken
        encoding = tiktoken.encoding_for_model(value_for_tiktoken)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    if model in {
        ModelType.GPT_3_5_TURBO,
        ModelType.GPT_3_5_TURBO_NEW,
        ModelType.GPT_4,
        ModelType.GPT_4_32k,
        ModelType.GPT_4_TURBO,
        ModelType.GPT_4_TURBO_V,
        ModelType.GPT_4O,
        ModelType.GPT_4O_MINI,
        ModelType.STUB
    }:
        return count_tokens_openai_chat_models(messages, encoding)
    else:
        raise NotImplementedError(
            f"`num_tokens_from_messages`` is not presently implemented "
            f"for model {model}. "
            f"See https://github.com/openai/openai-python/blob/main/chatml.md "
            f"for information on how messages are converted to tokens. "
            f"See https://platform.openai.com/docs/models/gpt-4"
            f"or https://platform.openai.com/docs/models/gpt-3-5"
            f"for information about openai chat models.")


def get_model_token_limit(model: ModelType) -> int:
    r"""返回给定模型的最大 token 限制。

    参数 (Args):
        model (ModelType): 模型类型。

    返回 (Returns):
        int: 给定模型的最大 token 限制。
    """
    if model == ModelType.GPT_3_5_TURBO:
        return 16384
    elif model == ModelType.GPT_3_5_TURBO_NEW:
        return 16384
    elif model == ModelType.GPT_4:
        return 8192
    elif model == ModelType.GPT_4_32k:
        return 32768
    elif model == ModelType.GPT_4_TURBO:
        return 128000
    elif model == ModelType.STUB:
        return 4096
    elif model == ModelType.GPT_4O:
        return 128000
    elif model == ModelType.GPT_4O_MINI:
        return 128000
    else:
        raise ValueError("Unknown model type")


def openai_api_key_required(func: F) -> F:
    r"""检查环境变量中是否提供了 OpenAI API 密钥的装饰器。

    参数 (Args):
        func (callable): 要包装的函数。

    返回 (Returns):
        callable: 装饰后的函数。

    抛出异常 (Raises):
        ValueError: 如果在环境变量中未找到 OpenAI API 密钥。
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        from chatdev.agents.chat_agent import ChatAgent
        if not isinstance(self, ChatAgent):
            raise ValueError("Expected ChatAgent")
        if self.model == ModelType.STUB:
            return func(self, *args, **kwargs)
        elif 'OPENAI_API_KEY' in os.environ:
            return func(self, *args, **kwargs)
        else:
            raise ValueError('OpenAI API key not found.')

    return wrapper


def print_text_animated(text, delay: float = 0.005, end: str = ""):
    r"""以动画效果打印给定文本（打字机效果）。

    参数 (Args):
        text (str): 要打印的文本。
        delay (float, optional): 打印每个字符之间的延迟（以秒为单位）。
            (默认: :obj:`0.02`)
        end (str, optional): 在文本之后打印的结束字符。
            (默认: :obj:`""`)
    """
    for char in text:
        print(char, end=end, flush=True)
        time.sleep(delay)
    print('\n')


def get_prompt_template_key_words(template: str) -> Set[str]:
    r"""给定一个包含大括号 {} 的字符串模板，返回括号内单词的集合。

    参数 (Args):
        template (str): 包含大括号的字符串。

    返回 (Returns):
        List[str]: 大括号内单词的列表/集合。

    示例 (Example):
        >>> get_prompt_template_key_words('Hi, {name}! How are you {status}?')
        {'name', 'status'}
    """
    return set(re.findall(r'{([^}]*)}', template))


def get_first_int(string: str) -> Optional[int]:
    r"""返回在给定字符串中找到的第一个整数。

    如果未找到整数，则返回 None。

    参数 (Args):
        string (str): 输入的字符串。

    返回 (Returns):
        int or None: 在字符串中找到的第一个整数，如果未找到则返回 None。
    """
    match = re.search(r'\d+', string)
    if match:
        return int(match.group())
    else:
        return None


def download_tasks(task: TaskType, folder_path: str) -> None:
    r"""从远程 URL 下载任务数据的 zip 文件并解压至指定文件夹，随后清理压缩包。

    参数 (Args):
        task (TaskType): 要下载的任务类型对象。
        folder_path (str): 压缩包解压后保存的目标文件夹路径。

    返回 (Returns):
        None
    """
    # Define the path to save the zip file
    zip_file_path = os.path.join(folder_path, "tasks.zip")

    # Download the zip file from the Google Drive link
    response = requests.get("https://huggingface.co/datasets/camel-ai/"
                            f"metadata/resolve/main/{task.value}_tasks.zip")

    # Save the zip file
    with open(zip_file_path, "wb") as f:
        f.write(response.content)

    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(folder_path)

    # Delete the zip file
    os.remove(zip_file_path)
