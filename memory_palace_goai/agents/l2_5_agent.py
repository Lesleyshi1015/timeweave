# @agent: session-260808-vital-prairie | module: apps/memory_palace/agents/l2_5_agent | ts: 2026-08-08T17:00+08:00
"""
L2.5 Agent — 实体图谱层（Entity Graph）

职责：
- 读取 L1 检索结果或存储内容
- 调用 EntityGraph Skill 提取实体并构建关系图谱
- 将图谱结果写入黑板 l2-5-agent_result
"""

from typing import Any, Dict, List

from agent_teams_sdk.roles.worker import WorkerAgent
from memory_palace_goai.skills.entity_graph import EntityGraph


class L2_5Agent(WorkerAgent):
    """
    Layer 2.5 Worker — 实体图谱 Agent。

    查询模式：从 L1 结果中提取实体，查询图谱关系路径
    存储模式：从 store_content 中提取实体
    """

    def __init__(self, team_room):
        super().__init__("l2-5-agent", team_room)

    def do_work(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行实体图谱工作。

        查询模式：读取 L1 结果 → 提取实体 → EntityGraph.graph()
        存储模式：读取 store_content → EntityGraph.extract_entities()
        """
        skill = EntityGraph()
        query_mode = self.team_room.read("user_query") is not None
        content = self.team_room.read("store_content")

        if query_mode:
            # 查询模式：从 L1 结果构建图谱
            return self._build_graph(skill)
        elif content:
            # 存储模式：提取实体
            return self._extract_entities(skill, content)
        else:
            self._log("L2.5: 无查询内容")
            return {"mode": "graph", "paths": [], "root_cause": None}

    def _build_graph(self, skill: EntityGraph) -> Dict[str, Any]:
        """从 L1 结果构建实体图谱。"""
        l1_result = self.team_room.read("l1-agent_result")
        if not l1_result:
            self._log("L2.5: L1 结果不存在")
            return {"mode": "graph", "paths": [], "root_cause": None, "confidence": 0.0}

        # 从 L1 结果中提取实体 ID（从 content 中提取）
        entities: List[str] = []
        for r in l1_result.get("results", []):
            if isinstance(r, dict):
                content = r.get("content", "")
                # 提取大写标识符作为实体
                import re
                found = re.findall(r"\b[A-Z][A-Z0-9_-]{2,}\b", content)
                entities.extend(found)

        # 去重
        entities = list(dict.fromkeys(entities))

        if not entities:
            # 使用演示实体
            entities = ["API_GATEWAY", "DB_PRIMARY"]

        result = skill.execute(mode="graph", entities=entities[:10], max_hops=3)
        root_cause = result.get("root_cause")
        paths = result.get("paths", [])
        self._log(f"L2.5 图谱构建完成: {len(paths)} 条路径, 根因={root_cause}")
        return result

    def _extract_entities(self, skill: EntityGraph, content: str) -> Dict[str, Any]:
        """从存储内容中提取实体。"""
        result = skill.execute(mode="extract_entities", content=content)
        entity_ids = result.get("entity_ids", [])
        self._log(f"L2.5 实体提取完成: {len(entity_ids)} 个实体")
        return result

    def _log(self, message: str) -> None:
        """内部日志。"""
        print(f"[{self.name}] {message}")
