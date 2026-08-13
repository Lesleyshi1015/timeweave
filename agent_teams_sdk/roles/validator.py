# @agent: session-260808-fleet-spruce | module: agent-teams-sdk-skeleton | ts: 2026-08-08T16:35+08:00
# 接口定义来源：跨项目接口开发需求-MemoryPalace-SelfBrain.md §4.3
from abc import abstractmethod
from typing import Any, Dict, List
from dataclasses import dataclass
from agent_teams_sdk.core.base_agent import BaseAgent
from agent_teams_sdk.core.team_room import TeamRoom


@dataclass
class ValidationResult:
    passed: bool
    errors: List[str]
    warnings: List[str]


class ValidatorAgent(BaseAgent):
    """
    Validator 模式

    负责验证结果正确性
    """

    def __init__(self, name: str, team_room: TeamRoom):
        super().__init__(name, "validator", team_room)

    def on_message(self, message: str) -> None:
        if message.startswith(f"@{self.name}"):
            self.execute({"action": "validate"})

    def execute(self, task: Dict[str, Any]) -> ValidationResult:
        blackboard = self.team_room.read_all()
        result = self.validate(blackboard)
        self.team_room.write(f"{self.name}_result", {
            "passed": result.passed, "errors": result.errors
        }, updated_by=self.name)
        return result

    @abstractmethod
    def validate(self, blackboard: Dict[str, Any]) -> ValidationResult:
        """执行验证"""
        pass
