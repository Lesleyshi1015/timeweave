# @agent: session-260808-fleet-spruce | module: memory_backend(TimeWeaveBackend) | ts: 2026-08-13T20:42+08:00
"""TimeWeave 记忆引擎热插拔接口（MemoryBackend 对接端）。

契约（由 SelfBrain 侧 noble-cove 定义，合并底座热插拔演示用）：
    class MemoryBackend(ABC):
        def search(self, query: str, top_k: int = 5) -> dict:
            \"\"\"返回 {"query": str, "results": list[dict], "memory_paths": list[str]} \"\"\"

本模块实现 TimeWeave 侧对接：把 TimeWeave 的检索能力
（L1 混合检索 + L2 时间线上下文）包装成上述接口，
供 SelfBrain demo 注入演示"记忆引擎可替换"。

独立可测：默认使用 StubEngine（无需闭源核心），
与 memory-palace-goai 的 stub 策略一致。
"""

from typing import List, Optional

from memory_palace_goai.mp_api import get_service


class TimeWeaveBackend:
    """TimeWeave 记忆引擎的 MemoryBackend 实现（duck-typing 兼容契约）。"""

    def __init__(self, engine=None, service_mode: str = "stub"):
        """初始化后端。

        Args:
            engine: 可选，传入已构造的 MPService 实例（默认 StubEngine）
            service_mode: "stub" 或 "engine"（未传 engine 时按此构造）
        """
        self.engine = engine if engine is not None else get_service(service_mode)

    def search(self, query: str, top_k: int = 5) -> dict:
        """检索记忆，返回热插拔契约格式。

        Returns:
            {"query": str, "results": list[dict], "memory_paths": list[str]}
            results: 每项含 id/title/summary/score/confidence
            memory_paths: 记忆路径标识（TimeWeave 层语义路径）
        """
        result = self.engine.layer1_search(query=query, top_k=top_k)

        results = []
        memory_paths = []
        for idx, item in enumerate(result.get("results", [])[:top_k]):
            if isinstance(item, dict):
                rid = str(item.get("id", item.get("memory_id", f"mem-{idx}")))
                title = item.get("title", item.get("summary", ""))[:80]
                score = item.get("score", item.get("confidence", 0.0))
            else:
                rid = f"mem-{idx}"
                title = str(item)[:80]
                score = 0.0
            results.append({
                "id": rid,
                "title": title,
                "summary": title,
                "score": float(score),
                "confidence": float(score),
            })
            # 记忆路径（L2 时间线语义路径：按时间锚点组织）
            memory_paths.append(f"L1/{rid}")

        return {
            "query": query,
            "results": results,
            "memory_paths": memory_paths,
        }

    # 兼容 ABC 抽象接口（供类型检查/鸭子类型使用）
    def __repr__(self) -> str:
        return f"<TimeWeaveBackend mode={self.engine.__class__.__name__}>"
