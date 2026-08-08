# @agent: session-260808-golden-quasar | module: apps/memory_palace/skills/entity_graph | ts: 2026-08-08T17:00+08:00
"""
Entity Graph Skill（实体图谱）

用途：
- Layer 2.5 图谱查询（layer2_5_graph）：查询实体间的关系路径，支持根因分析
- Layer 2.5 实体提取（layer2_5_extract_entities）：从文本中自动提取结构化实体

开源部分：Schema 定义 + Wrapper 调用逻辑（本文件）
闭源部分：图谱遍历算法、关系推理、实体识别模型（引擎内部）
"""

from typing import Any, Dict

from agent_teams_sdk.skills.base_skill import BaseSkill


class EntityGraph(BaseSkill):
    """
    实体图谱 Skill — 支持图谱查询和实体提取两种模式。

    Attributes
    ----------
    name : str
        Skill 标识符："entity-graph"
    version : str
        版本号："1.0.0"
    schema : dict
        输入/输出 JSON Schema
    """

    name = "entity-graph"
    version = "1.0.0"
    schema = {
        "input": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["graph", "extract_entities"],
                    "description": "操作模式：graph=图谱查询，extract_entities=实体提取",
                },
                "entities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "实体 ID 列表（mode=graph 时必填）",
                },
                "max_hops": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 6,
                    "description": "最大跳数/关系深度（mode=graph 时使用）",
                },
                "content": {
                    "type": "string",
                    "description": "待提取实体的文本（mode=extract_entities 时必填）",
                },
            },
            "required": ["mode"],
        },
        "output": {
            "type": "object",
            "properties": {
                "mode": {"type": "string"},
                "paths": {
                    "type": "array",
                    "items": {"type": "object"},
                },
                "root_cause": {"type": ["string", "null"]},
                "entity_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "confidence": {"type": "number"},
            },
            "required": ["mode"],
        },
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行实体图谱操作。

        Parameters
        ----------
        mode : str
            "graph" 或 "extract_entities"
        **kwargs
            根据模式传递不同参数

        Returns
        -------
        dict
            引擎返回的结果字典
        """
        self.validate_input(**kwargs)

        from memory_palace_goai.mp_api import get_service

        mp = get_service("stub")
        mode = kwargs["mode"]

        if mode == "graph":
            entities = kwargs.get("entities", [])
            result = mp.layer2_5_graph(
                entities=entities,
                max_hops=kwargs.get("max_hops", 3),
            )
            return {"mode": "graph", **result}
        else:  # mode == "extract_entities"
            content = kwargs.get("content", "")
            result = mp.layer2_5_extract_entities(content=content)
            return {"mode": "extract_entities", **result}
