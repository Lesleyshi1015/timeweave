# @agent: session-260808-vital-prairie | module: apps/memory_palace/agents/l2_agent | ts: 2026-08-08T17:00+08:00
"""
L2 Agent — 时间映射层（Temporal Mapping）

职责：
- 读取 L1 检索结果的 memory_ids
- 调用 TemporalMapping Skill 构建时间线
- 将时间线结果写入黑板 l2-agent_result
"""

from typing import Any, Dict

from agent_teams_sdk.roles.worker import WorkerAgent
from memory_palace_goai.skills.temporal_mapping import TemporalMapping


class L2Agent(WorkerAgent):
    """
    Layer 2 Worker — 时间映射 Agent。

    从 L1 检索结果中提取 memory_ids，构建按时间排序的事件时间线。
    """

    def __init__(self, team_room):
        super().__init__("l2-agent", team_room)

    def do_work(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行时间映射工作。

        读取 L1 结果 → 提取 memory_ids → TemporalMapping.timeline()
        """
        skill = TemporalMapping()
        l1_result = self.team_room.read("l1-agent_result")

        if not l1_result:
            self._log("L2: L1 结果不存在，跳过时间线构建")
            return {"mode": "timeline", "timeline_events": [], "confidence": 0.0}

        # 从 L1 结果中提取 memory_ids
        memory_ids = []
        results = l1_result.get("results", [])
        for r in results:
            if isinstance(r, dict) and r.get("memory_id"):
                memory_ids.append(r["memory_id"])

        if not memory_ids:
            self._log("L2: 未找到 memory_ids")
            return {"mode": "timeline", "timeline_events": [], "confidence": 0.0}

        result = skill.execute(mode="timeline", memory_ids=memory_ids, time_range="24h")
        events = result.get("timeline_events", [])
        self._log(f"L2 时间线构建完成: {len(events)} 个事件")
        return result

    def _log(self, message: str) -> None:
        """内部日志。"""
        print(f"[{self.name}] {message}")
