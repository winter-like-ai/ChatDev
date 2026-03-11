import os
import sys
import openai
from openai import OpenAI

# 使用统一的 API 配置模块，支持 OpenAI / DeepSeek 自动回退
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from agent_adapter.api_config import get_api_key, get_base_url, create_openai_client

OPENAI_API_KEY = get_api_key()
BASE_URL = get_base_url()
import time
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    wait_fixed
)
from utils import log_and_print_online
sys.path.append(os.path.join(os.getcwd(),"ecl"))

class OpenAIEmbedding:
    def __init__(self, **params):
        self.code_prompt_tokens = 0
        self.text_prompt_tokens = 0
        self.code_total_tokens = 0
        self.text_total_tokens = 0

        self.prompt_tokens = 0
        self.total_tokens = 0

    @retry(wait=wait_random_exponential(min=2, max=5), stop=stop_after_attempt(10))
    def get_text_embedding(self,text: str):
            # 每次动态获取 client，确保能正确读到 dotenv 加载的 Key
            client = create_openai_client()

            if len(text)>8191:
                  text = text[:8190]
            response = client.embeddings.create(input = text, model="text-embedding-ada-002").model_dump()
            embedding = response['data'][0]['embedding']
            log_and_print_online(
            "Get text embedding from {}:\n**[OpenAI_Usage_Info Receive]**\nprompt_tokens: {}\ntotal_tokens: {}\n".format(
                response["model"],response["usage"]["prompt_tokens"],response["usage"]["total_tokens"]))
            self.text_prompt_tokens += response["usage"]["prompt_tokens"]
            self.text_total_tokens += response["usage"]["total_tokens"]
            self.prompt_tokens += response["usage"]["prompt_tokens"]
            self.total_tokens += response["usage"]["total_tokens"]

            return embedding

    @retry(wait=wait_random_exponential(min=10, max=60), stop=stop_after_attempt(10))
    def get_code_embedding(self,code: str):
            # 每次动态获取 client，确保能正确读到 dotenv 加载的 Key
            client = create_openai_client()
            if len(code) == 0:
                  code = "#"
            elif len(code) >8191:
                  code = code[0:8190]
            response = client.embeddings.create(input=code, model="text-embedding-ada-002").model_dump()
            embedding = response['data'][0]['embedding']
            log_and_print_online(
            "Get code embedding from {}:\n**[OpenAI_Usage_Info Receive]**\nprompt_tokens: {}\ntotal_tokens: {}\n".format(
                response["model"],response["usage"]["prompt_tokens"],response["usage"]["total_tokens"]))
            
            self.code_prompt_tokens += response["usage"]["prompt_tokens"]
            self.code_total_tokens += response["usage"]["total_tokens"]
            self.prompt_tokens += response["usage"]["prompt_tokens"]
            self.total_tokens += response["usage"]["total_tokens"]

            return embedding


