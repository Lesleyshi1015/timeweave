# @agent: session-260808-fleet-spruce | module: agent-teams-sdk-skeleton | ts: 2026-08-08T16:35+08:00
# 接口定义来源：跨项目接口开发需求-MemoryPalace-SelfBrain.md §3.3
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseSkill(ABC):
    """
    Skill 基础类

    所有 Skill 必须继承此类
    """

    name: str = ""
    version: str = "1.0.0"
    schema: Dict = {}

    def __init__(self):
        if not self.name:
            self.name = self.__class__.__name__.lower()

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行 Skill"""
        pass

    def validate_input(self, **kwargs) -> bool:
        """验证输入"""
        required = self.schema.get("input", {}).get("required", [])
        for field in required:
            if field not in kwargs:
                raise ValueError(f"Missing required field: {field}")
        return True

    def get_schema(self) -> Dict:
        """获取 Schema"""
        return {"name": self.name, "version": self.version, **self.schema}
