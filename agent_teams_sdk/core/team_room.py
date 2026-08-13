# @agent: session-260808-fleet-spruce | module: agent-teams-sdk-skeleton | ts: 2026-08-08T16:35+08:00
# 接口定义来源：跨项目接口开发需求-MemoryPalace-SelfBrain.md §3.1
from typing import Any, Dict
from dataclasses import dataclass, field
from datetime import datetime
import threading


@dataclass
class BlackboardEntry:
    key: str
    value: Any
    updated_by: str
    updated_at: datetime
    version: int = 0
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "key": self.key,
                "value": self.value,
                "updated_by": self.updated_by,
                "updated_at": self.updated_at.isoformat(),
                "version": self.version,
            }


class TeamRoom:
    """
    Team Room - 共享黑板

    所有 Agent 通过黑板交换信息

    使用示例：
        room = TeamRoom("task-001")
        room.write("query", "分析销售趋势", updated_by="curator")
        query = room.read("query")
    """

    def __init__(self, task_id: str):
        self.task_id = task_id
        self._data: Dict[str, BlackboardEntry] = {}
        self._lock = threading.RLock()

    def read(self, key: str) -> Any:
        with self._lock:
            entry = self._data.get(key)
            return entry.value if entry else None

    def read_entry(self, key: str) -> BlackboardEntry | None:
        with self._lock:
            return self._data.get(key)

    def write(self, key: str, value: Any, updated_by: str = "system") -> None:
        with self._lock:
            old_version = self._data[key].version if key in self._data else 0
            self._data[key] = BlackboardEntry(
                key=key, value=value, updated_by=updated_by,
                updated_at=datetime.now(), version=old_version + 1
            )

    def read_all(self) -> Dict[str, Any]:
        with self._lock:
            return {key: entry.value for key, entry in self._data.items()}

    def read_all_with_meta(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {key: entry.snapshot() for key, entry in self._data.items()}

    def keys(self) -> list[str]:
        with self._lock:
            return list(self._data.keys())

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._data

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
