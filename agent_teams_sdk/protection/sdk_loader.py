# @agent: session-260808-fleet-spruce | module: agent-teams-sdk-skeleton | ts: 2026-08-08T16:35+08:00
# 接口定义来源：跨项目接口开发需求-MemoryPalace-SelfBrain.md §5.2
import ctypes
from pathlib import Path
from typing import Any


class SDKLoader:
    """SDK 加载器（用于加载闭源 .so/.dll）"""

    def __init__(self, sdk_path: str):
        self.sdk_path = Path(sdk_path)
        self._lib = None
        self._load()

    def _load(self) -> None:
        if not self.sdk_path.exists():
            raise FileNotFoundError(f"SDK not found: {self.sdk_path}")
        if self.sdk_path.suffix == ".so":
            self._lib = ctypes.CDLL(str(self.sdk_path))
        elif self.sdk_path.suffix == ".dll":
            self._lib = ctypes.WinDLL(str(self.sdk_path))
        else:
            raise ValueError(f"不支持的 SDK 后缀: {self.sdk_path.suffix}")

    def call(self, func_name: str, *args) -> Any:
        func = getattr(self._lib, func_name)
        return func(*args)

    def is_loaded(self) -> bool:
        return self._lib is not None
