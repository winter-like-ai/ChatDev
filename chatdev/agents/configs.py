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
from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence, Union


@dataclass(frozen=True)
class ChatGPTConfig:
    r"""定义了使用 OpenAI API 生成聊天内容的参数配置。

    参数 (Args):
        temperature (float, optional): 使用的采样温度，介于 :obj:`0` 和 :obj:`2` 之间。
            更高的值使得输出更加随机，而更低的值则使其更加集中和确定。
            (默认: :obj:`0.2`)
        top_p (float, optional): 温度采样的替代方案，被称为核心采样 (nucleus sampling)，
            模型会考虑具有 top_p 概率质量的 token 结果。因此 :obj:`0.1` 意味着只有
            包含前 10% 概率质量的 token 才会被考虑。
            (默认: :obj:`1.0`)
        n (int, optional): 为每条输入消息生成多少个聊天补全选项。 (默认: :obj:`1`)
        stream (bool, optional): 如果为 True，当部分消息增量可用时，
            将作为仅数据的服务器发送事件 (server-sent events) 发送。
            (默认: :obj:`False`)
        stop (str or list, optional): 最多 :obj:`4` 个序列，API 在遇到这些序列时
            会停止生成进一步的 token。(默认: :obj:`None`)
        max_tokens (int, optional): 聊天补全中生成的最大 token 数量。
            输入 token 和生成 token 的总长度受模型上下文长度的限制。
            (默认: :obj:`None`)
        presence_penalty (float, optional): 介于 :obj:`-2.0` 和 :obj:`2.0` 之间的数字。
            正值会根据新 token 是否已经出现在目前文本中来对其进行惩罚，
            从而增加模型谈论新主题的可能性。 (默认: :obj:`0.0`)
        frequency_penalty (float, optional): 介于 :obj:`-2.0` 和 :obj:`2.0` 之间的数字。
            正值会根据新 token 在目前文本中的现有频率对其进行惩罚，
            从而降低模型逐字重复同一行的可能性。 (默认: :obj:`0.0`)
        logit_bias (dict, optional): 修改指定 token 出现在完成结果中的可能性。
            接受一个 JSON 对象，将 token (由其在分词器中的 token ID 指定) 映射到
            从 :obj:`-100` 到 :obj:`100` 的关联偏差值。(默认: :obj:`{}`)
        user (str, optional): 代表最终用户的唯一标识符，可帮助 OpenAI 监控和检测滥用行为。
            (默认: :obj:`""`)
    """
    temperature: float = 0  # openai default: 1.0 chatdev default: 0.2
    top_p: float = 1.0
    n: int = 1
    stream: bool = False
    stop: Optional[Union[str, Sequence[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    logit_bias: Dict = field(default_factory=dict)
    user: str = ""
    seed: int = 42
