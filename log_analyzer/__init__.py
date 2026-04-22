"""
log_analyzer - ChatDev 日志结构化解析模块

将 ChatDev 生成的 .log 文件解析为结构化 JSON，
便于程序化分析、bug 识别和统计。

Quick Start::

    from log_analyzer import LogParser

    parser = LogParser()

    # 单文件解析
    result = parser.parse("path/to/log.log")

    # 批量解析
    results = parser.parse_batch("path/to/dataset_mini/")

    # 验证输出
    from log_analyzer.schema import validate
    is_valid, errors = validate(result)
"""

from .parser import LogParser
from .event_types import EventType, RawEntry
from .schema import validate
from .convert_to_playbook import api_to_playbook
from .bug_detector import scan_playbook_for_bug_1_1, check_constraint_violation, scan_playbook_for_bug_1_3, scan_playbook_for_bug_2_2

__all__ = [
    "LogParser",
    "EventType",
    "RawEntry",
    "validate",
    "api_to_playbook",
    "scan_playbook_for_bug_1_1",
    "check_constraint_violation",
    "scan_playbook_for_bug_1_3",
    "scan_playbook_for_bug_2_2",
]


def parse_log(log_path: str, output_path: str = None, **kwargs) -> dict:
    """便捷函数：解析单个日志文件。

    Args:
        log_path:    日志文件路径
        output_path: JSON 输出路径（默认同目录同名 .json）
        **kwargs:    传递给 LogParser 构造函数的参数

    Returns:
        解析后的 dict
    """
    parser = LogParser(**kwargs)
    return parser.parse(log_path, output_path)


def parse_batch(dir_path: str, output_dir: str = None, **kwargs) -> list:
    """便捷函数：批量解析目录下所有日志。

    Args:
        dir_path:   顶层目录路径
        output_dir: JSON 输出目录（默认各日志所在目录）
        **kwargs:   传递给 LogParser 构造函数的参数

    Returns:
        所有解析结果列表
    """
    parser = LogParser(**kwargs)
    return parser.parse_batch(dir_path, output_dir)
