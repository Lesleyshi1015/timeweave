# @agent: session-260808-fleet-spruce | module: agent-teams-sdk-skeleton | ts: 2026-08-08T16:35+08:00
"""agent-teams-sdk 骨架核心单元测试"""
import threading
import pytest

from agent_teams_sdk import (
    TeamRoom, MessageBus, BaseAgent, AgentState,
    BaseSkill, SchemaValidator, PluginManager,
    CuratorAgent, WorkerAgent, ValidatorAgent, ValidationResult,
    Tracer,
)


# ─── TeamRoom ───
def test_team_room_basic():
    room = TeamRoom("t1")
    room.write("q", "hello", updated_by="curator")
    assert room.read("q") == "hello"
    assert room.read("missing") is None
    assert room.has("q") and not room.has("x")


def test_team_room_versioning():
    room = TeamRoom("t2")
    room.write("k", 1, updated_by="a")
    room.write("k", 2, updated_by="b")
    entry = room.read_entry("k")
    assert entry.version == 2
    assert entry.updated_by == "b"
    assert room.read_all() == {"k": 2}


def test_team_room_thread_safety():
    room = TeamRoom("t3")
    errors = []

    def writer(i):
        try:
            for j in range(200):
                room.write(f"key{i}", j, updated_by=f"w{i}")
        except Exception as e:  # pragma: no cover
            errors.append(e)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len(room.keys()) == 8


# ─── MessageBus ───
def test_message_bus_point_to_point():
    bus = MessageBus()
    received = []
    bus.subscribe("l1", lambda env: received.append(env))
    bus.send("curator", "l1", "@L1 请检索")
    assert len(received) == 1
    assert received[0]["recipient"] == "l1"
    assert received[0]["message"] == "@L1 请检索"
    assert "trace_id" in received[0] or "message_id" in received[0]


def test_message_bus_broadcast():
    bus = MessageBus()
    seen = []
    bus.subscribe("a", lambda e: seen.append(e))
    bus.subscribe("b", lambda e: seen.append(e))
    bus.broadcast("curator", "hi")
    assert len(seen) == 2


# ─── BaseAgent ───
def test_base_agent_state():
    class Dummy(BaseAgent):
        def on_message(self, message): pass
        def execute(self, task): return None

    room = TeamRoom("t4")
    a = Dummy("d1", "worker", room)
    assert a.get_state() == {"name": "d1", "role": "worker", "state": AgentState.IDLE.value}


# ─── BaseSkill / SchemaValidator / PluginManager ───
def test_base_skill_validation():
    class SearchSkill(BaseSkill):
        name = "search"
        schema = {"input": {"required": ["query"]}}

        def execute(self, **kwargs):
            return {"ok": True}

    s = SearchSkill()
    assert s.validate_input(query="x") is True
    with pytest.raises(ValueError):
        s.validate_input()  # 缺 query
    assert s.get_schema()["name"] == "search"


def test_schema_validator_registry():
    sv = SchemaValidator()
    sv.register("search", {"input": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
                           "output": {"type": "object"}})
    assert sv.validate_input("search", query="x") is True
    with pytest.raises(ValueError):
        sv.validate_input("search", query=123)  # 类型不符
    with pytest.raises(ValueError):
        sv.validate_input("unknown", query="x")


def test_plugin_manager():
    class SkillA(BaseSkill):
        name = "skill-a"

        def execute(self, **kwargs):
            return {"from": "a"}

    pm = PluginManager()
    pm.register(SkillA())
    assert pm.list_skills()[0]["name"] == "skill-a"
    assert pm.execute("skill-a") == {"from": "a"}
    with pytest.raises(KeyError):
        pm.get("missing")


# ─── 角色模式 ───
def test_curator_worker_validator_flow():
    room = TeamRoom("flow")

    class C(CuratorAgent):
        def evaluate_completeness(self, blackboard):
            return 0.9 if blackboard.get("w1_result") else 0.0

    class W(WorkerAgent):
        def do_work(self, task):
            return {"done": True}

    class V(ValidatorAgent):
        def validate(self, blackboard):
            return ValidationResult(True, [], []) if blackboard.get("w1_result") else ValidationResult(False, ["missing"], [])

    curator = C("curator", room, workers=["w1"])
    w1 = W("w1", room)
    v = V("v", room)

    curator.dispatch_task("w1", "@w1 干活")
    w1.on_message("@w1 干活")
    result = curator.collect_result("w1")
    assert result == {"done": True}
    assert curator.evaluate_completeness(room.read_all()) == 0.9

    v.on_message("@v 检查")
    v_result = room.read("v_result")
    assert v_result["passed"] is True


# ─── Tracer ───
def test_tracer():
    tr = Tracer()
    tid = tr.start_trace("query")
    span = tr.start_span(tid, "l1-search", span_type="skill")
    tr.end_span(span, status="ok", result={"n": 1})
    spans = tr.get_trace(tid)
    assert len(spans) == 2
    assert spans[1]["status"] == "ok"
