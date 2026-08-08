"""
Engine — Memory Palace 真实引擎接入层。

通过配置读取主项目路径，动态导入检索核心。
当前为骨架实现：方法体返回 stub 降级结果并打印 warning。
TODO: 接入 F:/memory-palace-v3.0/src 的真实引擎方法。
"""

import os
import sys
import warnings
from pathlib import Path

from .api import MPService
from .stub import StubEngine


class Engine(MPService):
    """
    Memory Palace 真实引擎代理。

    从环境变量 MP_ENGINE_PATH 或配置文件读取主项目路径，
    动态导入检索核心并代理调用。

    当前状态：骨架实现，所有方法降级为 StubEngine 并打印 warning。
    """

    def __init__(self, engine_path: str | None = None) -> None:
        """
        初始化引擎代理。

        Args:
            engine_path: 主项目路径。优先使用传入值，其次 MP_ENGINE_PATH 环境变量，
                         最后回退到默认路径 F:/memory-palace-v3.0/src。
        """
        self._engine_path = engine_path or os.environ.get(
            "MP_ENGINE_PATH",
            "F:/memory-palace-v3.0/src",
        )
        self._stub = StubEngine()
        self._core = None
        self._try_load_core()

    def _try_load_core(self) -> None:
        """尝试动态加载主项目检索核心。"""
        core_path = Path(self._engine_path)
        if not core_path.exists():
            warnings.warn(
                f"[mp_api/engine] 引擎路径不存在: {self._engine_path}，降级为 StubEngine",
                RuntimeWarning,
                stacklevel=2,
            )
            return

        # TODO: 接入真实引擎
        # 示例接入代码（取消注释并调整路径后使用）：
        #
        # if str(core_path) not in sys.path:
        #     sys.path.insert(0, str(core_path))
        # try:
        #     from memory_palace.core import SearchEngine, TimelineEngine, GraphEngine
        #     self._core = {
        #         "search": SearchEngine(),
        #         "timeline": TimelineEngine(),
        #         "graph": GraphEngine(),
        #     }
        # except ImportError as e:
        #     warnings.warn(
        #         f"[mp_api/engine] 导入失败: {e}，降级为 StubEngine",
        #         RuntimeWarning,
        #         stacklevel=2,
        #     )
        warnings.warn(
            f"[mp_api/engine] 引擎路径存在但未加载核心模块（TODO: 接入 {self._engine_path}），"
            "当前降级为 StubEngine",
            RuntimeWarning,
            stacklevel=2,
        )

    def _delegate(self, method_name: str, *args, **kwargs) -> dict:
        """代理调用：如果核心已加载则调用核心，否则降级到 stub。"""
        if self._core is not None:
            # TODO: 核心加载后的真实调用
            # return self._core[...].method(*args, **kwargs)
            pass
        return getattr(self._stub, method_name)(*args, **kwargs)

    # ── Layer 1 ───────────────────────────────────────────────────────────

    def layer1_search(self, query: str, top_k: int = 10, context: dict | None = None) -> dict:
        """语义检索 — 代理到真实引擎或降级 stub。"""
        return self._delegate("layer1_search", query, top_k, context)

    def layer1_index(self, memory_id: str, timestamp: str, content: str | None = None) -> dict:
        """索引写入 — 代理到真实引擎或降级 stub。"""
        return self._delegate("layer1_index", memory_id, timestamp, content)

    # ── Layer 2 ───────────────────────────────────────────────────────────

    def layer2_timeline(self, memory_ids: list[str], time_range: str = "24h") -> dict:
        """时间线提取 — 代理到真实引擎或降级 stub。"""
        return self._delegate("layer2_timeline", memory_ids, time_range)

    def layer2_extract_time(self, content: str) -> dict:
        """时间戳提取 — 代理到真实引擎或降级 stub。"""
        return self._delegate("layer2_extract_time", content)

    def layer2_5_graph(self, entities: list[str], max_hops: int = 3) -> dict:
        """知识图谱查询 — 代理到真实引擎或降级 stub。"""
        return self._delegate("layer2_5_graph", entities, max_hops)

    def layer2_5_extract_entities(self, content: str) -> dict:
        """实体提取 — 代理到真实引擎或降级 stub。"""
        return self._delegate("layer2_5_extract_entities", content)

    def layer2_7_predict(self, event_series: list[dict], horizon: str = "24h") -> dict:
        """趋势预测 — 代理到真实引擎或降级 stub。"""
        return self._delegate("layer2_7_predict", event_series, horizon)

    # ── Layer 3 ───────────────────────────────────────────────────────────

    def layer3_archive(self, content: str) -> dict:
        """归档内容 — 代理到真实引擎或降级 stub。"""
        return self._delegate("layer3_archive", content)

    def layer3_read(self, memory_id: str) -> dict:
        """读取记忆 — 代理到真实引擎或降级 stub。"""
        return self._delegate("layer3_read", memory_id)
