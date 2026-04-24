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
import argparse
import logging
import os

import dotenv

dotenv.load_dotenv(override=True)

from chatdev.agents.typing import ModelType
from chatdev.path_utils import get_workspace_root, resolve_company_config_paths

from chatdev.chat_chain import ChatChain

try:
    from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
    from openai.types.chat.chat_completion_message import FunctionCall

    openai_new_api = True  # new openai api version
except ImportError:
    openai_new_api = False  # old openai api version
    print(
        "Warning: Your OpenAI version is outdated. \n "
        "Please update as specified in requirement.txt. \n "
        "The old API interface is deprecated and will no longer be supported.")


def get_config(company):
    """Return the three resolved ChatChain configuration file paths for a company."""
    return resolve_company_config_paths(company)


parser = argparse.ArgumentParser(description='argparse')
parser.add_argument('--config', type=str, default="Default",
                    help="Name of config, which is used to load configuration under config/")
parser.add_argument('--org', type=str, default="DefaultOrganization",
                    help="Name of organization, your software will be generated under the workspace root as <name>_<org>_<timestamp>")
parser.add_argument('--task', type=str, default="Create a CLI tool that takes a text file path as input and outputs the total word count. The tool should handle basic punctuation and count sequences of alphanumeric characters as words. Output the count to the console.",
                    help="Prompt of software")
parser.add_argument('--name', type=str, default="CLI_Text_File_Word_Counter",
                    help="Name of software, your software will be generated under the workspace root as <name>_<org>_<timestamp>")
parser.add_argument('--model', type=str, default="GPT_4O",
                    help="GPT Model, choose from {'GPT_3_5_TURBO', 'GPT_4', 'GPT_4_TURBO', 'GPT_4O', 'GPT_4O_MINI'}")
parser.add_argument('--path', type=str, default="",
                    help="Your file directory, ChatDev will build upon your software in the Incremental mode")

# ========== 三种互斥运行模式 ==========
# 不传任何模式参数 → 默认模式（纯 API 调用，无 git 快照，无 JSONL 记录）
# --snapshot       → 快照模式（真实 API + git 追踪 + JSONL 记录）
# --replay <path>  → 回放模式（从 JSONL 重放，不调用真实 API）
# --hybrid <path>  → 混合模式（先回放前 k-1 个节点，从第 k 个节点开始调用真实 API）
mode_group = parser.add_mutually_exclusive_group()
mode_group.add_argument('--snapshot', type=str, nargs='?', const='', default=None,
                        metavar='OUTPUT_PATH',
                        help="快照模式：真实 API 调用 + git 追踪 + JSONL 记录。"
                             "可选指定 JSONL 输出路径（默认为 <workspace_root>/api_records.jsonl）")
mode_group.add_argument('--replay', type=str, default=None, metavar='JSONL_PATH',
                        help="回放模式：从指定 JSONL 文件回放，不调用真实 API")
mode_group.add_argument('--hybrid', type=str, default=None, metavar='JSONL_PATH',
                        help="混合模式：先从 JSONL 回放，到达指定节点后切换为真实 API 调用")

# hybrid 专属参数
parser.add_argument('--hybrid-node', type=int, default=1,
                    help="仅用于 --hybrid 模式：从第 k 个节点开始调用真实 API（1-based，范围 1~n）。"
                         "例如 --hybrid-node 5 表示前 4 个节点回放，从第 5 个节点开始实时调用。默认值为 1（全部实时）。")

args = parser.parse_args()

# ========== 参数校验 ==========
if args.hybrid_node != 1 and args.hybrid is None:
    parser.error("--hybrid-node 只能与 --hybrid 一起使用")

if args.hybrid and args.hybrid_node < 1:
    parser.error("--hybrid-node 必须 >= 1（1-based 索引，表示从第几个节点开始调用真实 API）")

# ========== 确定运行模式并设置环境变量 ==========
if args.snapshot is not None:
    run_mode = "snapshot"
elif args.replay is not None:
    run_mode = "replay"
elif args.hybrid is not None:
    run_mode = "hybrid"
else:
    run_mode = "default"

os.environ["CHATDEV_RUN_MODE"] = run_mode

config_path, config_phase_path, config_role_path = get_config(args.config)
workspace_root = get_workspace_root()

if run_mode == "snapshot" and args.snapshot:
    # 用户指定了自定义 JSONL 输出路径
    os.environ["CHATDEV_SNAPSHOT_OUTPUT"] = args.snapshot
elif run_mode == "snapshot":
    os.environ["CHATDEV_SNAPSHOT_OUTPUT"] = str(workspace_root / "api_records.jsonl")

if run_mode == "replay":
    os.environ["CHATDEV_REPLAY_JSONL"] = args.replay

if run_mode == "hybrid":
    os.environ["CHATDEV_HYBRID_JSONL"] = args.hybrid
    os.environ["CHATDEV_HYBRID_NODE"] = str(args.hybrid_node)

# Start ChatDev

# ----------------------------------------
#          Init ChatChain
# ----------------------------------------
args2type = {'GPT_3_5_TURBO': ModelType.GPT_3_5_TURBO,
             'GPT_4': ModelType.GPT_4,
            #  'GPT_4_32K': ModelType.GPT_4_32k,
             'GPT_4_TURBO': ModelType.GPT_4_TURBO,
            #  'GPT_4_TURBO_V': ModelType.GPT_4_TURBO_V
            'GPT_4O': ModelType.GPT_4O,
            'GPT_4O_MINI': ModelType.GPT_4O_MINI,
             }
if openai_new_api:
    args2type['GPT_3_5_TURBO'] = ModelType.GPT_3_5_TURBO_NEW

chat_chain = ChatChain(config_path=config_path,
                       config_phase_path=config_phase_path,
                       config_role_path=config_role_path,
                       task_prompt=args.task,
                       project_name=args.name,
                       org_name=args.org,
                       model_type=args2type[args.model],
                       code_path=args.path)

# ----------------------------------------
#          Init Log
# ----------------------------------------
logging.basicConfig(filename=chat_chain.log_filepath, level=logging.INFO,
                    format='[%(asctime)s %(levelname)s] %(message)s',
                    datefmt='%Y-%d-%m %H:%M:%S', encoding="utf-8")

# ----------------------------------------
#          Pre Processing
# ----------------------------------------

chat_chain.pre_processing()

# ----------------------------------------
#          Personnel Recruitment
# ----------------------------------------

chat_chain.make_recruitment()

# ----------------------------------------
#          Chat Chain
# ----------------------------------------

chat_chain.execute_chain()

# ----------------------------------------
#          Post Processing
# ----------------------------------------

chat_chain.post_processing()
