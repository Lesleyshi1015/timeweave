# @agent: session-260808-golden-quasar | module: apps/memory_palace/skills/hybrid_search | ts: 2026-08-08T17:00+08:00
"""
Hybrid Search Skill（混合检索）

用途：
- Layer 1 语义检索（layer1_search）：根据查询字符串从记忆库中检索相关记忆
- Layer 1 索引写入（layer1_index）：将新的记忆条目写入索引

开源部分：Schema 定义 + Wrapper 调用逻辑（本文件）
闭源部分：核心检索算法、向量相似度计算、索引策略（引擎内部）
"""

from typing import Any, Dict

from agent_teams_sdk.skills.base_skill import BaseSkill


class HybridSearch(BaseSkill):
    """
    混合检索 Skill — 支持语义搜索和索引写入两种模式。

    Attributes
    ----------
    name : str
        Skill 标识符："hybrid-search"
    version : str
        版本号："1.0.0"
    schema : dict
        输入/输出 JSON Schema
    """

    name = "hybrid-search"
    version = "1.0.0"
    schema = {
        "input": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["search", "index"],
                    "description": "操作模式：search=检索，index=写入索引",
                },
                "query": {
                    "type": "string",
                    "description": "检索查询字符串（mode=search 时必填）",
                },
                "top_k": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "description": "返回结果数量上限（mode=search 时使用）",
                },
                "context": {
                    "type": "object",
                    "description": "可选的上下文信息（如用户身份、当前会话状态）",
                },
                "memory_id": {
                    "type": "string",
                    "description": "记忆唯一标识（mode=index 时必填）",
                },
                "timestamp": {
                    "type": "string",
                    "description": "ISO 8601 时间戳（mode=index 时必填）",
                },
                "content": {
                    "type": "string",
                    "description": "记忆内容（mode=index 时可选）",
                },
            },
            "required": ["mode"],
        },
        "output": {
            "type": "object",
            "properties": {
                "mode": {"type": "string"},
                "summary": {"type": "string"},
                "results": {
                    "type": "array",
                    "items": {"type": "object"},
                },
                "confidence": {"type": "number"},
                "status": {"type": "string"},
                "memory_id": {"type": "string"},
            },
            "required": ["mode"],
        },
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行混合检索操作。

        Parameters
        ----------
        mode : str
            "search" 或 "index"
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
        if mode == "search" and "query" not in kwargs:
            raise ValueError("mode='search' 时 query 为必填字段")
        if mode == "index":
            if "memory_id" not in kwargs:
                raise ValueError("mode='index' 时 memory_id 为必填字段")
            if "timestamp" not in kwargs:
                raise ValueError("mode='index' 时 timestamp 为必填字段")

        from memory_palace_goai.mp_api import get_service

        mp = get_service("stub")

        if mode == "search":
            result = mp.layer1_search(
                query=kwargs["query"],
                top_k=kwargs.get("top_k", 10),
                context=kwargs.get("context"),
            )
            return {"mode": "search", **result}
        else:  # mode == "index"
            result = mp.layer1_index(
                memory_id=kwargs["memory_id"],
                timestamp=kwargs["timestamp"],
                content=kwargs.get("content"),
            )
            return {"mode": "index", **result}
