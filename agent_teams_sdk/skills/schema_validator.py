# @agent: session-260808-fleet-spruce | module: agent-teams-sdk-skeleton | ts: 2026-08-08T16:35+08:00
# 设计依据：跨项目接口开发需求-MemoryPalace-SelfBrain.md §2.1（SchemaValidator）
from typing import Any, Dict, List
import jsonschema


class SchemaValidator:
    """
    SchemaValidator - Skill 输入/输出 Schema 校验

    - 基于 JSON Schema（jsonschema 库）
    - validate_input / validate_output 两个入口，失败抛 ValueError
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Dict] = {}

    def register(self, skill_name: str, schema: Dict) -> None:
        """注册 Skill 的完整 Schema（input + output）。"""
        jsonschema.Draft202012Validator.check_schema(schema.get("input", {}))
        jsonschema.Draft202012Validator.check_schema(schema.get("output", {}))
        self._registry[skill_name] = schema

    def unregister(self, skill_name: str) -> None:
        self._registry.pop(skill_name, None)

    def registered(self) -> List[str]:
        return list(self._registry.keys())

    def validate_input(self, skill_name: str, **kwargs) -> bool:
        schema = self._registry.get(skill_name)
        if schema is None:
            raise ValueError(f"Skill '{skill_name}' 未注册 Schema")
        input_schema = schema.get("input", {})
        try:
            jsonschema.validate(instance=kwargs, schema=input_schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Skill '{skill_name}' 输入校验失败: {e.message}") from e
        return True

    def validate_output(self, skill_name: str, output: Any) -> bool:
        schema = self._registry.get(skill_name)
        if schema is None:
            raise ValueError(f"Skill '{skill_name}' 未注册 Schema")
        output_schema = schema.get("output", {})
        try:
            jsonschema.validate(instance=output, schema=output_schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Skill '{skill_name}' 输出校验失败: {e.message}") from e
        return True
