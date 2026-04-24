"""
analyzer_base.py - Bug 分析器基类与注册中心

提供:
  - AnalyzerBase: Bug 分析器抽象基类
  - BugAnalyzerRegistry: 分析器注册中心

设计原则:
  - 每个具体分析器对应一种 bug_type_id
  - 输入: 一个 event (dict)
  - 输出: 是否出现该类错误 (bool) + 可选的详细信息 (dict)
  - bug 类型与检测方法尚未定义，此模块仅提供接口预留

使用示例::

    from chatdev.analyzer.analyzer_base import AnalyzerBase, BugAnalyzerRegistry

    class RepeatOutputAnalyzer(AnalyzerBase):
        bug_type_id = "BUG_001"
        bug_type_name = "重复输出"

        def check_event(self, event):
            # 具体检测逻辑（待定义）
            return False, None

    registry = BugAnalyzerRegistry()
    registry.register(RepeatOutputAnalyzer())

    parsed_data = parser.parse("log.log")
    parsed_data["_analysis"] = registry.run_all(parsed_data)
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


class AnalyzerBase(ABC):
    """Bug 分析器抽象基类。

    子类必须定义:
        - bug_type_id:   str, Bug 类型编号，如 "BUG_001"
        - bug_type_name: str, Bug 类型名称，如 "重复输出"
        - check_event(): 检查单个 event 是否出现该类 bug
    """

    bug_type_id: str = ""
    bug_type_name: str = ""

    @abstractmethod
    def check_event(self, event: dict) -> Tuple[bool, Optional[dict]]:
        """检查单个 event 是否出现该类 bug。

        Args:
            event: 从 parsed JSON 的 events 列表中取出的单个事件 dict，
                   包含 event_id, event_type, timestamp, sender 等字段

        Returns:
            (is_buggy, detail):
                is_buggy: 是否检测到该类 bug
                detail:   可选的详细信息 dict（触发原因、严重程度等），
                          未检测到 bug 时应返回 None
        """
        pass

    def analyze_all(self, parsed_data: dict) -> List[dict]:
        """对所有 events 执行检查，返回检测结果列表。

        Args:
            parsed_data: LogParser.parse() 的完整输出 dict

        Returns:
            检测到的 bug 列表，每项包含:
                - event_id: 触发事件的 ID
                - bug_type_id: Bug 类型编号
                - bug_type_name: Bug 类型名称
                - detail: 详细信息
        """
        results = []
        for event in parsed_data.get("events", []):
            is_buggy, detail = self.check_event(event)
            if is_buggy:
                results.append({
                    "event_id": event.get("event_id"),
                    "bug_type_id": self.bug_type_id,
                    "bug_type_name": self.bug_type_name,
                    "detail": detail,
                })
        return results


class BugAnalyzerRegistry:
    """Bug 分析器注册中心，管理多种 bug 检测器。

    使用方法::

        registry = BugAnalyzerRegistry()
        registry.register(MyBugAnalyzer())
        registry.register(AnotherBugAnalyzer())

        all_bugs = registry.run_all(parsed_data)
        parsed_data["_analysis"] = all_bugs
    """

    def __init__(self):
        self._analyzers: Dict[str, AnalyzerBase] = {}

    def register(self, analyzer: AnalyzerBase) -> None:
        """注册一个 bug 分析器。

        Args:
            analyzer: AnalyzerBase 子类的实例

        Raises:
            ValueError: 如果 bug_type_id 为空
            TypeError:  如果 analyzer 不是 AnalyzerBase 子类
        """
        if not isinstance(analyzer, AnalyzerBase):
            raise TypeError(
                f"analyzer 必须是 AnalyzerBase 子类，"
                f"得到 {type(analyzer).__name__}"
            )
        if not analyzer.bug_type_id:
            raise ValueError("analyzer.bug_type_id 不能为空")
        self._analyzers[analyzer.bug_type_id] = analyzer

    def unregister(self, bug_type_id: str) -> None:
        """取消注册指定编号的分析器。"""
        self._analyzers.pop(bug_type_id, None)

    def list_analyzers(self) -> List[dict]:
        """列出所有已注册的分析器信息。

        Returns:
            [{"bug_type_id": "...", "bug_type_name": "..."}, ...]
        """
        return [
            {"bug_type_id": a.bug_type_id, "bug_type_name": a.bug_type_name}
            for a in self._analyzers.values()
        ]

    def run_all(self, parsed_data: dict) -> dict:
        """运行所有已注册的分析器。

        Args:
            parsed_data: LogParser.parse() 的完整输出

        Returns:
            {
                "total_bugs_found": N,
                "by_type": {"BUG_001": [...], "BUG_002": [...]},
                "analyzers_used": ["BUG_001", "BUG_002"]
            }
        """
        result = {
            "total_bugs_found": 0,
            "by_type": {},
            "analyzers_used": list(self._analyzers.keys()),
        }
        for bug_id, analyzer in self._analyzers.items():
            bugs = analyzer.analyze_all(parsed_data)
            result["by_type"][bug_id] = bugs
            result["total_bugs_found"] += len(bugs)
        return result

    def run_single(self, bug_type_id: str, parsed_data: dict) -> List[dict]:
        """运行指定编号的单个分析器。

        Args:
            bug_type_id: Bug 类型编号
            parsed_data: LogParser.parse() 的完整输出

        Returns:
            检测到的 bug 列表

        Raises:
            ValueError: 如果 bug_type_id 未注册
        """
        if bug_type_id not in self._analyzers:
            raise ValueError(
                f"未注册的 bug_type_id: {bug_type_id}. "
                f"已注册: {list(self._analyzers.keys())}"
            )
        return self._analyzers[bug_type_id].analyze_all(parsed_data)
