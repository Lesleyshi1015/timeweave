# 测试用示例 Skill B
# @agent: session-260808-clever-orchid | module: skills/plugin_manager | ts: 2026-08-08T16:37+08:00
from agent_teams_sdk.skills.base_skill import BaseSkill
from typing import Any, Dict


class SkillB(BaseSkill):
    """测试用 Skill B"""

    name = "fixture-skill-b"
    version = "2.0.0"
    schema = {
        "input": {"required": []},
        "output": {"type": "object"},
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        return {"result": "from-b"}
