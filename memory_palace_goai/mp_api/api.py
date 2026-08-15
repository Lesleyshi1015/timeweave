"""
TimeWeave API 接口契约层。

定义 MPService 抽象基类，供 StubEngine 和 Engine 继承实现。
所有方法返回 dict，保持黑盒保护（框架开源、引擎闭源）。
"""

from abc import ABC, abstractmethod
from typing import Any


class MPService(ABC):
    """
    TimeWeave 服务接口契约。

    提供三层能力：
    - Layer 1: 记忆检索与索引（search / index）
    - Layer 2: 时间线、知识图谱、预测（timeline / graph / predict）
    - Layer 3: 归档与读取（archive / read）
    """

    # ── Layer 1: 记忆检索 ────────────────────────────────────────────────

    @abstractmethod
    def layer1_search(
        self,
        query: str,
        top_k: int = 10,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        语义检索记忆库。

        Args:
            query: 检索查询字符串。
            top_k: 返回结果数量上限。
            context: 可选的上下文信息（如用户身份、当前会话状态）。

        Returns:
            {
                "summary": str,        # 检索结果摘要
                "results": list[dict], # 匹配的记忆条目列表
                "confidence": float,   # 整体置信度 [0, 1]
            }
        """

    @abstractmethod
    def layer1_index(
        self,
        memory_id: str,
        timestamp: str,
        content: str | None = None,
    ) -> dict[str, Any]:
        """
        将记忆条目写入索引。

        Args:
            memory_id: 记忆唯一标识。
            timestamp: ISO 8601 时间戳。
            content: 记忆内容（可为 None，表示仅索引元数据）。

        Returns:
            {
                "status": str,      # "indexed" | "error"
                "memory_id": str,   # 确认的记忆 ID
            }
        """

    # ── Layer 2: 时间线 & 图谱 & 预测 ────────────────────────────────────

    @abstractmethod
    def layer2_timeline(
        self,
        memory_ids: list[str],
        time_range: str = "24h",
    ) -> dict[str, Any]:
        """
        从记忆中提取时间线事件。

        Args:
            memory_ids: 记忆 ID 列表。
            time_range: 时间范围（如 "24h", "7d", "30d"）。

        Returns:
            {
                "timeline_events": list[dict],  # 按时间排序的事件列表
                "confidence": float,            # 置信度 [0, 1]
            }
        """

    @abstractmethod
    def layer2_extract_time(self, content: str) -> dict[str, Any]:
        """
        从文本内容中提取时间戳。

        Args:
            content: 待提取时间的文本。

        Returns:
            {
                "timestamp": str,  # ISO 8601 格式时间戳
            }
        """

    @abstractmethod
    def layer2_5_graph(
        self,
        entities: list[str],
        max_hops: int = 3,
    ) -> dict[str, Any]:
        """
        知识图谱关系查询（子图检索）。

        Args:
            entities: 实体 ID 列表。
            max_hops: 最大跳数（关系深度）。

        Returns:
            {
                "paths": list[dict],        # 实体间关系路径
                "root_cause": str | None,   # 根因分析结论
                "confidence": float,        # 置信度 [0, 1]
            }
        """

    @abstractmethod
    def layer2_5_extract_entities(self, content: str) -> dict[str, Any]:
        """
        从文本中提取实体。

        Args:
            content: 待提取实体的文本。

        Returns:
            {
                "entity_ids": list[str],  # 提取到的实体 ID 列表
            }
        """

    @abstractmethod
    def layer2_7_predict(
        self,
        event_series: list[dict[str, Any]],
        horizon: str = "24h",
    ) -> dict[str, Any]:
        """
        基于事件序列预测未来趋势。

        Args:
            event_series: 历史事件序列（每条含 timestamp 和 payload）。
            horizon: 预测时间范围。

        Returns:
            {
                "predictions": list[dict],  # 预测结果列表
                "confidence": float,        # 置信度 [0, 1]
                "risk_level": str,          # 风险等级: low | medium | high | critical
            }
        """

    # ── Layer 3: 归档 & 读取 ─────────────────────────────────────────────

    @abstractmethod
    def layer3_archive(self, content: str) -> dict[str, Any]:
        """
        将内容归档为长期记忆。

        Args:
            content: 待归档的内容。

        Returns:
            {
                "memory_id": str,  # 归档后的记忆 ID
            }
        """

    @abstractmethod
    def layer3_read(self, memory_id: str) -> dict[str, Any]:
        """
        读取已归档的记忆内容。

        Args:
            memory_id: 记忆 ID。

        Returns:
            {
                "content": str,  # 记忆内容
            }
        """
