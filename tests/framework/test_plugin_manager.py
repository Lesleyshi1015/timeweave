# @agent: session-260808-clever-orchid | module: skills/plugin_manager | ts: 2026-08-08T16:37+08:00
"""PluginManager 单元测试

覆盖：
- auto_discover（模块路径 / 目录路径）
- discover_and_register
- entry_points（mock）
- 重复注册报错
- 现有 API 向后兼容
"""
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from unittest import mock

import pytest

from agent_teams_sdk.skills.base_skill import BaseSkill
from agent_teams_sdk.skills.plugin_manager import PluginManager

# 将 tests 目录加入 sys.path 以便导入 fixture_skills
_TESTS_DIR = Path(__file__).parent
_TESTS_ROOT = _TESTS_DIR.parent
if str(_TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TESTS_ROOT))
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))


# ─── Fixture Skill 定义 ───

class ConcreteSkill(BaseSkill):
    """可实例化的具体 Skill（用于 auto_discover 测试）"""

    name = "concrete-test"
    schema = {"input": {"required": ["x"]}}

    def execute(self, **kwargs):
        return {"ok": True}


class AbstractSkillSub(BaseSkill):
    """抽象子类（不应被 auto_discover 发现）"""

    @abstractmethod
    def execute(self, **kwargs):
        pass


class AnotherAbstract(AbstractSkillSub):
    """仍为抽象（未实现 execute）"""

    extra = True


class FullConcrete(AbstractSkillSub):
    """实现了抽象方法的子类（应被发现）"""

    name = "full-concrete"

    def execute(self, **kwargs):
        return {"ok": True}


# ─── 现有 API 兼容测试 ───

class TestExistingAPI:
    """确保现有 API 不被破坏"""

    def test_register_and_get(self):
        pm = PluginManager()
        pm.register(ConcreteSkill())
        assert pm.get("concrete-test").name == "concrete-test"

    def test_register_with_name_override(self):
        pm = PluginManager()
        pm.register(ConcreteSkill(), name="custom-name")
        assert pm.get("custom-name") is not None
        with pytest.raises(KeyError):
            pm.get("concrete-test")

    def test_register_no_name_raises(self):
        class NamelessSkill(BaseSkill):
            name = ""

            def execute(self, **kwargs):
                return {}

        pm = PluginManager()
        skill = NamelessSkill()
        # BaseSkill.__init__ 会在 name 为空时自动设为类名小写，
        # 此处模拟真正无名的场景（如外部反序列化）
        skill.name = ""
        with pytest.raises(ValueError, match="必须有名"):
            pm.register(skill)

    def test_duplicate_register_raises(self):
        pm = PluginManager()
        pm.register(ConcreteSkill())
        with pytest.raises(ValueError, match="已注册"):
            pm.register(ConcreteSkill())

    def test_unregister(self):
        pm = PluginManager()
        pm.register(ConcreteSkill())
        pm.unregister("concrete-test")
        with pytest.raises(KeyError):
            pm.get("concrete-test")
        # 重复 unregister 不报错
        pm.unregister("concrete-test")

    def test_list_skills(self):
        pm = PluginManager()
        pm.register(ConcreteSkill())
        skills = pm.list_skills()
        assert len(skills) == 1
        assert skills[0]["name"] == "concrete-test"
        assert "version" in skills[0]
        assert "schema" in skills[0]

    def test_execute(self):
        pm = PluginManager()
        pm.register(ConcreteSkill())
        result = pm.execute("concrete-test", x=1)
        assert result == {"ok": True}

    def test_execute_missing_skill(self):
        pm = PluginManager()
        with pytest.raises(KeyError, match="未注册"):
            pm.execute("nope")

    def test_execute_validation(self):
        pm = PluginManager()
        pm.register(ConcreteSkill())
        with pytest.raises(ValueError, match="Missing required field"):
            pm.execute("concrete-test")  # 缺少 x


# ─── auto_discover 测试 ───

class TestAutoDiscover:
    """auto_discover 静态方法测试"""

    def test_discover_from_module_path(self):
        """从模块路径发现 fixture_skills 中的 Skill"""
        classes = PluginManager.auto_discover("tests.fixture_skills")
        names = {cls.name for cls in classes}
        assert "fixture-skill-a" in names
        assert "fixture-skill-b" in names

    def test_discover_skips_base_class(self):
        """BaseSkill 本身不应出现在结果中"""
        # 在一个只包含 BaseSkill 子类的模块中搜索
        # 通过动态模块测试
        import types
        mod = types.ModuleType("_test_mod")
        mod.BaseSkill = BaseSkill
        mod.Concrete = ConcreteSkill
        mod.Abstract = AbstractSkillSub
        sys.modules["_test_mod"] = mod
        try:
            classes = PluginManager.auto_discover("_test_mod")
            assert BaseSkill not in classes
            assert AbstractSkillSub not in classes
            assert ConcreteSkill in classes
        finally:
            del sys.modules["_test_mod"]

    def test_discover_skips_abstract(self):
        """抽象子类不应被发现"""
        import types
        mod = types.ModuleType("_test_abstract")
        mod.AbstractSkillSub = AbstractSkillSub
        mod.AnotherAbstract = AnotherAbstract
        mod.FullConcrete = FullConcrete
        sys.modules["_test_abstract"] = mod
        try:
            classes = PluginManager.auto_discover("_test_abstract")
            names = {cls.__name__ for cls in classes}
            assert "AbstractSkillSub" not in names
            assert "AnotherAbstract" not in names
            assert "FullConcrete" in names
        finally:
            del sys.modules["_test_abstract"]

    def test_discover_from_directory(self):
        """从目录路径发现 Skill"""
        fixture_dir = _TESTS_ROOT / "fixture_skills"
        classes = PluginManager.auto_discover(str(fixture_dir))
        names = {cls.name for cls in classes}
        assert "fixture-skill-a" in names
        assert "fixture-skill-b" in names

    def test_discover_invalid_module_raises(self):
        """无效模块路径应抛出 ImportError"""
        with pytest.raises(ImportError, match="无法导入"):
            PluginManager.auto_discover("this.module.does.not.exist.xyz")

    def test_discover_empty_module(self):
        """不含 Skill 的模块返回空列表"""
        import types
        mod = types.ModuleType("_empty_mod")
        mod.foo = "bar"
        sys.modules["_empty_mod"] = mod
        try:
            classes = PluginManager.auto_discover("_empty_mod")
            assert classes == []
        finally:
            del sys.modules["_empty_mod"]


# ─── discover_and_register 测试 ───

class TestDiscoverAndRegister:
    """discover_and_register 实例方法测试"""

    def test_discover_and_register(self):
        pm = PluginManager()
        names = pm.discover_and_register("tests.fixture_skills")
        assert "fixture-skill-a" in names
        assert "fixture-skill-b" in names
        # 验证已注册
        assert pm.get("fixture-skill-a").execute(query="hello") == {"result": "a:hello"}
        assert pm.get("fixture-skill-b").execute() == {"result": "from-b"}

    def test_discover_and_register_empty(self):
        """空发现结果返回空列表"""
        pm = PluginManager()
        import types
        mod = types.ModuleType("_empty_reg")
        mod.foo = 1
        sys.modules["_empty_reg"] = mod
        try:
            names = pm.discover_and_register("_empty_reg")
            assert names == []
        finally:
            del sys.modules["_empty_reg"]

    def test_discover_and_register_duplicate_raises(self):
        """重复注册时抛出明确错误"""
        pm = PluginManager()
        pm.discover_and_register("tests.fixture_skills")
        # 再次注册应报错
        with pytest.raises(ValueError, match="注册失败"):
            pm.discover_and_register("tests.fixture_skills")


# ─── entry_points 测试 ───

class TestEntryPoints:
    """entry_points 静态方法测试（mock）"""

    def test_entry_points_mock(self):
        """mock entry_points 返回 Skill 类"""

        class ExternalSkill(BaseSkill):
            name = "external-skill"

            def execute(self, **kwargs):
                return {"external": True}

        mock_ep = mock.MagicMock()
        mock_ep.load.return_value = ExternalSkill

        mock_eps = mock.MagicMock()
        mock_eps.select.return_value = [mock_ep]

        with mock.patch("importlib.metadata.entry_points", return_value=mock_eps):
            classes = PluginManager.discover_entry_points()
            assert len(classes) == 1
            assert classes[0] is ExternalSkill

    def test_entry_points_skips_non_skill(self):
        """entry_point 加载非 BaseSkill 类时被跳过"""
        mock_ep = mock.MagicMock()
        mock_ep.load.return_value = str  # 不是 BaseSkill

        mock_eps = mock.MagicMock()
        mock_eps.select.return_value = [mock_ep]

        with mock.patch("importlib.metadata.entry_points", return_value=mock_eps):
            classes = PluginManager.discover_entry_points()
            assert classes == []

    def test_entry_points_skips_abstract(self):
        """entry_point 加载抽象类时被跳过"""
        mock_ep = mock.MagicMock()
        mock_ep.load.return_value = AbstractSkillSub

        mock_eps = mock.MagicMock()
        mock_eps.select.return_value = [mock_ep]

        with mock.patch("importlib.metadata.entry_points", return_value=mock_eps):
            classes = PluginManager.discover_entry_points()
            assert classes == []

    def test_entry_points_load_failure(self):
        """entry_point 加载失败时静默跳过"""
        mock_ep = mock.MagicMock()
        mock_ep.load.side_effect = ImportError("boom")

        mock_eps = mock.MagicMock()
        mock_eps.select.return_value = [mock_ep]

        with mock.patch("importlib.metadata.entry_points", return_value=mock_eps):
            classes = PluginManager.discover_entry_points()
            assert classes == []

    def test_entry_points_no_group(self):
        """无匹配 group 时返回空列表"""
        mock_eps = mock.MagicMock()
        mock_eps.select.return_value = []

        with mock.patch("importlib.metadata.entry_points", return_value=mock_eps):
            classes = PluginManager.discover_entry_points(group="nonexistent")
            assert classes == []

    def test_entry_points_old_api(self):
        """兼容 Python 3.11 以下的 dict-style entry_points API"""

        class ExtSkill(BaseSkill):
            name = "ext-old"

            def execute(self, **kwargs):
                return {}

        mock_ep = mock.MagicMock()
        mock_ep.load.return_value = ExtSkill

        mock_eps = mock.MagicMock()
        mock_eps.select.side_effect = AttributeError("no select")
        mock_eps.get.return_value = [mock_ep]

        with mock.patch("importlib.metadata.entry_points", return_value=mock_eps):
            classes = PluginManager.discover_entry_points()
            assert len(classes) == 1
            assert classes[0] is ExtSkill
