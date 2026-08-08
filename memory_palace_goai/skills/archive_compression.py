# @agent: session-260808-golden-quasar | module: apps/memory_palace/skills/archive_compression | ts: 2026-08-08T17:10+08:00
"""
Archive Compression Skill（归档压缩）

用途：
- Layer 3 归档写入（layer3_archive）：将内容压缩归档为长期记忆
- Layer 3 归档读取（layer3_read）：读取已归档的记忆内容

开源部分：Schema 定义 + Wrapper 调用逻辑（本文件）
闭源部分：压缩算法、去重策略、存储优化（引擎内部）
"""

from typing import Any, Dict

from agent_teams_sdk.skills.base_skill import BaseSkill


class ArchiveCompression(BaseSkill):
    """
    归档压缩 Skill — 支持归档写入和读取两种模式。

    Attributes
    ----------
    name : str
        Skill 标识符："archive-compression"
    version : str
        版本号："1.0.0"
    schema : dict
        输入/输出 JSON Schema
    """

    name = "archive-compression"
    version = "1.0.0"
    schema = {
        "input": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["archive", "read"],
                    "description": "操作模式：archive=写入归档，read=读取归档",
                },
                "content": {
                    "type": "string",
                    "description": "待归档的内容（mode=archive 时必填）",
                },
                "memory_id": {
                    "type": "string",
                    "description": "归档记忆 ID（mode=read 时必填）",
                },
            },
            "required": ["mode"],
        },
        "output": {
            "type": "object",
            "properties": {
                "mode": {"type": "string"},
                "memory_id": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["mode"],
        },
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行归档压缩操作。

        Parameters
        ----------
        mode : str
            "archive" 或 "read"
        **kwargs
            根据模式传递不同参数

        Returns
        -------
        dict
            引擎返回的结果字典
        """
        self.validate_input(**kwargs)

        mode = kwargs["mode"]

        # 模式特定的必填字段校验
        if mode == "archive" and "content" not in kwargs:
            raise ValueError("mode='archive' 时 content 为必填字段")
        if mode == "read" and "memory_id" not in kwargs:
            raise ValueError("mode='read' 时 memory_id 为必填字段")

        from memory_palace_goai.mp_api import get_service

        mp = get_service("stub")

        if mode == "archive":
            result = mp.layer3_archive(content=kwargs["content"])
            return {"mode": "archive", **result}
        else:  # mode == "read"
            result = mp.layer3_read(memory_id=kwargs["memory_id"])
            return {"mode": "read", **result}
