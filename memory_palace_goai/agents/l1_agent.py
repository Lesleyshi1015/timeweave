# @agent: session-260808-vital-prairie | module: apps/memory_palace/agents/l1_agent | ts: 2026-08-08T17:00+08:00
"""
L1 Agent — 混合检索层（Hybrid Search）

职责：
- 读取用户查询或存储内容
- 调用 HybridSearch Skill 执行语义检索或索引写入
- 将检索结果写入黑板 l1-agent_result
"""

from typing import Any, Dict

from agent_teams_sdk.roles.worker import WorkerAgent
from memory_palace_goai.skills.hybrid_search import HybridSearch


class L1Agent(WorkerAgent):
    """
    Layer 1 Worker — 混合检索 Agent。

    查询模式：根据 user_query 从记忆库检索相关记忆
    存储模式：将 store_content 写入索引
    """

    def __init__(self, team_room):
        super().__init__("l1-agent", team_room)

    def do_work(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行混合检索工作。

        查询模式：读取 user_query → HybridSearch.search()
        存储模式：读取 store_content → HybridSearch.index()
        """
        skill = HybridSearch()
        query = self.team_room.read("user_query")
        content = self.team_room.read("store_content")

        if query:
            # 查询模式：语义检索
            result = skill.execute(mode="search", query=query, top_k=10)
            self._log(f"L1 检索完成: {result.get('summary', '无摘要')}")
            return result
        elif content:
            # 存储模式：写入索引
            import uuid
            from datetime import datetime, timezone
            memory_id = f"mem-{uuid.uuid4().hex[:8]}"
            timestamp = datetime.now(timezone.utc).isoformat()
            result = skill.execute(
                mode="index",
                memory_id=memory_id,
                timestamp=timestamp,
                content=content,
            )
            self._log(f"L1 索引写入完成: {memory_id}")
            return result

        self._log("L1: 未找到 user_query 或 store_content")
        return {"mode": "search", "results": [], "confidence": 0.0}

    def _log(self, message: str) -> None:
        """内部日志（可替换为 AgentLogger）。"""
        print(f"[{self.name}] {message}")
