# @agent: session-260808-young-raven | module: agent-teams-sdk-docs-tests | ts: 2026-08-08T16:43+08:00
"""SchemaValidator 单元测试

覆盖：
- register：注册成功 + schema 校验（非法 schema 抛 jsonschema 错误）
- validate_input：通过 / 失败 / 未注册报错
- validate_output：通过 / 失败 / 未注册报错
- unregister：注销后查询不到
- registered：返回已注册列表
"""
import pytest

from agent_teams_sdk.skills.schema_validator import SchemaValidator


# ─── register ───

class TestRegister:
    """register 方法测试"""

    def test_register_success(self):
        """注册合法 schema 成功"""
        sv = SchemaValidator()
        sv.register("search", {
            "input": {"type": "object", "properties": {"query": {"type": "string"}}},
            "output": {"type": "object"},
        })
        assert "search" in sv.registered()

    def test_register_invalid_input_schema_raises(self):
        """input schema 非法时抛出 jsonschema 错误"""
        sv = SchemaValidator()
        with pytest.raises(Exception):  # jsonschema 可能抛 SchemaError
            sv.register("bad", {"input": {"type": "invalid_type_xyz"}})

    def test_register_invalid_output_schema_raises(self):
        """output schema 非法时抛出 jsonschema 错误"""
        sv = SchemaValidator()
        with pytest.raises(Exception):
            sv.register("bad", {
                "input": {},
                "output": {"type": "not_a_real_type"},
            })

    def test_register_overwrite(self):
        """重复注册同名 skill 会覆盖"""
        sv = SchemaValidator()
        sv.register("s", {"input": {"properties": {"a": {"type": "string"}}}})
        sv.register("s", {"input": {"properties": {"b": {"type": "integer"}}}})
        # 覆盖后只有一条记录
        assert len(sv.registered()) == 1


# ─── validate_input ───

class TestValidateInput:
    """validate_input 方法测试"""

    def test_validate_input_pass(self):
        """输入符合 schema 时返回 True"""
        sv = SchemaValidator()
        sv.register("search", {
            "input": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            "output": {},
        })
        assert sv.validate_input("search", query="hello") is True

    def test_validate_input_optional_fields(self):
        """可选字段不传也通过"""
        sv = SchemaValidator()
        sv.register("s", {
            "input": {"properties": {"optional": {"type": "string"}}},
            "output": {},
        })
        assert sv.validate_input("s") is True

    def test_validate_input_failure_wrong_type(self):
        """类型不符时抛出 ValueError"""
        sv = SchemaValidator()
        sv.register("search", {
            "input": {"properties": {"query": {"type": "string"}}, "required": ["query"]},
            "output": {},
        })
        with pytest.raises(ValueError, match="输入校验失败"):
            sv.validate_input("search", query=123)

    def test_validate_input_failure_missing_required(self):
        """缺少必填字段时抛出 ValueError"""
        sv = SchemaValidator()
        sv.register("s", {
            "input": {"required": ["must_have"]},
            "output": {},
        })
        with pytest.raises(ValueError, match="输入校验失败"):
            sv.validate_input("s")

    def test_validate_input_unregistered_raises(self):
        """未注册的 skill 抛出 ValueError"""
        sv = SchemaValidator()
        with pytest.raises(ValueError, match="未注册 Schema"):
            sv.validate_input("unknown", query="x")

    def test_validate_input_empty_schema(self):
        """空 input schema 允许任意输入"""
        sv = SchemaValidator()
        sv.register("free", {"input": {}, "output": {}})
        assert sv.validate_input("free", anything="goes") is True


# ─── validate_output ───

class TestValidateOutput:
    """validate_output 方法测试"""

    def test_validate_output_pass(self):
        """输出符合 schema 时返回 True"""
        sv = SchemaValidator()
        sv.register("search", {
            "input": {},
            "output": {"type": "object", "properties": {"results": {"type": "array"}}},
        })
        assert sv.validate_output("search", {"results": []}) is True

    def test_validate_output_failure(self):
        """输出不符合 schema 时抛出 ValueError"""
        sv = SchemaValidator()
        sv.register("s", {
            "input": {},
            "output": {"type": "object", "properties": {"count": {"type": "integer"}}},
        })
        with pytest.raises(ValueError, match="输出校验失败"):
            sv.validate_output("s", {"count": "not-an-int"})

    def test_validate_output_unregistered_raises(self):
        """未注册的 skill 抛出 ValueError"""
        sv = SchemaValidator()
        with pytest.raises(ValueError, match="未注册 Schema"):
            sv.validate_output("unknown", {"x": 1})

    def test_validate_output_empty_schema(self):
        """空 output schema 允许任意输出"""
        sv = SchemaValidator()
        sv.register("free", {"input": {}, "output": {}})
        assert sv.validate_output("free", "anything") is True


# ─── unregister ───

class TestUnregister:
    """unregister 方法测试"""

    def test_unregister_removes_skill(self):
        """注销后 skill 不在 registered 中"""
        sv = SchemaValidator()
        sv.register("s", {"input": {}, "output": {}})
        assert "s" in sv.registered()

        sv.unregister("s")
        assert "s" not in sv.registered()

    def test_unregister_unknown_no_error(self):
        """注销不存在的 skill 不报错"""
        sv = SchemaValidator()
        sv.unregister("does_not_exist")  # 不应抛出

    def test_unregister_then_reregister(self):
        """注销后可重新注册"""
        sv = SchemaValidator()
        sv.register("s", {"input": {"required": ["a"]}, "output": {}})
        sv.unregister("s")
        sv.register("s", {"input": {"required": ["b"]}, "output": {}})
        assert sv.validate_input("s", b=1) is True
        with pytest.raises(ValueError):
            sv.validate_input("s", a=1)


# ─── registered ───

class TestRegistered:
    """registered 方法测试"""

    def test_registered_empty(self):
        """初始状态为空列表"""
        sv = SchemaValidator()
        assert sv.registered() == []

    def test_registered_returns_names(self):
        """返回所有已注册的 skill 名称"""
        sv = SchemaValidator()
        sv.register("a", {"input": {}, "output": {}})
        sv.register("b", {"input": {}, "output": {}})
        names = sv.registered()
        assert set(names) == {"a", "b"}

    def test_registered_returns_list_not_reference(self):
        """返回列表副本，修改不影响内部状态"""
        sv = SchemaValidator()
        sv.register("s", {"input": {}, "output": {}})
        names = sv.registered()
        names.append("fake")
        assert "fake" not in sv.registered()
