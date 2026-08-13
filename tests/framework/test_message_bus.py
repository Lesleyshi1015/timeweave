# @agent: session-260808-first-tiger | module: core/message_bus | ts: 2026-08-08T16:37+08:00
"""MessageBus 增强功能单元测试

覆盖：队列模式、消息回放、dead-letter 隔离、现有 API 向后兼容
"""
from datetime import datetime
import pytest

from agent_teams_sdk.core.message_bus import MessageBus


# ─── 队列模式 ───
def test_queue_mode_messages_queued_not_delivered():
    """queue=True 时消息入队而非立即投递给 handler。"""
    bus = MessageBus()
    received = []
    bus.subscribe("worker", lambda e: received.append(e), queue=True)

    bus.send("curator", "worker", "task1")

    # handler 不应被调用
    assert received == []
    # 但消息在队列中
    queued = bus.consume("worker", auto_ack=False)
    assert len(queued) == 1
    assert queued[0]["message"] == "task1"


def test_queue_mode_consume_returns_in_order():
    """队列消息按入队顺序消费。"""
    bus = MessageBus()
    bus.subscribe("worker", lambda e: None, queue=True)

    bus.send("curator", "worker", "first")
    bus.send("curator", "worker", "second")
    bus.send("curator", "worker", "third")

    messages = bus.consume("worker")
    assert len(messages) == 3
    assert [m["message"] for m in messages] == ["first", "second", "third"]


def test_queue_mode_auto_ack_clears_queue():
    """auto_ack=True 消费后队列清空。"""
    bus = MessageBus()
    bus.subscribe("w", lambda e: None, queue=True)

    bus.send("s", "w", "m1")
    bus.send("s", "w", "m2")

    first = bus.consume("w", auto_ack=True)
    second = bus.consume("w", auto_ack=True)

    assert len(first) == 2
    assert second == []


def test_queue_mode_auto_ack_false_keeps_messages():
    """auto_ack=False 仅读取不清空。"""
    bus = MessageBus()
    bus.subscribe("w", lambda e: None, queue=True)

    bus.send("s", "w", "m1")

    first = bus.consume("w", auto_ack=False)
    second = bus.consume("w", auto_ack=False)

    assert len(first) == 1
    assert len(second) == 1


def test_queue_mode_non_queue_subscription_still_immediate():
    """queue=False（默认）的订阅仍立即投递。"""
    bus = MessageBus()
    received = []
    bus.subscribe("worker", lambda e: received.append(e))  # 默认 queue=False

    bus.send("curator", "worker", "immediate")

    assert len(received) == 1
    assert received[0]["message"] == "immediate"
    # 非队列模式的 agent 消费应返回空
    assert bus.consume("worker") == []


def test_queue_mode_mixed_agents():
    """队列模式和非队列模式的 agent 互不干扰。"""
    bus = MessageBus()
    queued_received = []
    immediate_received = []

    bus.subscribe("queued_agent", lambda e: queued_received.append(e), queue=True)
    bus.subscribe("immediate_agent", lambda e: immediate_received.append(e))

    bus.send("s", "queued_agent", "q_msg")
    bus.send("s", "immediate_agent", "i_msg")

    assert queued_received == []
    assert len(immediate_received) == 1

    q = bus.consume("queued_agent")
    assert len(q) == 1
    assert q[0]["message"] == "q_msg"


# ─── 消息回放 ───
def test_query_history_by_message_id():
    """按 message_id 精确查询。"""
    bus = MessageBus()
    bus.subscribe("a", lambda e: None)

    env = bus.send("sender", "a", "hello")
    mid = env["message_id"]

    results = bus.query_history(message_id=mid)
    assert len(results) == 1
    assert results[0]["message_id"] == mid
    assert results[0]["message"] == "hello"


def test_query_history_by_message_id_not_found():
    """查询不存在的 message_id 返回空列表。"""
    bus = MessageBus()
    results = bus.query_history(message_id="nonexistent")
    assert results == []


def test_query_history_time_range():
    """按时间范围查询。"""
    import time
    bus = MessageBus()
    bus.subscribe("a", lambda e: None)

    bus.send("s", "a", "m1")
    before = datetime.now().isoformat()
    time.sleep(0.01)
    bus.send("s", "a", "m2")
    after = datetime.now().isoformat()

    results = bus.query_history(since=before, until=after)
    assert len(results) == 1
    assert results[0]["message"] == "m2"


def test_query_history_limit():
    """limit 参数限制返回条数。"""
    bus = MessageBus()
    bus.subscribe("a", lambda e: None)

    for i in range(10):
        bus.send("s", "a", f"msg{i}")

    results = bus.query_history(limit=3)
    assert len(results) == 3
    # 返回最新的 3 条
    assert results[0]["message"] == "msg7"
    assert results[2]["message"] == "msg9"


def test_replay_all_to_recipient():
    """replay 不带 message_ids 时重放所有历史消息。"""
    bus = MessageBus()
    received = []
    bus.subscribe("new_agent", lambda e: received.append(e))

    bus.send("s", "old_agent", "historical1")
    bus.send("s", "old_agent", "historical2")

    replayed = bus.replay("new_agent")

    assert len(replayed) == 2
    assert len(received) == 2
    msgs = {r["message"] for r in received}
    assert msgs == {"historical1", "historical2"}


def test_replay_by_single_message_id():
    """按单个 message_id 重放。"""
    bus = MessageBus()
    received = []
    bus.subscribe("r", lambda e: received.append(e))

    env1 = bus.send("s", "other", "msg1")
    bus.send("s", "other", "msg2")

    replayed = bus.replay("r", message_ids=env1["message_id"])

    assert len(replayed) == 1
    assert replayed[0]["message"] == "msg1"
    assert len(received) == 1


def test_replay_by_message_ids_list():
    """按 message_ids 列表重放。"""
    bus = MessageBus()
    received = []
    bus.subscribe("r", lambda e: received.append(e))

    env1 = bus.send("s", "o", "m1")
    env2 = bus.send("s", "o", "m2")
    bus.send("s", "o", "m3")

    replayed = bus.replay("r", message_ids=[env1["message_id"], env2["message_id"]])

    assert len(replayed) == 2
    assert len(received) == 2


def test_replay_time_range():
    """按时间范围重放。"""
    import time
    bus = MessageBus()
    received = []
    bus.subscribe("r", lambda e: received.append(e))

    bus.send("s", "o", "before_range")
    before = datetime.now().isoformat()
    time.sleep(0.01)  # 确保时间戳有差异
    bus.send("s", "o", "in_range")
    after = datetime.now().isoformat()

    replayed = bus.replay("r", since=before, until=after)

    assert len(replayed) == 1
    assert replayed[0]["message"] == "in_range"


def test_replay_to_agent_without_subscribers():
    """重放到无订阅者的 agent 不报错。"""
    bus = MessageBus()
    bus.send("s", "o", "msg")

    replayed = bus.replay("no_subscriber")
    assert len(replayed) == 1


# ─── dead-letter ───
def test_dead_letter_captured_on_handler_error():
    """handler 抛异常时记录到 dead-letter。"""
    bus = MessageBus()

    def bad_handler(e):
        raise ValueError("simulated error")

    bus.subscribe("a", bad_handler)
    bus.send("s", "a", "test")

    dl = bus.get_dead_letters()
    assert len(dl) == 1
    assert dl[0]["error"] == "simulated error"
    assert dl[0]["error_type"] == "ValueError"
    assert dl[0]["agent_name"] == "a"
    assert dl[0]["message_id"] is not None


def test_dead_letter_does_not_interrupt_other_handlers():
    """一个 handler 异常不影响同 agent 的其他 handler。"""
    bus = MessageBus()
    good_called = []

    def bad_handler(e):
        raise RuntimeError("boom")

    def good_handler(e):
        good_called.append(e["message"])

    bus.subscribe("a", bad_handler)
    bus.subscribe("a", good_handler)

    bus.send("s", "a", "hello")

    assert good_called == ["hello"]
    assert len(bus.get_dead_letters()) == 1


def test_dead_letter_does_not_interrupt_broadcast():
    """broadcast 中某个 agent 的 handler 异常不影响其他 agent。"""
    bus = MessageBus()
    received_b = []

    def bad_handler(e):
        raise RuntimeError("boom")

    bus.subscribe("a", bad_handler)
    bus.subscribe("b", lambda e: received_b.append(e["message"]))

    envelopes = bus.broadcast("s", "hello")

    assert len(envelopes) == 2
    assert received_b == ["hello"]
    assert len(bus.get_dead_letters()) == 1


def test_dead_letter_contains_envelope():
    """dead-letter 记录包含完整的信封信息。"""
    bus = MessageBus()

    def bad(e):
        raise ValueError("err")

    bus.subscribe("a", bad)
    env = bus.send("sender", "a", "payload_test", payload={"key": "val"})

    dl = bus.get_dead_letters()
    assert dl[0]["envelope"]["sender"] == "sender"
    assert dl[0]["envelope"]["payload"] == {"key": "val"}
    assert dl[0]["envelope"]["message_id"] == env["message_id"]


def test_get_dead_letters_limit():
    """get_dead_letters 的 limit 参数生效。"""
    bus = MessageBus()

    def bad(e):
        raise ValueError("x")

    bus.subscribe("a", bad)
    for i in range(5):
        bus.send("s", "a", f"m{i}")

    dl = bus.get_dead_letters(limit=2)
    assert len(dl) == 2
    # 倒序：最新的在前
    assert dl[0]["envelope"]["message"] == "m4"
    assert dl[1]["envelope"]["message"] == "m3"


def test_clear_dead_letters():
    """clear_dead_letters 清空记录。"""
    bus = MessageBus()

    def bad(e):
        raise ValueError("x")

    bus.subscribe("a", bad)
    bus.send("s", "a", "test")
    assert len(bus.get_dead_letters()) == 1

    bus.clear_dead_letters()
    assert len(bus.get_dead_letters()) == 0


# ─── 向后兼容 ───
def test_backward_compatible_subscribe_without_queue():
    """不传 queue 参数时行为与之前一致。"""
    bus = MessageBus()
    received = []
    bus.subscribe("l1", lambda e: received.append(e))
    bus.send("curator", "l1", "@L1 请检索")

    assert len(received) == 1
    assert received[0]["recipient"] == "l1"
    assert received[0]["message"] == "@L1 请检索"
    assert "message_id" in received[0]


def test_backward_compatible_broadcast():
    """broadcast 行为不变。"""
    bus = MessageBus()
    seen = []
    bus.subscribe("a", lambda e: seen.append(e))
    bus.subscribe("b", lambda e: seen.append(e))
    envelopes = bus.broadcast("curator", "hi")

    assert len(envelopes) == 2
    assert len(seen) == 2


def test_backward_compatible_history():
    """history() 返回最近消息，行为不变。"""
    bus = MessageBus()
    bus.subscribe("a", lambda e: None)

    for i in range(5):
        bus.send("s", "a", f"m{i}")

    h = bus.history(limit=3)
    assert len(h) == 3
    assert h[0]["message"] == "m2"
    assert h[2]["message"] == "m4"


def test_backward_compatible_clear():
    """clear() 清空历史，行为不变。"""
    bus = MessageBus()
    bus.subscribe("a", lambda e: None)
    bus.send("s", "a", "m1")

    bus.clear()
    assert bus.history() == []


def test_backward_compatible_unsubscribe():
    """unsubscribe 移除 handler。"""
    bus = MessageBus()
    received = []
    handler = lambda e: received.append(e)  # noqa: E731

    bus.subscribe("a", handler)
    bus.send("s", "a", "before")
    assert len(received) == 1

    bus.unsubscribe("a", handler)
    bus.send("s", "a", "after")
    assert len(received) == 1  # 未增加


def test_backward_compatible_send_returns_envelope():
    """send 返回信封结构不变。"""
    bus = MessageBus()
    bus.subscribe("a", lambda e: None)

    env = bus.send("sender", "a", "hello", payload={"x": 1})

    assert env["sender"] == "sender"
    assert env["recipient"] == "a"
    assert env["message"] == "hello"
    assert env["payload"] == {"x": 1}
    assert "message_id" in env
    assert "timestamp" in env
