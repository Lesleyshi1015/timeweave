# 测试用示例 Skill A
# @agent: session-260808-clever-orchid | module: skills/plugin_manager | ts: 2026-08-08T16:37+08:00
from agent_teams_sdk.skills.base_skill import BaseSkill
from typing import Any, Dict


class SkillA(BaseSkill):
    """测试用 Skill A"""

    name = "fixture-skill-a"
    version = "1.0.0"
    schema = {
        "input": {"required": ["query"]},
        "output": {"type": "object"},
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        return {"result": f"a:{kwargs.get('query')}"}
