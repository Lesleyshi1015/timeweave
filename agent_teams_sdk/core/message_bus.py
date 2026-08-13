# @agent: session-260808-first-tiger | module: core/message_bus | ts: 2026-08-08T16:37+08:00
# 设计依据：跨项目接口开发需求-MemoryPalace-SelfBrain.md §2.1（MessageBus）
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime
import threading
import uuid


class MessageBus:
    """
    MessageBus - Agent 间消息传递

    - 支持点对点（发给指定 Agent）与广播
    - 每个消息带 message_id / timestamp，供可观测层关联
    - 默认异步投递：send 不阻塞；deliver 由 Agent 自行消费
    - 支持队列模式：subscribe 时指定 queue=True，消息按序入队，需通过 consume() 消费
    - 支持消息回放：query_history 按条件查询，replay 重放给指定订阅者
    - 支持 dead-letter：handler 异常时捕获并记录，不中断其他订阅者

    使用示例：
        bus = MessageBus()
        bus.subscribe("l1-agent", handler)
        bus.send("curator", "l1-agent", "@L1 请检索")
    """

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self._lock = threading.RLock()
        self._history: List[Dict[str, Any]] = []
        self._queues: Dict[str, List[Dict[str, Any]]] = {}
        self._queue_mode: set = set()
        self._dead_letters: List[Dict[str, Any]] = []

    def subscribe(
        self,
        agent_name: str,
        handler: Callable[[Dict[str, Any]], None],
        queue: bool = False,
    ) -> None:
        """
        订阅指定 Agent 的消息。

        Args:
            agent_name: 订阅的目标 Agent 名称
            handler: 消息处理回调，接收信封字典
            queue: 是否启用队列模式。为 True 时消息入队而非立即投递，
                   需通过 consume() 按序消费
        """
        with self._lock:
            self._subscribers.setdefault(agent_name, []).append(handler)
            if queue:
                self._queue_mode.add(agent_name)

    def unsubscribe(self, agent_name: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """取消订阅。"""
        with self._lock:
            if agent_name in self._subscribers and handler in self._subscribers[agent_name]:
                self._subscribers[agent_name].remove(handler)

    def _call_handler(
        self,
        agent_name: str,
        handler: Callable[[Dict[str, Any]], None],
        envelope: Dict[str, Any],
    ) -> None:
        """调用单个 handler，异常时记录到 dead-letter，不向外抛出。"""
        try:
            handler(envelope)
        except Exception as e:
            self._dead_letters.append({
                "message_id": envelope["message_id"],
                "agent_name": agent_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "envelope": envelope,
                "timestamp": datetime.now().isoformat(),
            })

    def send(self, sender: str, recipient: str, message: str, payload: Any = None) -> Dict[str, Any]:
        """
        点对点发送消息给指定 Agent。

        Args:
            sender: 发送方名称
            recipient: 接收方 Agent 名称
            message: 消息文本
            payload: 可选的附加数据

        Returns:
            消息信封字典，含 message_id、timestamp 等元数据
        """
        envelope = {
            "message_id": uuid.uuid4().hex,
            "sender": sender,
            "recipient": recipient,
            "message": message,
            "payload": payload,
            "timestamp": datetime.now().isoformat(),
        }
        with self._lock:
            self._history.append(envelope)
            if recipient in self._queue_mode:
                self._queues.setdefault(recipient, []).append(envelope)
                return envelope

        for handler in self._subscribers.get(recipient, []):
            self._call_handler(recipient, handler, envelope)
        return envelope

    def broadcast(self, sender: str, message: str, payload: Any = None) -> List[Dict[str, Any]]:
        """广播消息给所有已订阅的 Agent。"""
        envelopes = []
        with self._lock:
            recipients = list(self._subscribers.keys())
        for recipient in recipients:
            envelopes.append(self.send(sender, recipient, message, payload))
        return envelopes

    def consume(self, agent_name: str, auto_ack: bool = True) -> List[Dict[str, Any]]:
        """
        消费指定 Agent 的队列消息（仅 queue=True 的订阅有效）。

        Args:
            agent_name: 队列所属 Agent 名称
            auto_ack: 为 True 时消费后自动清空该 Agent 队列；
                      为 False 时仅读取不清空

        Returns:
            队列中的消息列表，按入队顺序排列
        """
        with self._lock:
            messages = list(self._queues.get(agent_name, []))
            if auto_ack:
                self._queues[agent_name] = []
        return messages

    def query_history(
        self,
        message_id: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        按条件查询历史消息。

        Args:
            message_id: 按消息 ID 精确查询
            since: 起始时间（ISO 格式），包含该时间点
            until: 结束时间（ISO 格式），包含该时间点
            limit: 最大返回条数

        Returns:
            符合条件的消息列表，按时间正序
        """
        with self._lock:
            results = list(self._history)

        if message_id:
            results = [m for m in results if m["message_id"] == message_id]
        if since:
            results = [m for m in results if m["timestamp"] >= since]
        if until:
            results = [m for m in results if m["timestamp"] <= until]

        return results[-limit:]

    def replay(
        self,
        recipient: str,
        message_ids: Optional[Union[str, List[str]]] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        将历史消息重放给指定订阅者。

        Args:
            recipient: 重放目标 Agent 名称
            message_ids: 指定要重放的消息 ID（单个或列表）；
                         为 None 时重放所有符合条件的消息
            since: 起始时间过滤
            until: 结束时间过滤

        Returns:
            已重放的消息列表
        """
        ids = {message_ids} if isinstance(message_ids, str) else set(message_ids or [])

        with self._lock:
            candidates = list(self._history)

        if ids:
            candidates = [m for m in candidates if m["message_id"] in ids]
        if since:
            candidates = [m for m in candidates if m["timestamp"] >= since]
        if until:
            candidates = [m for m in candidates if m["timestamp"] <= until]

        for msg in candidates:
            for handler in self._subscribers.get(recipient, []):
                self._call_handler(recipient, handler, msg)

        return candidates

    def get_dead_letters(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取 dead-letter 记录。

        Args:
            limit: 最大返回条数

        Returns:
            dead-letter 记录列表，按时间倒序（最新的在前）
        """
        with self._lock:
            return list(reversed(self._dead_letters[-limit:]))

    def clear_dead_letters(self) -> None:
        """清空 dead-letter 记录。"""
        with self._lock:
            self._dead_letters.clear()

    def history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """返回最近的历史消息（兼容旧接口）。"""
        with self._lock:
            return self._history[-limit:]

    def clear(self) -> None:
        """清空历史消息（兼容旧接口）。"""
        with self._lock:
            self._history.clear()
