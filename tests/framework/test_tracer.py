# @agent: session-260808-vital-stag | module: infra/tracer | ts: 2026-08-08T16:37+08:00
"""Tracer 模块测试（含新增 SpanType / export_json / to_otlp_exportable）"""
import json
import os
import tempfile
import pytest
from datetime import datetime

from agent_teams_sdk.infra.tracer import Tracer, SpanType


# ── SpanType 枚举测试 ──────────────────────────────────────────────────────────

class TestSpanType:
    """SpanType 枚举值验证"""

    def test_enum_values(self):
        """五个枚举值必须存在且 value 正确"""
        assert SpanType.AGENT.value == "agent"
        assert SpanType.SKILL.value == "skill"
        assert SpanType.MCP.value == "mcp"
        assert SpanType.RAG.value == "rag"
        assert SpanType.LLM.value == "llm"

    def test_is_str_subclass(self):
        """SpanType 应继承 str，支持与字符串直接比较"""
        assert SpanType.AGENT == "agent"
        assert "agent" == SpanType.AGENT
        assert SpanType.AGENT in {"agent", "skill"}

    def test_enum_membership(self):
        """合法类型字符串应能通过枚举值集合校验"""
        valid = {t.value for t in SpanType}
        assert valid == {"agent", "skill", "mcp", "rag", "llm"}


# ── span_type 参数校验测试 ────────────────────────────────────────────────────

class TestSpanTypeValidation:
    """start_span 的 span_type 参数校验"""

    def test_accept_span_type_enum(self):
        """传入 SpanType 枚举值应正常创建 span"""
        tracer = Tracer()
        tid = tracer.start_trace("test")
        sid = tracer.start_span(tid, "my_skill", span_type=SpanType.SKILL)
        spans = tracer.get_trace(tid)
        skill_spans = [s for s in spans if s["span_id"] == sid]
        assert len(skill_spans) == 1
        assert skill_spans[0]["type"] == "skill"

    def test_accept_string_span_type(self):
        """传入合法字符串应正常创建 span"""
        tracer = Tracer()
        tid = tracer.start_trace("test")
        sid = tracer.start_span(tid, "my_llm", span_type="llm")
        spans = tracer.get_trace(tid)
        assert spans[-1]["span_id"] == sid
        assert spans[-1]["type"] == "llm"

    def test_reject_invalid_string(self):
        """非法字符串应抛出 ValueError"""
        tracer = Tracer()
        tid = tracer.start_trace("test")
        with pytest.raises(ValueError) as exc_info:
            tracer.start_span(tid, "bad", span_type="invalid_type")
        assert "非法 span_type" in str(exc_info.value)
        assert "invalid_type" in str(exc_info.value)

    def test_reject_non_string_type(self):
        """非 str / SpanType 类型应抛出 TypeError"""
        tracer = Tracer()
        tid = tracer.start_trace("test")
        with pytest.raises(TypeError) as exc_info:
            tracer.start_span(tid, "bad", span_type=123)  # type: ignore[arg-type]
        assert "span_type 必须为 str 或 SpanType" in str(exc_info.value)

    def test_default_span_type_is_agent(self):
        """不传 span_type 时默认值为 agent（向后兼容）"""
        tracer = Tracer()
        tid = tracer.start_trace("test")
        sid = tracer.start_span(tid, "default_span")
        spans = tracer.get_trace(tid)
        assert spans[-1]["type"] == "agent"


# ── export_json 测试 ──────────────────────────────────────────────────────────

class TestExportJson:
    """export_json 落盘测试"""

    def test_export_json_writes_file(self):
        """export_json 应写入 UTF-8 JSON 文件"""
        tracer = Tracer()
        tid = tracer.start_trace("export_test")
        tracer.start_span(tid, "span_a", span_type=SpanType.AGENT)
        tracer.start_span(tid, "span_b", span_type=SpanType.LLM)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False,
                                          encoding="utf-8") as f:
            path = f.name

        try:
            tracer.export_json(path)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert isinstance(data, list)
            assert len(data) == 3  # 1 trace + 2 spans
            trace_records = [d for d in data if d["trace_id"] == tid]
            assert len(trace_records) == 3
        finally:
            os.unlink(path)

    def test_export_json_preserves_chinese(self):
        """export_json 应正确保存中文字符（ensure_ascii=False）"""
        tracer = Tracer()
        tid = tracer.start_trace("中文测试")
        tracer.start_span(tid, "搜索技能", span_type=SpanType.SKILL,
                          attrs={"query": "你好世界"})

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False,
                                          encoding="utf-8") as f:
            path = f.name

        try:
            tracer.export_json(path)
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()

            assert "中文测试" in raw
            assert "搜索技能" in raw
            assert "你好世界" in raw
        finally:
            os.unlink(path)

    def test_export_json_empty(self):
        """空 tracer 导出应为空数组"""
        tracer = Tracer()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False,
                                          encoding="utf-8") as f:
            path = f.name

        try:
            tracer.export_json(path)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data == []
        finally:
            os.unlink(path)


# ── to_otlp_exportable 测试 ───────────────────────────────────────────────────

class TestToOtlpExportable:
    """to_otlp_exportable 结构验证"""

    def test_returns_list_of_dicts(self):
        """返回值应为字典列表"""
        tracer = Tracer()
        tid = tracer.start_trace("otlp_test")
        tracer.start_span(tid, "agent_root", span_type=SpanType.AGENT)
        result = tracer.to_otlp_exportable()
        assert isinstance(result, list)
        assert all(isinstance(item, dict) for item in result)

    def test_otlp_required_fields(self):
        """每个 OTLP span 应包含推荐字段"""
        tracer = Tracer()
        tid = tracer.start_trace("otlp_test")
        tracer.start_span(tid, "llm_call", span_type=SpanType.LLM)
        result = tracer.to_otlp_exportable()

        required = {
            "trace_id", "span_id", "parent_span_id", "name",
            "kind", "start_time_unix_nano", "end_time_unix_nano",
            "status_code", "attributes",
        }
        for item in result:
            assert required.issubset(item.keys()), f"缺少字段: {required - item.keys()}"

    def test_otlp_kind_mapping(self):
        """span type → OTLP kind 映射应正确"""
        tracer = Tracer()
        tid = tracer.start_trace("kind_test")
        tracer.start_span(tid, "a", span_type=SpanType.AGENT)
        tracer.start_span(tid, "b", span_type=SpanType.SKILL)
        tracer.start_span(tid, "c", span_type=SpanType.MCP)
        tracer.start_span(tid, "d", span_type=SpanType.RAG)
        tracer.start_span(tid, "e", span_type=SpanType.LLM)

        result = tracer.to_otlp_exportable()
        by_name = {item["name"]: item["kind"] for item in result if item["name"] in "abcde"}

        assert by_name["a"] == "INTERNAL"
        assert by_name["b"] == "INTERNAL"
        assert by_name["c"] == "CLIENT"
        assert by_name["d"] == "CLIENT"
        assert by_name["e"] == "CLIENT"

    def test_otlp_status_code_mapping(self):
        """status → status_code 映射应正确"""
        tracer = Tracer()
        tid = tracer.start_trace("status_test")
        sid_ok = tracer.start_span(tid, "ok_span")
        sid_err = tracer.start_span(tid, "err_span")
        sid_un = tracer.start_span(tid, "unended_span")

        tracer.end_span(sid_ok, status="ok")
        tracer.end_span(sid_err, status="error")
        # sid_un 不结束

        result = tracer.to_otlp_exportable()
        by_id = {item["span_id"][:12]: item["status_code"] for item in result}

        # span_id 在 OTLP 中会被补齐到 16 字符，但前缀仍匹配
        ok_items = [r for r in result if r["name"] == "ok_span"]
        err_items = [r for r in result if r["name"] == "err_span"]
        un_items = [r for r in result if r["name"] == "unended_span"]

        assert ok_items[0]["status_code"] == "OK"
        assert err_items[0]["status_code"] == "ERROR"
        assert un_items[0]["status_code"] == "UNSET"

    def test_otlp_trace_id_padded(self):
        """trace_id 应补齐到 32 字符"""
        tracer = Tracer()
        tid = tracer.start_trace("pad_test")  # 16字符
        tracer.start_span(tid, "x")
        result = tracer.to_otlp_exportable()
        for item in result:
            assert len(item["trace_id"]) == 32
            assert item["trace_id"].startswith(tid)

    def test_otlp_parent_span_id_null_for_trace_root(self):
        """trace 根节点的 parent_span_id 应为 null"""
        tracer = Tracer()
        tid = tracer.start_trace("parent_test")
        result = tracer.to_otlp_exportable()
        trace_items = [r for r in result if r["name"] == "parent_test" and r["parent_span_id"] is None]
        assert len(trace_items) >= 1


# ── 向后兼容测试（现有 API 行为不变） ──────────────────────────────────────────

class TestBackwardCompatibility:
    """确保现有 API 签名与行为不被破坏"""

    def test_start_trace_returns_hex_id(self):
        tracer = Tracer()
        tid = tracer.start_trace("compat_test")
        assert len(tid) == 16
        assert all(c in "0123456789abcdef" for c in tid)

    def test_start_span_returns_hex_id(self):
        tracer = Tracer()
        tid = tracer.start_trace("t")
        sid = tracer.start_span(tid, "s")
        assert len(sid) == 12
        assert all(c in "0123456789abcdef" for c in sid)

    def test_end_span_sets_status(self):
        tracer = Tracer()
        tid = tracer.start_trace("t")
        sid = tracer.start_span(tid, "s")
        tracer.end_span(sid, status="ok", result={"key": "val"})
        spans = tracer.get_trace(tid)
        target = [s for s in spans if s["span_id"] == sid][0]
        assert target["status"] == "ok"
        assert target["result"] == {"key": "val"}
        assert target["end"] is not None

    def test_get_trace_returns_only_matching(self):
        tracer = Tracer()
        tid1 = tracer.start_trace("a")
        tid2 = tracer.start_trace("b")
        tracer.start_span(tid1, "s1")
        tracer.start_span(tid2, "s2")
        assert len(tracer.get_trace(tid1)) == 2
        assert len(tracer.get_trace(tid2)) == 2

    def test_export_returns_all_spans(self):
        tracer = Tracer()
        tracer.start_trace("a")
        tracer.start_trace("b")
        assert len(tracer.export()) == 2

    def test_clear_removes_all(self):
        tracer = Tracer()
        tracer.start_trace("a")
        tracer.clear()
        assert tracer.export() == []

    def test_parent_span_id_optional(self):
        """parent_span_id 仍为可选参数"""
        tracer = Tracer()
        tid = tracer.start_trace("t")
        root = tracer.start_span(tid, "root")
        child = tracer.start_span(tid, "child", parent_span_id=root)
        spans = tracer.get_trace(tid)
        child_rec = [s for s in spans if s["span_id"] == child][0]
        assert child_rec["parent_span_id"] == root

    def test_attrs_default_empty_dict(self):
        """不传 attrs 时默认为空字典"""
        tracer = Tracer()
        tid = tracer.start_trace("t")
        sid = tracer.start_span(tid, "s")
        spans = tracer.get_trace(tid)
        assert spans[-1]["attrs"] == {}
