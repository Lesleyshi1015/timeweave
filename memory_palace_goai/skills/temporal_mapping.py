# @agent: session-260808-golden-quasar | module: apps/memory_palace/skills/temporal_mapping | ts: 2026-08-08T17:00+08:00
"""
Temporal Mapping Skill（时间映射）

用途：
- Layer 2 时间线构建（layer2_timeline）：从一组记忆中提取按时间排序的事件
- Layer 2 时间戳提取（layer2_extract_time）：从文本内容中提取结构化时间戳

开源部分：Schema 定义 + Wrapper 调用逻辑（本文件）
闭源部分：时间解析算法、时区归一化、事件排序逻辑（引擎内部）
"""

from typing import Any, Dict

from agent_teams_sdk.skills.base_skill import BaseSkill


class TemporalMapping(BaseSkill):
    """
    时间映射 Skill — 支持时间线构建和时间戳提取两种模式。

    Attributes
    ----------
    name : str
        Skill 标识符："temporal-mapping"
    version : str
        版本号："1.0.0"
    schema : dict
        输入/输出 JSON Schema
    """

    name = "temporal-mapping"
    version = "1.0.0"
    schema = {
        "input": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["timeline", "extract_time"],
                    "description": "操作模式：timeline=构建时间线，extract_time=提取时间戳",
                },
                "memory_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "记忆 ID 列表（mode=timeline 时必填）",
                },
                "time_range": {
                    "type": "string",
                    "description": "时间范围，如 24h、7d、30d（mode=timeline 时使用）",
                },
                "content": {
                    "type": "string",
                    "description": "待提取时间的文本（mode=extract_time 时必填）",
                },
            },
            "required": ["mode"],
        },
        "output": {
            "type": "object",
            "properties": {
                "mode": {"type": "string"},
                "timeline_events": {
                    "type": "array",
                    "items": {"type": "object"},
                },
                "timestamp": {"type": "string"},
                "confidence": {"type": "number"},
            },
            "required": ["mode"],
        },
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行时间映射操作。

        Parameters
        ----------
        mode : str
            "timeline" 或 "extract_time"
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

        if mode == "timeline":
            memory_ids = kwargs.get("memory_ids", [])
            result = mp.layer2_timeline(
                memory_ids=memory_ids,
                time_range=kwargs.get("time_range", "24h"),
            )
            return {"mode": "timeline", **result}
        else:  # mode == "extract_time"
            content = kwargs.get("content", "")
            result = mp.layer2_extract_time(content=content)
            return {"mode": "extract_time", **result}
