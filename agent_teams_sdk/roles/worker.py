# @agent: session-260808-fleet-spruce | module: agent-teams-sdk-skeleton | ts: 2026-08-08T16:35+08:00
# 接口定义来源：跨项目接口开发需求-MemoryPalace-SelfBrain.md §4.2
from abc import abstractmethod
from typing import Any, Dict
from agent_teams_sdk.core.base_agent import BaseAgent
from agent_teams_sdk.core.team_room import TeamRoom


class WorkerAgent(BaseAgent):
    """
    Worker 模式

    负责执行具体任务、读写黑板
    """

    def __init__(self, name: str, team_room: TeamRoom):
        super().__init__(name, "worker", team_room)

    def on_message(self, message: str) -> None:
        if message.startswith(f"@{self.name}"):
            self.execute({"action": "work"})

    def execute(self, task: Dict[str, Any]) -> Any:
        result = self.do_work(task)
        self.team_room.write(f"{self.name}_result", result, updated_by=self.name)
        return result

    @abstractmethod
    def do_work(self, task: Dict[str, Any]) -> Any:
        """执行具体工作"""
        pass
