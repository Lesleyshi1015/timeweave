# @agent: session-260808-fleet-spruce | module: agent-teams-sdk-skeleton | ts: 2026-08-08T16:35+08:00
# 接口定义来源：跨项目接口开发需求-MemoryPalace-SelfBrain.md §4.1
from abc import abstractmethod
from typing import Any, Dict, List
from agent_teams_sdk.core.base_agent import BaseAgent, AgentState
from agent_teams_sdk.core.team_room import TeamRoom


class CuratorAgent(BaseAgent):
    """
    Curator/Leader 模式

    负责任务调度、完整度评估、结果整合
    """

    def __init__(self, name: str, team_room: TeamRoom, workers: List[str]):
        super().__init__(name, "curator", team_room)
        self.workers = workers

    def dispatch_task(self, worker: str, message: str) -> None:
        """分配任务给 Worker"""
        self.team_room.write(f"task_to_{worker}", message, updated_by=self.name)

    def collect_result(self, worker: str) -> Any:
        """收集 Worker 结果"""
        return self.team_room.read(f"{worker}_result")

    @abstractmethod
    def evaluate_completeness(self, blackboard: Dict) -> float:
        """评估完整度（0-1）"""
        pass

    def reconstruct_result(self, blackboard: Dict) -> Any:
        """重建最终结果"""
        results = {}
        for worker in self.workers:
            result = blackboard.get(f"{worker}_result")
            if result:
                results[worker] = result
        return results

    def on_message(self, message: str) -> None:
        """Curator 接收用户/外部消息，写入黑板。"""
        self.team_room.write("user_message", message, updated_by=self.name)

    def execute(self, task: Dict[str, Any]) -> Any:
        """默认执行：读取黑板上的用户消息，触发调度流程（子类可覆写）。"""
        self.state = AgentState.RUNNING
        blackboard = self.team_room.read_all()
        result = self.reconstruct_result(blackboard)
        self.state = AgentState.COMPLETED
        return result
