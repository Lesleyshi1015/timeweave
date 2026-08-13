# @agent: session-260808-fleet-spruce | module: agent-teams-sdk-skeleton | ts: 2026-08-08T16:35+08:00
# 接口定义来源：跨项目接口开发需求-MemoryPalace-SelfBrain.md §3.2
from abc import ABC, abstractmethod
from typing import Any, Dict
from enum import Enum


class AgentState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseAgent(ABC):
    """
    Agent 基础类

    所有 Agent 必须继承此类
    """

    def __init__(self, name: str, role: str, team_room: "TeamRoom"):
        self.name = name
        self.role = role
        self.team_room = team_room
        self.state = AgentState.IDLE

    @abstractmethod
    def on_message(self, message: str) -> None:
        """处理消息"""
        pass

    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> Any:
        """执行任务"""
        pass

    def get_state(self) -> Dict[str, Any]:
        return {"name": self.name, "role": self.role, "state": self.state.value}
