# @agent: session-260808-vital-prairie | module: apps/memory_palace/agents/l3_agent | ts: 2026-08-08T17:00+08:00
"""
L3 Agent — 归档压缩层（Archive Compression）

职责：
- 读取黑板上的存储内容
- 调用 ArchiveCompression Skill 归档内容
- 将归档后的 memory_id 写入黑板 l3-agent_result
"""

from typing import Any, Dict

from agent_teams_sdk.roles.worker import WorkerAgent
from memory_palace_goai.skills.archive_compression import ArchiveCompression


class L3Agent(WorkerAgent):
    """
    Layer 3 Worker — 归档压缩 Agent。

    将内容压缩归档为长期记忆，返回 memory_id。
    在存储流程中作为第一层执行。
    """

    def __init__(self, team_room):
        super().__init__("l3-agent", team_room)

    def do_work(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行归档压缩工作。

        读取 store_content → ArchiveCompression.archive()
        """
        skill = ArchiveCompression()
        content = self.team_room.read("store_content")

        if not content:
            # 如果是查询模式，归档查询结果
            all_results = self.team_room.read_all()
            content = str({
                k: v for k, v in all_results.items()
                if k.endswith("_result") and k != "l3-agent_result"
            })

        result = skill.execute(mode="archive", content=content)
        memory_id = result.get("memory_id", "unknown")
        size_before = result.get("size_before", len(content))
        self._log(f"L3 归档完成: {memory_id} ({size_before} bytes)")
        return result

    def _log(self, message: str) -> None:
        """内部日志。"""
        print(f"[{self.name}] {message}")
