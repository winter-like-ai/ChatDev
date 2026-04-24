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
import inspect
from typing import Any, Callable, Dict, Optional, Set, Tuple, TypeVar, Union

from chatdev.agents.typing import RoleType

T = TypeVar('T')


def return_prompt_wrapper(
    cls: T,
    func: Callable,
) -> Callable[..., Union[T, tuple]]:
    r"""将函数的返回值（如果是字符串）转换为输入类实例的包装器。

    参数 (Args):
        cls (type): 要转换成的类。
        func (Callable): 要装饰的函数。

    返回 (Returns):
        Callable[..., Union[T, tuple]]: 装饰后的函数，如果返回值为字符串，
            则返回被装饰类的实例。
    """

    def wrapper(*args: Any, **kwargs: Any) -> Union[T, tuple]:
        r"""执行转换为 :obj:`TextPrompt` 实例的包装器函数。

        参数 (Args):
            *args (Any): 可变长度参数列表。
            **kwargs (Any): 任意关键字参数。

        返回 (Returns):
            Union[TextPrompt, tuple]: 转换后的返回值。
        """
        result = func(*args, **kwargs)
        if isinstance(result, str) and not isinstance(result, cls):
            return cls(result)
        elif isinstance(result, tuple):
            new_result = tuple(
                cls(item) if isinstance(item, str)
                and not isinstance(item, cls) else item for item in result)
            return new_result
        return result

    # # Preserve the original function's attributes
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__

    return wrapper


def wrap_prompt_functions(cls: T) -> T:
    r"""使用 :obj:`return_prompt_wrapper` 装饰器包装继承自 :obj:`str` 
    的类的所有函数的装饰器。

    参数 (Args):
        cls (type): 要装饰的类。

    返回 (Returns):
        type: 包含已包装函数的被装饰类。
    """
    excluded_attrs = {'__init__', '__new__', '__str__', '__repr__'}
    for attr_name in dir(cls):
        attr_value = getattr(cls, attr_name)
        if callable(attr_value) and attr_name not in excluded_attrs:
            if inspect.isroutine(attr_value):
                setattr(cls, attr_name, return_prompt_wrapper(cls, attr_value))
    return cls


@wrap_prompt_functions
class TextPrompt(str):
    r"""表示文本提示(text prompt)的类。:obj:`TextPrompt` 类扩展了内置的
    :obj:`str` 类，提供了一个可以检索提示中关键字集合的属性。

    属性 (Attributes):
        key_words (set): 包含提示中关键字的字符串集合。
    """

    @property
    def key_words(self) -> Set[str]:
        r"""返回包含提示中关键字的字符串集合。
        """
        from chatdev.agents.utils import get_prompt_template_key_words
        return get_prompt_template_key_words(self)

    def format(self, *args: Any, **kwargs: Any) -> 'TextPrompt':
        r"""重写内置的 :obj:`str.format` 方法，允许在格式化字符串中使用默认值。
        此功能用于支持部分字符串的格式化。

        参数 (Args):
            *args (Any): 可变长度参数列表。
            **kwargs (Any): 任意关键字参数。

        返回 (Returns):
            TextPrompt: 一个新的 :obj:`TextPrompt` 对象，其中的格式字符串
                已被格式化替换。
        """
        default_kwargs = {key: '{' + f'{key}' + '}' for key in self.key_words}
        default_kwargs.update(kwargs)
        return TextPrompt(super().format(*args, **default_kwargs))


@wrap_prompt_functions
class CodePrompt(TextPrompt):
    r"""表示代码提示(code prompt)的类。它扩展了 :obj:`TextPrompt` 类，
    并增加了一个 :obj:`code_type` 属性。

    参数 (Args):
        code_string (str): 提示的代码字符串。
        code_type (str, optional): 代码的类型。默认值为 None。
    """

    def __new__(cls, *args: Any, **kwargs: Any) -> 'CodePrompt':
        r"""创建一个新的 :obj:`CodePrompt` 类实例。

        参数 (Args):
            *args (Any): 位置参数。
            **kwargs (Any): 关键字参数。

        返回 (Returns):
            CodePrompt: 创建的 :obj:`CodePrompt` 实例。
        """
        code_type = kwargs.pop('code_type', None)
        instance = super().__new__(cls, *args, **kwargs)
        instance._code_type = code_type
        return instance

    @property
    def code_type(self) -> Optional[str]:
        r"""返回代码的类型。

        返回 (Returns):
            Optional[str]: 代码的类型。
        """
        return self._code_type

    def set_code_type(self, code_type: str) -> None:
        r"""设置代码的类型。

        参数 (Args):
            code_type (str): 代码的类型。
        """
        self._code_type = code_type

    def execute(
            self,
            global_vars: Optional[Dict] = None) -> Tuple[str, Optional[Dict]]:
        r"""执行代码字符串。如果发生错误，错误将被捕获并返回 traceback。
        否则，将返回输出字符串和局部变量。

        参数 (Args):
            global_vars (Dict, optional): 代码执行期间要使用的全局变量。
                (默认: :obj:`None`)

        返回 (Returns):
            Tuple[str, Optional[Dict]]: 包含输出字符串和局部变量的元组。
        """
        # NOTE: Only supports Python code for now.
        try:
            # Execute the code string
            import io
            import sys
            output_str = io.StringIO()
            sys.stdout = output_str

            global_vars = global_vars or globals()
            local_vars = {}
            exec(
                self,
                global_vars,
                local_vars,
            )
            sys.stdout = sys.__stdout__
            output_str.seek(0)

            # If there was no error, return the output and local variables
            return output_str.read(), local_vars

        except Exception:
            import traceback
            traceback_str = traceback.format_exc()
            sys.stdout = sys.__stdout__
            # If there was an error, return the traceback
            return traceback_str, None


# flake8: noqa :E501
class TextPromptDict(Dict[Any, TextPrompt]):
    r"""从键映射到 :obj:`TextPrompt` 对象的字典类。
    """
    EMBODIMENT_PROMPT = TextPrompt(
        """You are the physical embodiment of the {role} who is working on solving a task: {task}.
You can do things in the physical world including browsing the Internet, reading documents, drawing images, creating videos, executing code and so on.
Your job is to perform the physical actions necessary to interact with the physical world.
You will receive thoughts from the {role} and you will need to perform the actions described in the thoughts.
You can write a series of simple commands in Python to act.
You can perform a set of actions by calling the available Python functions.
You should perform actions based on the descriptions of the functions.

Here is your action space:
{action_space}

You should only perform actions in the action space.
You can perform multiple actions.
You can perform actions in any order.
First, explain the actions you will perform and your reasons, then write Python code to implement your actions.
If you decide to perform actions, you must write Python code to implement the actions.
You may print intermediate results if necessary.""")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.update({RoleType.EMBODIMENT: self.EMBODIMENT_PROMPT})
