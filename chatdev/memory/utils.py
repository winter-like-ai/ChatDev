import subprocess
import json
import yaml
import time
import logging
from easydict import EasyDict
import openai
from openai import OpenAI
import numpy as np
import os
from abc import ABC, abstractmethod
import tiktoken
from typing import Any, Dict
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential
)
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
if 'BASE_URL' in os.environ:
    BASE_URL = os.environ['BASE_URL']
else:
    BASE_URL = None

def getFilesFromType(sourceDir, filetype):
    """获取指定目录下某类型特征(后缀)的所有文件路径列表。"""
    files = []
    for root, directories, filenames in os.walk(sourceDir):
        for filename in filenames:
            if filename.endswith(filetype):
                files.append(os.path.join(root, filename))
    return files

def cmd(command: str):
    """通过子进程执行 Shell 命令并返回标准输出文本。"""
    print(">> {}".format(command))
    text = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE).stdout
    return text

def get_easyDict_from_filepath(path: str):
    """读取指定路径下的 JSON 或 YAML 配置文件，并转换成 EasyDict 对象以链式访问。"""
    # print(path)
    if path.endswith('.json'):
        with open(path, 'r', encoding="utf-8") as file:
            config_map = json.load(file, strict=False)
            config_easydict = EasyDict(config_map)
            return config_easydict
    if path.endswith('.yaml'):
        file_data = open(path, 'r', encoding="utf-8").read()
        config_map = yaml.load(file_data, Loader=yaml.FullLoader)
        config_easydict = EasyDict(config_map)
        return config_easydict
    return None


def calc_max_token(messages, model):
    """使用 tiktoken 根据消息列表和给定模型计算剩余可用于补全的最大 token 数量。"""
    string = "\n".join([message["content"] for message in messages])
    encoding = tiktoken.encoding_for_model(model)
    num_prompt_tokens = len(encoding.encode(string))
    gap_between_send_receive = 50
    num_prompt_tokens += gap_between_send_receive

    num_max_token_map = {
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16384,
        "gpt-3.5-turbo-0613": 4096,
        "gpt-3.5-turbo-16k-0613": 16384,
        "gpt-4": 8192,
        "gpt-4-0613": 8192,
        "gpt-4-32k": 32768,
        "gpt-4o": 4096, #100000
        "gpt-4o-mini": 16384, #100000
    }
    num_max_token = num_max_token_map[model]
    num_max_completion_tokens = num_max_token - num_prompt_tokens
    return num_max_completion_tokens


class ModelBackend(ABC):
    r"""模型后端的基类接口。
    可以是 OpenAI API、本地 LLM 或者用于单元测试的桩对象。"""

    @abstractmethod
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        r"""向后端模型发起查询并运行请求。

        抛出异常 (Raises):
            RuntimeError: 如果 OpenAI API 的返回值并非预期的字典类型。

        返回 (Returns):
            Dict[str, Any]: 所有后端必须返回类似 OpenAI 返回格式的字典对象。
        """
        pass

class OpenAIModel(ModelBackend):
    r"""封装为统一 ModelBackend 接口的 OpenAI API 类。"""

    def __init__(self, model_type, model_config_dict: Dict=None) -> None:
        super().__init__()
        self.model_type = model_type
        self.model_config_dict = model_config_dict
        if self.model_config_dict == None:
            self.model_config_dict = {"temperature": 0.2,
                                "top_p": 1.0,
                                "n": 1,
                                "stream": False,
                                "frequency_penalty": 0.0,
                                "presence_penalty": 0.0,
                                "logit_bias": {},
                                }
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    @retry(wait=wait_exponential(min=5, max=60), stop=stop_after_attempt(5))
    def run(self, messages) :
        if BASE_URL:
            client = openai.OpenAI(
                api_key=OPENAI_API_KEY,
                base_url=BASE_URL,
            )
        else:
            client = openai.OpenAI(
                api_key=OPENAI_API_KEY
            )
        current_retry = 0
        max_retry = 5

        string = "\n".join([message["content"] for message in messages])
        encoding = tiktoken.encoding_for_model(self.model_type)
        num_prompt_tokens = len(encoding.encode(string))
        gap_between_send_receive = 15 * len(messages)
        num_prompt_tokens += gap_between_send_receive

        num_max_token_map = {
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "gpt-3.5-turbo-0613": 4096,
            "gpt-3.5-turbo-16k-0613": 16384,
            "gpt-4": 8192,
            "gpt-4-0613": 8192,
            "gpt-4-32k": 32768,
            "gpt-4o": 4096, #100000
            "gpt-4o-mini": 16384, #100000
        }
        response = client.chat.completions.create(messages = messages,
        model = "gpt-3.5-turbo-16k",
        temperature = 0.2,
        top_p = 1.0,
        n = 1,
        stream = False,
        frequency_penalty = 0.0,
        presence_penalty = 0.0,
        logit_bias = {},
        ).model_dump()
        response_text = response['choices'][0]['message']['content']



        num_max_token = num_max_token_map[self.model_type]
        num_max_completion_tokens = num_max_token - num_prompt_tokens
        self.model_config_dict['max_tokens'] = num_max_completion_tokens
        log_and_print_online(
            "InstructionStar generation:\n**[OpenAI_Usage_Info Receive]**\nprompt_tokens: {}\ncompletion_tokens: {}\ntotal_tokens: {}\n".format(
                response["usage"]["prompt_tokens"], response["usage"]["completion_tokens"],
                response["usage"]["total_tokens"]))
        self.prompt_tokens += response["usage"]["prompt_tokens"]
        self.completion_tokens += response["usage"]["completion_tokens"]
        self.total_tokens += response["usage"]["total_tokens"]
        
        if not isinstance(response, Dict):
            raise RuntimeError("Unexpected return from OpenAI API")
        return response

    
def now():
    """获取并返回当前时间的字符串格式（如 YYYYMMDDHHMMSS）。"""
    return time.strftime("%Y%m%d%H%M%S", time.localtime())

def log_and_print_online(content=None):
    """将指定内容打印至控制台并行记录到日志中。"""
    if  content is not None:
        print(content)
        logging.info(content)
