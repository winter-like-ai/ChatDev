"""
event_types.py - ChatDev 日志事件类型定义

定义了所有可识别的日志事件类型枚举 和 原始日志条目的数据结构。
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EventType(Enum):
    """ChatDev 日志中可识别的全部事件类型。

    主要事件（几乎所有日志都会出现）:
        PREPROCESSING         - 会话元信息
        CHATTING               - Phase 参数表（@log_arguments 装饰器生成）
        ROLE_PLAYING           - 角色扮演配置表（@log_arguments 装饰器生成）
        START_CHAT             - 对话开始
        AGENT_MESSAGE          - Agent 之间的消息交互
        OPENAI_USAGE           - Token 消耗统计
        SEMINAR_CONCLUSION     - Phase 讨论结论
        UPDATE_CODES           - 代码更新 diff
        REWRITE_CODES          - 代码写入文件系统
        SOFTWARE_INFO          - 累计统计信息
        EXECUTE_DETAIL         - Phase 执行顺序
        POST_INFO              - 最终统计
        GIT_INFO               - Git 操作日志
        TEST_REPORTS           - 测试结果报告

    附加事件（不一定出现在所有日志中）:
        TEST_INFO              - 测试通过信息
        CMD_EXECUTE            - pip install 等命令
        HUMAN_AGENT_INTERACTION - 人机交互提示
        USER_PROVIDED_COMMENTS  - 用户反馈内容
        TASK_PROMPT_IMPROVE     - Prompt 自优化
        MEMORY_RETRIEVAL        - Memory 检索
        HYBRID_REPLAY           - 混合模式控制
        LOADED                  - 快照记录加载
        HTTP_REQUEST            - API 请求
        FLASK_NOT_START         - Flask 状态
        FILES_READ              - 增量开发文件加载
        MODULE_NOT_FOUND        - 模块导入错误修复

    特殊:
        UNKNOWN                - 无法识别的日志行
    """

    # --- 主要事件 ---
    PREPROCESSING = "preprocessing"
    CHATTING = "chatting"
    ROLE_PLAYING = "role_playing"
    START_CHAT = "start_chat"
    AGENT_MESSAGE = "agent_message"
    OPENAI_USAGE = "openai_usage"
    SEMINAR_CONCLUSION = "seminar_conclusion"
    UPDATE_CODES = "update_codes"
    REWRITE_CODES = "rewrite_codes"
    SOFTWARE_INFO = "software_info"
    EXECUTE_DETAIL = "execute_detail"
    POST_INFO = "post_info"
    GIT_INFO = "git_info"
    TEST_REPORTS = "test_reports"

    # --- 附加事件 ---
    TEST_INFO = "test_info"
    CMD_EXECUTE = "cmd_execute"
    HUMAN_AGENT_INTERACTION = "human_agent_interaction"
    USER_PROVIDED_COMMENTS = "user_provided_comments"
    TASK_PROMPT_IMPROVE = "task_prompt_improve"
    MEMORY_RETRIEVAL = "memory_retrieval"
    HYBRID_REPLAY = "hybrid_replay"
    LOADED = "loaded"
    HTTP_REQUEST = "http_request"
    FLASK_NOT_START = "flask_not_start"
    FILES_READ = "files_read"
    MODULE_NOT_FOUND = "module_not_found"

    # --- 特殊 ---
    UNKNOWN = "unknown"


@dataclass
class RawEntry:
    """原始日志条目，由 LogParser._split_entries 产生。

    Attributes:
        timestamp: 原始时间戳字符串，如 "2026-31-03 21:29:16"
        level: 日志级别，如 "INFO"
        sender: 发送者角色名，如 "System", "Chief Product Officer"，
                若日志行无 sender 则为 None
        content: 条目正文内容（可能跨多行）
        line_start: 该条目在原始日志文件中的起始行号（1-indexed）
        line_end: 该条目在原始日志文件中的结束行号（1-indexed, inclusive）
    """

    timestamp: str
    level: str
    sender: Optional[str]
    content: str
    line_start: int
    line_end: int
