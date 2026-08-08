"""
Memory Palace API 测试套件。

覆盖：
- StubEngine 全方法返回结构
- get_service 工厂模式切换
- Engine 初始化与降级行为
"""

import re
import sys
import uuid
from pathlib import Path

import pytest

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from memory_palace_goai.mp_api import (  # noqa: E402
    Engine,
    MPService,
    StubEngine,
    get_service,
)


# ── 工厂测试 ──────────────────────────────────────────────────────────────


class TestGetService:
    """get_service 工厂函数测试。"""

    def test_stub_mode(self):
        """mode='stub' 返回 StubEngine 实例。"""
        service = get_service(mode="stub")
        assert isinstance(service, StubEngine)
        assert isinstance(service, MPService)

    def test_engine_mode(self):
        """mode='engine' 返回 Engine 实例。"""
        service = get_service(mode="engine")
        assert isinstance(service, Engine)
        assert isinstance(service, MPService)

    def test_invalid_mode(self):
        """非法 mode 抛出 ValueError。"""
        with pytest.raises(ValueError, match="未知的 mode"):
            get_service(mode="invalid")

    def test_default_mode_is_stub(self):
        """默认 mode 为 stub。"""
        service = get_service()
        assert isinstance(service, StubEngine)


# ── StubEngine Layer 1 测试 ───────────────────────────────────────────────


class TestStubLayer1:
    """StubEngine Layer 1 方法测试。"""

    @pytest.fixture
    def stub(self):
        return StubEngine()

    def test_search_returns_structure(self, stub):
        """layer1_search 返回正确的结构。"""
        result = stub.layer1_search("API 5xx 告警")
        assert "summary" in result
        assert "results" in result
        assert "confidence" in result
        assert isinstance(result["results"], list)
        assert isinstance(result["confidence"], float)
        assert 0 <= result["confidence"] <= 1

    def test_search_top_k(self, stub):
        """top_k 参数限制结果数量。"""
        result = stub.layer1_search("test", top_k=2)
        assert len(result["results"]) <= 2

    def test_search_with_context(self, stub):
        """context 参数不影响返回结构。"""
        result = stub.layer1_search("test", context={"user": "admin"})
        assert "summary" in result

    def test_index_returns_structure(self, stub):
        """layer1_index 返回正确的结构。"""
        result = stub.layer1_index("mem-test-001", "2026-08-08T10:00:00Z")
        assert result["status"] == "indexed"
        assert result["memory_id"] == "mem-test-001"

    def test_index_with_content(self, stub):
        """layer1_index 带 content 参数。"""
        result = stub.layer1_index(
            "mem-test-002",
            "2026-08-08T10:00:00Z",
            content="测试记忆内容",
        )
        assert result["status"] == "indexed"

    def test_index_without_content(self, stub):
        """layer1_index 不带 content 参数。"""
        result = stub.layer1_index("mem-test-003", "2026-08-08T10:00:00Z")
        assert result["status"] == "indexed"


# ── StubEngine Layer 2 测试 ───────────────────────────────────────────────


class TestStubLayer2:
    """StubEngine Layer 2 方法测试。"""

    @pytest.fixture
    def stub(self):
        return StubEngine()

    def test_timeline_returns_structure(self, stub):
        """layer2_timeline 返回正确的结构。"""
        result = stub.layer2_timeline(["mem-api-5xx-001", "mem-db-slow-002"])
        assert "timeline_events" in result
        assert "confidence" in result
        assert isinstance(result["timeline_events"], list)

    def test_timeline_sorted(self, stub):
        """时间线按时间排序。"""
        result = stub.layer2_timeline(["mem-api-5xx-001", "mem-db-slow-002"])
        events = result["timeline_events"]
        if len(events) > 1:
            timestamps = [e["timestamp"] for e in events]
            assert timestamps == sorted(timestamps)

    def test_extract_time_returns_timestamp(self, stub):
        """layer2_extract_time 返回时间戳。"""
        result = stub.layer2_extract_time("2026-08-08 10:23:45 UTC 发生告警")
        assert "timestamp" in result
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", result["timestamp"])

    def test_extract_time_no_match(self, stub):
        """无匹配时返回当前时间。"""
        result = stub.layer2_extract_time("没有时间戳的内容")
        assert "timestamp" in result

    def test_graph_returns_structure(self, stub):
        """layer2_5_graph 返回正确的结构。"""
        result = stub.layer2_5_graph(["API_GATEWAY", "DB_PRIMARY"], max_hops=3)
        assert "paths" in result
        assert "root_cause" in result or result["root_cause"] is None
        assert "confidence" in result

    def test_graph_paths_have_fields(self, stub):
        """图谱路径包含必要字段。"""
        result = stub.layer2_5_graph(["ent1", "ent2"])
        for path in result["paths"]:
            assert "source" in path
            assert "target" in path
            assert "relation" in path

    def test_extract_entities_returns_structure(self, stub):
        """layer2_5_extract_entities 返回正确的结构。"""
        result = stub.layer2_5_extract_entities("API_GATEWAY 连接 DB_PRIMARY 失败")
        assert "entity_ids" in result
        assert isinstance(result["entity_ids"], list)

    def test_extract_entities_fallback(self, stub):
        """无实体时返回默认实体。"""
        result = stub.layer2_5_extract_entities("普通文本无大写标识符")
        assert len(result["entity_ids"]) > 0

    def test_predict_returns_structure(self, stub):
        """layer2_7_predict 返回正确的结构。"""
        result = stub.layer2_7_predict([{"timestamp": "2026-08-08T10:00:00Z"}])
        assert "predictions" in result
        assert "confidence" in result
        assert "risk_level" in result
        assert result["risk_level"] in ("low", "medium", "high", "critical")

    def test_predict_predictions_have_fields(self, stub):
        """预测结果包含必要字段。"""
        result = stub.layer2_7_predict([])
        for pred in result["predictions"]:
            assert "timestamp" in pred
            assert "metric" in pred
            assert "predicted_value" in pred


# ── StubEngine Layer 3 测试 ───────────────────────────────────────────────


class TestStubLayer3:
    """StubEngine Layer 3 方法测试。"""

    @pytest.fixture
    def stub(self):
        return StubEngine()

    def test_archive_returns_memory_id(self, stub):
        """layer3_archive 返回 memory_id。"""
        result = stub.layer3_archive("这是一段需要归档的记忆内容")
        assert "memory_id" in result
        assert result["memory_id"].startswith("mem-")

    def test_archive_then_read(self, stub):
        """归档后可读取。"""
        archive_result = stub.layer3_archive("重要记忆内容")
        memory_id = archive_result["memory_id"]
        read_result = stub.layer3_read(memory_id)
        assert "content" in read_result
        assert read_result["content"] == "重要记忆内容"

    def test_read_nonexistent(self, stub):
        """读取不存在的记忆返回空内容。"""
        result = stub.layer3_read("mem-nonexistent")
        assert result["content"] == ""


# ── 端到端流程测试 ────────────────────────────────────────────────────────


class TestEndToEnd:
    """端到端流程测试：验证 stub 可让完整流程跑通。"""

    @pytest.fixture
    def service(self):
        return get_service(mode="stub")

    def test_full_workflow(self, service):
        """完整工作流：搜索 → 归档 → 读取 → 时间线 → 图谱 → 预测。"""
        # Layer 1: 搜索
        search_result = service.layer1_search("API 5xx 告警")
        assert search_result["confidence"] > 0

        # Layer 1: 索引
        mid = f"mem-e2e-{uuid.uuid4().hex[:6]}"
        index_result = service.layer1_index(mid, "2026-08-08T12:00:00Z", "E2E 测试")
        assert index_result["status"] == "indexed"

        # Layer 2: 时间线
        timeline_result = service.layer2_timeline([mid])
        assert len(timeline_result["timeline_events"]) >= 1

        # Layer 2: 提取时间
        time_result = service.layer2_extract_time("2026-08-08 12:00:00 事件")
        assert "timestamp" in time_result

        # Layer 2: 图谱
        entities = service.layer2_5_extract_entities("API_GATEWAY 故障")
        graph_result = service.layer2_5_graph(entities["entity_ids"])
        assert "paths" in graph_result

        # Layer 2: 预测
        predict_result = service.layer2_7_predict(
            [{"timestamp": "2026-08-08T10:00:00Z", "value": 1}]
        )
        assert predict_result["risk_level"] in ("low", "medium", "high", "critical")

        # Layer 3: 归档
        archive_result = service.layer3_archive("端到端测试记忆")
        archived_id = archive_result["memory_id"]

        # Layer 3: 读取
        read_result = service.layer3_read(archived_id)
        assert read_result["content"] == "端到端测试记忆"


# ── Engine 初始化测试 ─────────────────────────────────────────────────────


class TestEngineInit:
    """Engine 初始化测试。"""

    def test_engine_default_path(self):
        """Engine 使用默认路径初始化。"""
        engine = Engine()
        assert engine._engine_path == "F:/memory-palace-v3.0/src"

    def test_engine_custom_path(self):
        """Engine 使用自定义路径初始化。"""
        engine = Engine(engine_path="/custom/path")
        assert engine._engine_path == "/custom/path"

    def test_engine_env_path(self, monkeypatch):
        """Engine 从环境变量读取路径。"""
        monkeypatch.setenv("MP_ENGINE_PATH", "/env/path")
        engine = Engine()
        assert engine._engine_path == "/env/path"

    def test_engine_is_mp_service(self):
        """Engine 是 MPService 的子类。"""
        engine = Engine()
        assert isinstance(engine, MPService)

    def test_engine_has_stub_fallback(self):
        """Engine 有 stub 降级能力。"""
        engine = Engine(engine_path="/nonexistent/path")
        # 应降级为 stub，不抛异常
        result = engine.layer1_search("test")
        assert "summary" in result


# ── 契约完整性测试 ────────────────────────────────────────────────────────


class TestContractCompleteness:
    """验证 MPService 契约完整性（9 个方法）。"""

    def test_mp_service_has_all_methods(self):
        """MPService 定义了全部 9 个抽象方法。"""
        expected_methods = {
            "layer1_search",
            "layer1_index",
            "layer2_timeline",
            "layer2_extract_time",
            "layer2_5_graph",
            "layer2_5_extract_entities",
            "layer2_7_predict",
            "layer3_archive",
            "layer3_read",
        }
        actual_methods = {
            m for m in dir(MPService)
            if callable(getattr(MPService, m)) and not m.startswith("_")
        }
        assert expected_methods.issubset(actual_methods), (
            f"缺少方法: {expected_methods - actual_methods}"
        )

    def test_stub_implements_all_methods(self):
        """StubEngine 实现了全部 9 个方法。"""
        expected_methods = {
            "layer1_search",
            "layer1_index",
            "layer2_timeline",
            "layer2_extract_time",
            "layer2_5_graph",
            "layer2_5_extract_entities",
            "layer2_7_predict",
            "layer3_archive",
            "layer3_read",
        }
        actual_methods = {
            m for m in dir(StubEngine)
            if callable(getattr(StubEngine, m)) and not m.startswith("_")
        }
        assert expected_methods.issubset(actual_methods)

    def test_engine_implements_all_methods(self):
        """Engine 实现了全部 9 个方法。"""
        expected_methods = {
            "layer1_search",
            "layer1_index",
            "layer2_timeline",
            "layer2_extract_time",
            "layer2_5_graph",
            "layer2_5_extract_entities",
            "layer2_7_predict",
            "layer3_archive",
            "layer3_read",
        }
        actual_methods = {
            m for m in dir(Engine)
            if callable(getattr(Engine, m)) and not m.startswith("_")
        }
        assert expected_methods.issubset(actual_methods)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
