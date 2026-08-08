"""
StubEngine — Memory Palace 桩实现。

使用内存 dict 模拟记忆存储，返回合理演示数据。
适用于：端到端流程验证、演示、无引擎环境下的开发测试。
"""

import uuid
from datetime import datetime, timezone

from .api import MPService


class StubEngine(MPService):
    """
    Memory Palace 桩引擎。

    用内存 dict 模拟记忆存储，所有方法返回演示数据。
    演示场景：运维告警根因分析（API 5xx、数据库索引失效等）。
    """

    def __init__(self) -> None:
        """初始化桩引擎，创建内存存储和演示数据。"""
        self._memories: dict[str, dict[str, str]] = {}
        self._seed_demo_data()

    def _seed_demo_data(self) -> None:
        """预置演示数据（运维告警场景）。"""
        now = datetime.now(timezone.utc).isoformat()
        demo_memories = [
            {
                "memory_id": "mem-api-5xx-001",
                "timestamp": now,
                "content": (
                    "2026-08-08 10:23:45 UTC — API Gateway 返回 5xx 错误率突增至 12.3%。"
                    "影响服务：user-service, order-service。疑似 upstream timeout。"
                ),
            },
            {
                "memory_id": "mem-db-slow-002",
                "timestamp": now,
                "content": (
                    "2026-08-08 09:45:12 UTC — 数据库 orders_db 查询延迟 P99 达 2.3s，"
                    "索引 idx_orders_created_at 失效，全表扫描触发告警。"
                ),
            },
            {
                "memory_id": "mem-cache-003",
                "timestamp": now,
                "content": (
                    "2026-08-08 08:10:00 UTC — Redis 缓存命中率下降至 67%，"
                    "热点 Key user:profile:* 过期导致缓存穿透。"
                ),
            },
        ]
        for mem in demo_memories:
            self._memories[mem["memory_id"]] = {
                "timestamp": mem["timestamp"],
                "content": mem["content"],
            }

    # ── Layer 1 ───────────────────────────────────────────────────────────

    def layer1_search(
        self,
        query: str,
        top_k: int = 10,
        context: dict | None = None,
    ) -> dict:
        """语义检索 — 返回演示匹配结果。"""
        all_results = [
            {
                "memory_id": mid,
                "content": data["content"],
                "timestamp": data["timestamp"],
                "score": 0.92 - i * 0.05,
            }
            for i, (mid, data) in enumerate(self._memories.items())
        ][:top_k]

        return {
            "summary": f"找到 {len(all_results)} 条相关记忆（82 tokens 摘要）",
            "results": all_results,
            "confidence": 0.91,
        }

    def layer1_index(
        self,
        memory_id: str,
        timestamp: str,
        content: str | None = None,
    ) -> dict:
        """索引写入 — 存入内存存储。"""
        self._memories[memory_id] = {
            "timestamp": timestamp,
            "content": content or "",
        }
        return {"status": "indexed", "memory_id": memory_id}

    # ── Layer 2 ───────────────────────────────────────────────────────────

    def layer2_timeline(
        self,
        memory_ids: list[str],
        time_range: str = "24h",
    ) -> dict:
        """时间线提取 — 按时间排序返回事件。"""
        events = []
        for mid in memory_ids:
            mem = self._memories.get(mid)
            if mem:
                events.append({
                    "memory_id": mid,
                    "timestamp": mem["timestamp"],
                    "summary": mem["content"][:80] + "...",
                })
        events.sort(key=lambda e: e["timestamp"])
        return {"timeline_events": events, "confidence": 0.88}

    def layer2_extract_time(self, content: str) -> dict:
        """时间戳提取 — 正则匹配 ISO 时间戳。"""
        import re
        iso_pattern = r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
        match = re.search(iso_pattern, content)
        if match:
            ts = match.group(0).replace(" ", "T")
            return {"timestamp": ts}
        return {"timestamp": datetime.now(timezone.utc).isoformat()}

    def layer2_5_graph(
        self,
        entities: list[str],
        max_hops: int = 3,
    ) -> dict:
        """知识图谱查询 — 返回演示路径和根因。"""
        paths = []
        for i, ent in enumerate(entities):
            paths.append({
                "source": ent,
                "target": f"service-{i + 1}",
                "relation": "affects",
                "hops": min(i + 1, max_hops),
            })
            if i > 0:
                paths.append({
                    "source": f"service-{i}",
                    "target": ent,
                    "relation": "depends_on",
                    "hops": 1,
                })

        root_cause = (
            "数据库索引失效导致级联超时，触发 API Gateway 5xx 告警"
            if len(entities) > 1 else None
        )
        return {
            "paths": paths,
            "root_cause": root_cause,
            "confidence": 0.85,
        }

    def layer2_5_extract_entities(self, content: str) -> dict:
        """实体提取 — 提取大写标识符和关键名词。"""
        import re
        # 简单启发式：提取大写单词、带连字符的标识符
        candidates = re.findall(r"\b[A-Z][A-Z0-9_-]{2,}\b", content)
        # 去重并保持顺序
        seen: set[str] = set()
        entity_ids = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                entity_ids.append(c)
        # 如果没有提取到，返回演示实体
        if not entity_ids:
            entity_ids = ["API_GATEWAY", "DB_PRIMARY"]
        return {"entity_ids": entity_ids}

    def layer2_7_predict(
        self,
        event_series: list[dict],
        horizon: str = "24h",
    ) -> dict:
        """趋势预测 — 基于事件序列返回固定预测。"""
        predictions = [
            {
                "timestamp": "2026-08-08T18:00:00Z",
                "metric": "error_rate",
                "predicted_value": 3.2,
                "unit": "%",
                "trend": "decreasing",
            },
            {
                "timestamp": "2026-08-08T20:00:00Z",
                "metric": "latency_p99",
                "predicted_value": 450,
                "unit": "ms",
                "trend": "stable",
            },
        ]
        return {
            "predictions": predictions,
            "confidence": 0.78,
            "risk_level": "medium",
        }

    # ── Layer 3 ───────────────────────────────────────────────────────────

    def layer3_archive(self, content: str) -> dict:
        """归档内容 — 生成 memory_id 并存储。"""
        memory_id = f"mem-{uuid.uuid4().hex[:8]}"
        self._memories[memory_id] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content": content,
        }
        return {"memory_id": memory_id}

    def layer3_read(self, memory_id: str) -> dict:
        """读取记忆 — 按 ID 返回内容。"""
        mem = self._memories.get(memory_id)
        if mem:
            return {"content": mem["content"]}
        return {"content": ""}
