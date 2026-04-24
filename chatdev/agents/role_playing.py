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
from typing import Dict, List, Optional, Sequence, Tuple

from chatdev.agents import (
    ChatAgent,
    TaskPlannerAgent,
    TaskSpecifyAgent,
)
from chatdev.agents.chat_agent import ChatAgentResponse
from chatdev.agents.messages import ChatMessage, UserChatMessage
from chatdev.agents.messages import SystemMessage
from chatdev.agents.typing import ModelType, RoleType, TaskType, PhaseType
from chatdev.utils import log_arguments, log_visualize


@log_arguments
class RolePlaying:
    r"""两个代理(agent)之间的角色扮演对话机制。

    参数 (Args):
        assistant_role_name (str): 助手扮演的角色名称。
        user_role_name (str): 用户扮演的角色名称。
        critic_role_name (str): 评论者扮演的角色名称。
            (默认: :obj:`"critic"`)
        task_prompt (str, optional): 待执行任务的提示词。
            (默认: :obj:`""`)
        with_task_specify (bool, optional): 是否使用任务细化代理 (task specify agent)。
            (默认: :obj:`True`)
        with_task_planner (bool, optional): 是否使用任务规划代理 (task planner agent)。
            (默认: :obj:`False`)
        with_critic_in_the_loop (bool, optional): 是否在循环中包含评论者 (critic)。
            (默认: :obj:`False`)
        model_type (ModelType, optional): 要使用的后端模型类型。
            (默认: :obj:`ModelType.GPT_3_5_TURBO`)
        task_type (TaskType, optional): 要执行的任务类型。
            (默认: :obj:`TaskType.AI_SOCIETY`)
        assistant_agent_kwargs (Dict, optional): 传递给助手代理的额外参数。
            (默认: :obj:`None`)
        user_agent_kwargs (Dict, optional): 传递给用户代理的额外参数。
            (默认: :obj:`None`)
        task_specify_agent_kwargs (Dict, optional): 传递给任务细化代理的额外参数。
            (默认: :obj:`None`)
        task_planner_agent_kwargs (Dict, optional): 传递给任务规划代理的额外参数。
            (默认: :obj:`None`)
        critic_kwargs (Dict, optional): 传递给评论者代理的额外参数。
            (默认: :obj:`None`)
        sys_msg_generator_kwargs (Dict, optional): 传递给系统消息生成器的额外参数。
            (默认: :obj:`None`)
        extend_sys_msg_meta_dicts (List[Dict], optional): 用于扩展系统消息元数据字典的列表。
            (默认: :obj:`None`)
        extend_task_specify_meta_dict (Dict, optional): 用于扩展任务细化元数据字典的字典。
            (默认: :obj:`None`)
    """

    def __init__(
            self,
            assistant_role_name: str,
            user_role_name: str,
            critic_role_name: str = "critic",
            task_prompt: str = "",
            assistant_role_prompt: str = "",
            user_role_prompt: str = "",
            user_role_type: Optional[RoleType] = None,
            assistant_role_type: Optional[RoleType] = None,
            with_task_specify: bool = True,
            with_task_planner: bool = False,
            with_critic_in_the_loop: bool = False,
            critic_criteria: Optional[str] = None,
            model_type: ModelType = ModelType.GPT_3_5_TURBO,
            task_type: TaskType = TaskType.AI_SOCIETY,
            assistant_agent_kwargs: Optional[Dict] = None,
            user_agent_kwargs: Optional[Dict] = None,
            task_specify_agent_kwargs: Optional[Dict] = None,
            task_planner_agent_kwargs: Optional[Dict] = None,
            critic_kwargs: Optional[Dict] = None,
            sys_msg_generator_kwargs: Optional[Dict] = None,
            extend_sys_msg_meta_dicts: Optional[List[Dict]] = None,
            extend_task_specify_meta_dict: Optional[Dict] = None,
            background_prompt: Optional[str] = "",
            memory = None,
    ) -> None:
        self.with_task_specify = with_task_specify
        self.with_task_planner = with_task_planner
        self.with_critic_in_the_loop = with_critic_in_the_loop
        self.model_type = model_type
        self.task_type = task_type
        self.memory = memory


        if with_task_specify:
            task_specify_meta_dict = dict()
            if self.task_type in [TaskType.AI_SOCIETY, TaskType.MISALIGNMENT]:
                task_specify_meta_dict.update(
                    dict(assistant_role=assistant_role_name,
                         user_role=user_role_name))
            if extend_task_specify_meta_dict is not None:
                task_specify_meta_dict.update(extend_task_specify_meta_dict)

            task_specify_agent = TaskSpecifyAgent(
                self.model_type,
                task_type=self.task_type,
                **(task_specify_agent_kwargs or {}),
            )
            self.specified_task_prompt = task_specify_agent.step(
                task_prompt,
                meta_dict=task_specify_meta_dict,
            )
            task_prompt = self.specified_task_prompt
        else:
            self.specified_task_prompt = None

        if with_task_planner:
            task_planner_agent = TaskPlannerAgent(
                self.model_type,
                **(task_planner_agent_kwargs or {}),
            )
            self.planned_task_prompt = task_planner_agent.step(task_prompt)
            task_prompt = f"{task_prompt}\n{self.planned_task_prompt}"
        else:
            self.planned_task_prompt = None

        self.task_prompt = task_prompt

        sys_msg_meta_dicts = [dict(chatdev_prompt=background_prompt, task=task_prompt)] * 2
        if (extend_sys_msg_meta_dicts is None and self.task_type in [TaskType.AI_SOCIETY, TaskType.MISALIGNMENT,
                                                                     TaskType.CHATDEV]):
            extend_sys_msg_meta_dicts = [dict(assistant_role=assistant_role_name, user_role=user_role_name)] * 2
        if extend_sys_msg_meta_dicts is not None:
            sys_msg_meta_dicts = [{**sys_msg_meta_dict, **extend_sys_msg_meta_dict} for
                                  sys_msg_meta_dict, extend_sys_msg_meta_dict in
                                  zip(sys_msg_meta_dicts, extend_sys_msg_meta_dicts)]

        self.assistant_sys_msg = SystemMessage(role_name=assistant_role_name, role_type=RoleType.DEFAULT,
                                               meta_dict=sys_msg_meta_dicts[0],
                                               content=assistant_role_prompt.format(**sys_msg_meta_dicts[0]))
        self.user_sys_msg = SystemMessage(role_name=user_role_name, role_type=RoleType.DEFAULT,
                                          meta_dict=sys_msg_meta_dicts[1],
                                          content=user_role_prompt.format(**sys_msg_meta_dicts[1]))

        self.assistant_agent: ChatAgent = ChatAgent(self.assistant_sys_msg, memory, model_type,
                                                    **(assistant_agent_kwargs or {}), )
        self.user_agent: ChatAgent = ChatAgent(self.user_sys_msg,memory, model_type, **(user_agent_kwargs or {}), )

        if with_critic_in_the_loop:
            raise ValueError("with_critic_in_the_loop not available")
            # if critic_role_name.lower() == "human":
            #     self.critic = Human(**(critic_kwargs or {}))
            # else:
            #     critic_criteria = (critic_criteria or "improving the task performance")
            #     critic_msg_meta_dict = dict(critic_role=critic_role_name, criteria=critic_criteria,
            #                                 **sys_msg_meta_dicts[0])
            #     self.critic_sys_msg = sys_msg_generator.from_dict(critic_msg_meta_dict,
            #                                                       role_tuple=(critic_role_name, RoleType.CRITIC), )
            #     self.critic = CriticAgent(self.critic_sys_msg, model_type, **(critic_kwargs or {}), )
        else:
            self.critic = None

    def init_chat(self, phase_type: PhaseType = None,
                  placeholders=None, phase_prompt=None):
        r"""通过重置助手和用户代理，使用聊天消息再次向代理发送系统消息来初始化聊天。
        返回助手的开头说明消息以及用户的回应消息。

        返回 (Returns):
            一个元组 (Tuple)，包含代表助手开头消息的 `AssistantChatMessage`，
            以及代表用户回应消息的 `ChatMessage` 列表。
        """
        if placeholders is None:
            placeholders = {}
        self.assistant_agent.reset()
        self.user_agent.reset()

        # refactored ChatDev
        content = phase_prompt.format(
            **({"assistant_role": self.assistant_agent.role_name} | placeholders)
        )
        retrieval_memory = self.assistant_agent.use_memory(content)
        if retrieval_memory!= None:
            placeholders["examples"] = retrieval_memory
        user_msg = UserChatMessage(
            role_name=self.user_sys_msg.role_name,
            role="user",
            content=content
            # content here will be concatenated with assistant role prompt (because we mock user and send msg to assistant) in the ChatAgent.step
        )
        pseudo_msg = copy.deepcopy(user_msg)
        pseudo_msg.role = "assistant"
        self.user_agent.update_messages(pseudo_msg)

        # here we concatenate to store the real message in the log
        log_visualize(self.user_agent.role_name,
                      "**[Start Chat]**\n\n[" + self.assistant_agent.system_message.content + "]\n\n" + content)
        return None, user_msg

    def process_messages(
            self,
            messages: Sequence[ChatMessage],
    ) -> ChatMessage:
        r"""处理聊天消息列表，返回处理后的消息。如果提供了多条消息，
        但 `with_critic_in_the_loop` 被设置为 `False`，则抛出 `ValueError`。
        如果没有提供消息，同样会抛出 `ValueError`。

        参数 (Args):
            messages (Sequence[ChatMessage]): 输入的聊天消息序列。

        返回 (Returns):
            单个 `ChatMessage`，表示处理后的消息。
        """
        if len(messages) == 0:
            raise ValueError("No messages to process.")
        if len(messages) > 1 and not self.with_critic_in_the_loop:
            raise ValueError("Got than one message to process. "
                             f"Num of messages: {len(messages)}.")
        elif self.with_critic_in_the_loop and self.critic is not None:
            processed_msg = self.critic.step(messages)
        else:
            processed_msg = messages[0]

        return processed_msg

    def step(
            self,
            user_msg: ChatMessage,
            assistant_only: bool,
    ) -> Tuple[ChatAgentResponse, ChatAgentResponse]:
        assert isinstance(user_msg, ChatMessage), print("broken user_msg: " + str(user_msg))

        # print("assistant...")
        user_msg_rst = user_msg.set_user_role_at_backend()
        assistant_response = self.assistant_agent.step(user_msg_rst)
        if assistant_response.terminated or assistant_response.msgs is None:
            return (
                ChatAgentResponse([assistant_response.msgs], assistant_response.terminated, assistant_response.info),
                ChatAgentResponse([], False, {}))
        assistant_msg = self.process_messages(assistant_response.msgs)
        if self.assistant_agent.info:
            return (ChatAgentResponse([assistant_msg], assistant_response.terminated, assistant_response.info),
                    ChatAgentResponse([], False, {}))
        self.assistant_agent.update_messages(assistant_msg)

        if assistant_only:
            return (
                ChatAgentResponse([assistant_msg], assistant_response.terminated, assistant_response.info),
                ChatAgentResponse([], False, {})
            )

        # print("user...")
        assistant_msg_rst = assistant_msg.set_user_role_at_backend()
        user_response = self.user_agent.step(assistant_msg_rst)
        if user_response.terminated or user_response.msgs is None:
            return (ChatAgentResponse([assistant_msg], assistant_response.terminated, assistant_response.info),
                    ChatAgentResponse([user_response], user_response.terminated, user_response.info))
        user_msg = self.process_messages(user_response.msgs)
        if self.user_agent.info:
            return (ChatAgentResponse([assistant_msg], assistant_response.terminated, assistant_response.info),
                    ChatAgentResponse([user_msg], user_response.terminated, user_response.info))
        self.user_agent.update_messages(user_msg)

        return (
            ChatAgentResponse([assistant_msg], assistant_response.terminated, assistant_response.info),
            ChatAgentResponse([user_msg], user_response.terminated, user_response.info),
        )
