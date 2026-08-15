"""
TimeWeave API 桥接层。

提供 get_service() 工厂函数，根据 mode 返回 StubEngine 或 Engine 实例。

用法示例：
    from memory_palace_goai.mp_api import get_service

    # 使用桩引擎（演示/测试）
    service = get_service(mode="stub")
    result = service.layer1_search("API 5xx 告警")

    # 使用真实引擎（需配置 MP_ENGINE_PATH）
    service = get_service(mode="engine")
    result = service.layer1_search("API 5xx 告警")
"""

from .api import MPService
from .engine import Engine
from .stub import StubEngine

__all__ = ["MPService", "StubEngine", "Engine", "get_service"]


def get_service(mode: str = "stub") -> MPService:
    """
    TimeWeave 服务工厂。

    Args:
        mode: 引擎模式。
            - "stub": 返回 StubEngine（桩实现，演示数据）。
            - "engine": 返回 Engine（真实引擎代理，需配置路径）。

    Returns:
        MPService 实例。

    Raises:
        ValueError: 当 mode 不为 "stub" 或 "engine" 时抛出。
    """
    if mode == "stub":
        return StubEngine()
    if mode == "engine":
        return Engine()
    raise ValueError(
        f"未知的 mode='{mode}'，有效值为: 'stub', 'engine'"
    )
