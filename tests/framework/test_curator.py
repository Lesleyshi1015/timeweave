# @agent: session-260808-young-raven | module: agent-teams-sdk-docs-tests | ts: 2026-08-08T16:43+08:00
"""CuratorAgent 单元测试

覆盖：
- dispatch_task 写入黑板
- collect_result 读取 Worker 结果
- reconstruct_result 整合所有 Worker 结果
- execute 默认实现（读取黑板 + reconstruct）
- evaluate_completeness 为抽象方法，CuratorAgent 不可直接实例化
"""
import pytest

from agent_teams_sdk import TeamRoom, CuratorAgent, AgentState


# ─── 具体子类（用于需要实例化的测试） ───

class ConcreteCurator(CuratorAgent):
    """实现了 evaluate_completeness 的具体 Curator（测试用）"""

    def evaluate_completeness(self, blackboard):
        return 1.0 if blackboard.get("w1_result") else 0.0


# ─── dispatch_task ───

class TestDispatchTask:
    """dispatch_task 方法测试"""

    def test_dispatch_writes_to_blackboard(self):
        """dispatch_task 将任务写入黑板"""
        room = TeamRoom("dispatch-test")
        curator = ConcreteCurator("c", room, workers=["w1"])

        curator.dispatch_task("w1", "请执行搜索")

        assert room.has("task_to_w1")
        assert room.read("task_to_w1") == "请执行搜索"

    def test_dispatch_multiple_workers(self):
        """可向多个 worker 分发任务"""
        room = TeamRoom("multi-dispatch")
        curator = ConcreteCurator("c", room, workers=["w1", "w2"])

        curator.dispatch_task("w1", "task1")
        curator.dispatch_task("w2", "task2")

        assert room.read("task_to_w1") == "task1"
        assert room.read("task_to_w2") == "task2"

    def test_dispatch_updated_by(self):
        """写入的黑板条目 updated_by 为 curator 名称"""
        room = TeamRoom("updated-by-test")
        curator = ConcreteCurator("my-curator", room, workers=["w1"])
        curator.dispatch_task("w1", "go")

        entry = room.read_entry("task_to_w1")
        assert entry.updated_by == "my-curator"


# ─── collect_result ───

class TestCollectResult:
    """collect_result 方法测试"""

    def test_collect_existing_result(self):
        """收集已存在的 Worker 结果"""
        room = TeamRoom("collect-test")
        curator = ConcreteCurator("c", room, workers=["w1"])

        room.write("w1_result", {"data": "worker-done"}, updated_by="w1")
        result = curator.collect_result("w1")

        assert result == {"data": "worker-done"}

    def test_collect_missing_result(self):
        """收集不存在的结果返回 None"""
        room = TeamRoom("collect-missing")
        curator = ConcreteCurator("c", room, workers=["w1"])

        result = curator.collect_result("w1")
        assert result is None


# ─── reconstruct_result ───

class TestReconstructResult:
    """reconstruct_result 方法测试"""

    def test_reconstruct_all_workers(self):
        """整合所有 Worker 的结果"""
        room = TeamRoom("reconstruct-test")
        curator = ConcreteCurator("c", room, workers=["w1", "w2"])

        room.write("w1_result", {"part": 1}, updated_by="w1")
        room.write("w2_result", {"part": 2}, updated_by="w2")

        result = curator.reconstruct_result(room.read_all())

        assert result == {"w1": {"part": 1}, "w2": {"part": 2}}

    def test_reconstruct_partial_results(self):
        """部分 Worker 有结果时只整合存在的"""
        room = TeamRoom("partial-test")
        curator = ConcreteCurator("c", room, workers=["w1", "w2"])

        room.write("w1_result", {"done": True}, updated_by="w1")
        # w2_result 未写入

        result = curator.reconstruct_result(room.read_all())

        assert result == {"w1": {"done": True}}
        assert "w2" not in result

    def test_reconstruct_empty(self):
        """黑板为空时返回空字典"""
        room = TeamRoom("empty-test")
        curator = ConcreteCurator("c", room, workers=["w1"])

        result = curator.reconstruct_result(room.read_all())
        assert result == {}


# ─── execute 默认实现 ───

class TestExecute:
    """execute 默认实现测试"""

    def test_execute_default_implementation(self):
        """默认 execute 读取黑板并 reconstruct"""
        room = TeamRoom("exec-test")
        curator = ConcreteCurator("c", room, workers=["w1"])

        room.write("w1_result", {"answer": 42}, updated_by="w1")

        result = curator.execute({})

        assert result == {"w1": {"answer": 42}}

    def test_execute_sets_state(self):
        """execute 执行过程中状态变为 RUNNING，结束后为 COMPLETED"""
        room = TeamRoom("state-test")
        curator = ConcreteCurator("c", room, workers=[])

        assert curator.state == AgentState.IDLE
        curator.execute({})
        assert curator.state == AgentState.COMPLETED

    def test_execute_uses_task_dict(self):
        """execute 接受 task 字典参数（默认实现不使用）"""
        room = TeamRoom("task-param-test")
        curator = ConcreteCurator("c", room, workers=[])

        result = curator.execute({"action": "test", "priority": "high"})
        assert result == {}


# ─── on_message ───

class TestOnMessage:
    """on_message 方法测试"""

    def test_on_message_writes_user_message(self):
        """on_message 将消息写入黑板 user_message 键"""
        room = TeamRoom("on-msg-test")
        curator = ConcreteCurator("c", room, workers=[])

        curator.on_message("用户查询")

        assert room.read("user_message") == "用户查询"
        entry = room.read_entry("user_message")
        assert entry.updated_by == "c"


# ─── 抽象方法 ───

class TestAbstractMethods:
    """抽象方法约束测试"""

    def test_curator_cannot_instantiate_without_evaluate(self):
        """未实现 evaluate_completeness 的 CuratorAgent 不可实例化"""
        with pytest.raises(TypeError, match="evaluate_completeness"):
            CuratorAgent("c", TeamRoom("x"), workers=[])

    def test_curator_with_evaluate_completeness(self):
        """实现 evaluate_completeness 后可实例化"""
        room = TeamRoom("complete-test")
        curator = ConcreteCurator("c", room, workers=["w1"])
        assert curator.evaluate_completeness({}) == 0.0

    def test_evaluate_completeness_receives_blackboard(self):
        """evaluate_completeness 接收完整黑板"""
        room = TeamRoom("inspect-test")
        curator = ConcreteCurator("c", room, workers=["w1"])

        assert curator.evaluate_completeness({}) == 0.0
        assert curator.evaluate_completeness({"w1_result": {"ok": True}}) == 1.0
