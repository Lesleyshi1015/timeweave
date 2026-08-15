# @agent: session-260808-golden-quasar | module: tests/test_mp_skills | ts: 2026-08-08T17:05+08:00
"""
TimeWeave Skills 单元测试

覆盖：
- 6 个 Skill 的 schema 完整性（jsonschema 可校验）
- execute 走 stub 返回结构正确
- data-validation 6 维校验逻辑
- PluginManager 注册和执行
"""
import pytest

from memory_palace_goai.skills import (
    HybridSearch,
    TemporalMapping,
    EntityGraph,
    TimeSeriesPredict,
    ArchiveCompression,
    DataValidation,
)
from agent_teams_sdk.skills.plugin_manager import PluginManager


# ─── 通用辅助 ───────────────────────────────────────────────────────────

def _validate_schema(skill):
    """用 jsonschema 验证 skill 的 input/output schema 合法性"""
    import jsonschema
    jsonschema.Draft202012Validator.check_schema(skill.schema.get("input", {}))
    jsonschema.Draft202012Validator.check_schema(skill.schema.get("output", {}))


# ─── HybridSearch ──────────────────────────────────────────────────────

class TestHybridSearch:
    """hybrid-search Skill 测试"""

    def test_schema_valid(self):
        skill = HybridSearch()
        assert skill.name == "hybrid-search"
        assert skill.version == "1.0.0"
        _validate_schema(skill)
        assert "input" in skill.schema
        assert "output" in skill.schema

    def test_search_mode(self):
        skill = HybridSearch()
        result = skill.execute(mode="search", query="测试查询", top_k=5)
        assert result["mode"] == "search"
        assert "summary" in result
        assert "results" in result
        assert "confidence" in result
        assert isinstance(result["results"], list)

    def test_index_mode(self):
        skill = HybridSearch()
        result = skill.execute(
            mode="index",
            memory_id="mem-001",
            timestamp="2026-08-08T10:00:00Z",
            content="测试内容",
        )
        assert result["mode"] == "index"
        assert result["status"] == "indexed"
        assert result["memory_id"] == "mem-001"

    def test_search_missing_query_raises(self):
        skill = HybridSearch()
        with pytest.raises(ValueError):
            skill.execute(mode="search")

    def test_index_missing_fields_raises(self):
        skill = HybridSearch()
        with pytest.raises(ValueError):
            skill.execute(mode="index", memory_id="mem-001")

    def test_search_top_k_default(self):
        skill = HybridSearch()
        result = skill.execute(mode="search", query="hello")
        assert len(result["results"]) <= 10  # 默认 top_k=10

    def test_plugin_register_and_execute(self):
        pm = PluginManager()
        pm.register(HybridSearch())
        result = pm.execute("hybrid-search", mode="search", query="plugin-test")
        assert result["mode"] == "search"


# ─── TemporalMapping ───────────────────────────────────────────────────

class TestTemporalMapping:
    """temporal-mapping Skill 测试"""

    def test_schema_valid(self):
        skill = TemporalMapping()
        assert skill.name == "temporal-mapping"
        assert skill.version == "1.0.0"
        _validate_schema(skill)

    def test_timeline_mode(self):
        skill = TemporalMapping()
        # 使用 stub 中预置的演示 memory_ids
        result = skill.execute(
            mode="timeline",
            memory_ids=["mem-api-5xx-001", "mem-db-slow-002"],
            time_range="24h",
        )
        assert result["mode"] == "timeline"
        assert "timeline_events" in result
        assert "confidence" in result
        assert len(result["timeline_events"]) == 2

    def test_extract_time_mode(self):
        skill = TemporalMapping()
        result = skill.execute(
            mode="extract_time",
            content="会议将在明天下午三点举行",
        )
        assert result["mode"] == "extract_time"
        assert "timestamp" in result

    def test_missing_mode_raises(self):
        skill = TemporalMapping()
        with pytest.raises(ValueError, match="Missing required field"):
            skill.execute()

    def test_plugin_register(self):
        pm = PluginManager()
        pm.register(TemporalMapping())
        result = pm.execute(
            "temporal-mapping",
            mode="timeline",
            memory_ids=["m1"],
        )
        assert result["mode"] == "timeline"


# ─── EntityGraph ───────────────────────────────────────────────────────

class TestEntityGraph:
    """entity-graph Skill 测试"""

    def test_schema_valid(self):
        skill = EntityGraph()
        assert skill.name == "entity-graph"
        assert skill.version == "1.0.0"
        _validate_schema(skill)

    def test_graph_mode(self):
        skill = EntityGraph()
        result = skill.execute(
            mode="graph",
            entities=["entity_A", "entity_B"],
            max_hops=2,
        )
        assert result["mode"] == "graph"
        assert "paths" in result
        assert "root_cause" in result
        assert "confidence" in result

    def test_extract_entities_mode(self):
        skill = EntityGraph()
        result = skill.execute(
            mode="extract_entities",
            content="张三和李四在北京开会",
        )
        assert result["mode"] == "extract_entities"
        assert "entity_ids" in result
        assert isinstance(result["entity_ids"], list)

    def test_missing_mode_raises(self):
        skill = EntityGraph()
        with pytest.raises(ValueError, match="Missing required field"):
            skill.execute()

    def test_plugin_register(self):
        pm = PluginManager()
        pm.register(EntityGraph())
        result = pm.execute(
            "entity-graph",
            mode="graph",
            entities=["e1"],
        )
        assert result["mode"] == "graph"


# ─── TimeSeriesPredict ─────────────────────────────────────────────────

class TestTimeSeriesPredict:
    """time-series-predict Skill 测试（⭐全球独有）"""

    def test_schema_valid(self):
        skill = TimeSeriesPredict()
        assert skill.name == "time-series-predict"
        assert skill.version == "1.0.0"
        _validate_schema(skill)

    def test_predict_default_horizon(self):
        skill = TimeSeriesPredict()
        event_series = [
            {"timestamp": "2026-08-08T08:00:00Z", "payload": {"value": 1}},
            {"timestamp": "2026-08-08T09:00:00Z", "payload": {"value": 2}},
            {"timestamp": "2026-08-08T10:00:00Z", "payload": {"value": 3}},
        ]
        result = skill.execute(event_series=event_series)
        assert "predictions" in result
        assert "confidence" in result
        assert "risk_level" in result
        assert result["risk_level"] in ("low", "medium", "high", "critical")
        assert isinstance(result["predictions"], list)

    def test_predict_custom_horizon(self):
        skill = TimeSeriesPredict()
        event_series = [
            {"timestamp": "2026-08-08T08:00:00Z"},
        ]
        result = skill.execute(event_series=event_series, horizon="7d")
        assert result["risk_level"] in ("low", "medium", "high", "critical")

    def test_missing_event_series_raises(self):
        skill = TimeSeriesPredict()
        with pytest.raises(ValueError, match="Missing required field"):
            skill.execute()

    def test_empty_event_series_raises(self):
        skill = TimeSeriesPredict()
        with pytest.raises(ValueError):
            skill.execute(event_series=[])

    def test_plugin_register(self):
        pm = PluginManager()
        pm.register(TimeSeriesPredict())
        result = pm.execute(
            "time-series-predict",
            event_series=[{"timestamp": "2026-08-08T10:00:00Z"}],
        )
        assert "predictions" in result


# ─── ArchiveCompression ────────────────────────────────────────────────

class TestArchiveCompression:
    """archive-compression Skill 测试"""

    def test_schema_valid(self):
        skill = ArchiveCompression()
        assert skill.name == "archive-compression"
        assert skill.version == "1.0.0"
        _validate_schema(skill)

    def test_archive_mode(self):
        skill = ArchiveCompression()
        result = skill.execute(
            mode="archive",
            content="重要记忆内容",
        )
        assert result["mode"] == "archive"
        assert "memory_id" in result

    def test_read_mode(self):
        skill = ArchiveCompression()
        result = skill.execute(
            mode="read",
            memory_id="archived-001",
        )
        assert result["mode"] == "read"
        assert "content" in result

    def test_missing_mode_raises(self):
        skill = ArchiveCompression()
        with pytest.raises(ValueError, match="Missing required field"):
            skill.execute()

    def test_plugin_register(self):
        pm = PluginManager()
        pm.register(ArchiveCompression())
        result = pm.execute(
            "archive-compression",
            mode="archive",
            content="test",
        )
        assert result["mode"] == "archive"


# ─── DataValidation ────────────────────────────────────────────────────

class TestDataValidation:
    """data-validation Skill 测试 — 6 维校验逻辑"""

    def test_schema_valid(self):
        skill = DataValidation()
        assert skill.name == "data-validation"
        assert skill.version == "1.0.0"
        _validate_schema(skill)

    def test_all_passed_empty_input(self):
        """空输入时所有维度通过"""
        skill = DataValidation()
        result = skill.execute()
        assert result["validation_status"] == "passed"
        assert result["errors"] == []
        assert all(result["details"].values())

    def test_completeness_fail(self):
        """维度 1：完整性 — L1 结果缺少 memory_id"""
        skill = DataValidation()
        result = skill.execute(
            l1_results=[{"content": "no_id_here"}],
        )
        assert result["validation_status"] == "failed"
        assert any(e["dimension"] == "completeness" for e in result["errors"])

    def test_timestamp_consistency_fail(self):
        """维度 2：时间戳一致性 — 非法时间戳格式"""
        skill = DataValidation()
        result = skill.execute(
            l1_results=[
                {"memory_id": "m1", "timestamp": "not-a-timestamp"},
            ],
        )
        assert result["validation_status"] == "failed"
        assert any(e["dimension"] == "timestamp_consistency" for e in result["errors"])

    def test_entity_consistency_fail(self):
        """维度 3：实体一致性 — 图谱实体不在 entities 列表中"""
        skill = DataValidation()
        result = skill.execute(
            l2_5_results=[
                {"from": "unknown_entity", "to": "e2", "relation": "test"},
            ],
            entities=["e1", "e2"],
        )
        assert result["validation_status"] == "failed"
        assert any(e["dimension"] == "entity_consistency" for e in result["errors"])

    def test_entity_consistency_pass(self):
        """维度 3：实体一致性 — 实体匹配时通过"""
        skill = DataValidation()
        result = skill.execute(
            l2_5_results=[
                {"from": "e1", "to": "e2", "relation": "test"},
            ],
            entities=["e1", "e2"],
        )
        assert result["details"]["entity_consistency"] is True

    def test_timeline_correctness_fail(self):
        """维度 5：时间线正确性 — 事件未按时间排序"""
        skill = DataValidation()
        result = skill.execute(
            l2_results=[
                {"memory_id": "m1", "timestamp": "2026-08-08T12:00:00Z", "event": "later"},
                {"memory_id": "m2", "timestamp": "2026-08-08T08:00:00Z", "event": "earlier"},
            ],
        )
        assert result["validation_status"] == "failed"
        assert any(e["dimension"] == "timeline_correctness" for e in result["errors"])

    def test_timeline_correctness_pass(self):
        """维度 5：时间线正确性 — 事件按时间排序"""
        skill = DataValidation()
        result = skill.execute(
            l2_results=[
                {"memory_id": "m1", "timestamp": "2026-08-08T08:00:00Z", "event": "first"},
                {"memory_id": "m2", "timestamp": "2026-08-08T12:00:00Z", "event": "second"},
            ],
        )
        assert result["details"]["timeline_correctness"] is True

    def test_file_integrity_fail(self):
        """维度 6：文件完整性 — 非标准数据类型"""
        skill = DataValidation()

        class NotSerializable:
            pass

        result = skill.execute(
            l1_results=[NotSerializable()],
        )
        assert result["validation_status"] == "failed"
        assert any(e["dimension"] == "file_integrity" for e in result["errors"])

    def test_multiple_dimensions_fail(self):
        """多个维度同时失败"""
        skill = DataValidation()
        result = skill.execute(
            l1_results=[
                {"content": "no_id", "timestamp": "bad-ts"},
            ],
            l2_results=[
                {"memory_id": "m2", "timestamp": "2026-08-08T12:00:00Z", "event": "e2"},
                {"memory_id": "m1", "timestamp": "2026-08-08T08:00:00Z", "event": "e1"},
            ],
        )
        assert result["validation_status"] == "failed"
        dims = {e["dimension"] for e in result["errors"]}
        assert "completeness" in dims
        assert "timestamp_consistency" in dims
        assert "timeline_correctness" in dims

    def test_details_structure(self):
        """details 包含全部 6 个维度"""
        skill = DataValidation()
        result = skill.execute()
        expected_dims = {
            "completeness",
            "timestamp_consistency",
            "entity_consistency",
            "index_validity",
            "timeline_correctness",
            "file_integrity",
        }
        assert set(result["details"].keys()) == expected_dims

    def test_plugin_register(self):
        pm = PluginManager()
        pm.register(DataValidation())
        result = pm.execute("data-validation")
        assert result["validation_status"] == "passed"


# ─── 全量集成：PluginManager auto_discover ─────────────────────────────

class TestPluginDiscovery:
    """验证 6 个 Skill 可被 PluginManager 自动发现"""

    def test_all_skills_discoverable(self):
        """从模块路径自动发现所有 6 个 Skill"""
        classes = PluginManager.auto_discover(
            "memory_palace_goai.skills"
        )
        names = {cls.name for cls in classes}
        expected = {
            "hybrid-search",
            "temporal-mapping",
            "entity-graph",
            "time-series-predict",
            "archive-compression",
            "data-validation",
        }
        assert expected.issubset(names), f"缺少: {expected - names}"

    def test_all_skills_executable_via_plugin(self):
        """所有 Skill 可通过 PluginManager 执行"""
        pm = PluginManager()
        pm.discover_and_register(
            "memory_palace_goai.skills"
        )
        registered = {s["name"] for s in pm.list_skills()}
        expected = {
            "hybrid-search",
            "temporal-mapping",
            "entity-graph",
            "time-series-predict",
            "archive-compression",
            "data-validation",
        }
        assert expected == registered, f"注册失败: {expected - registered}"

        # 逐一执行
        assert pm.execute("hybrid-search", mode="search", query="test")["mode"] == "search"
        assert pm.execute("temporal-mapping", mode="timeline", memory_ids=[])["mode"] == "timeline"
        assert pm.execute("entity-graph", mode="graph", entities=[])["mode"] == "graph"
        assert pm.execute("time-series-predict", event_series=[{"timestamp": "2026-08-08T10:00:00Z"}])["risk_level"] in ("low", "medium", "high", "critical")
        assert pm.execute("archive-compression", mode="archive", content="x")["mode"] == "archive"
        assert pm.execute("data-validation")["validation_status"] == "passed"
