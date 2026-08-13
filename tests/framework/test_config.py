# @agent: session-260808-young-raven | module: agent-teams-sdk-docs-tests | ts: 2026-08-08T16:43+08:00
"""load_config 单元测试

覆盖：
- yaml 加载（.yaml / .yml）
- json 加载
- 环境变量覆盖（ATS_ 前缀）
- 文件不存在报错
- 不支持的格式报错
"""
import json
import os
from pathlib import Path
from unittest import mock

import pytest

from agent_teams_sdk.infra.config import load_config


# ─── JSON 加载 ───

class TestJsonConfig:
    """JSON 配置文件加载"""

    def test_load_json(self, tmp_path: Path):
        """正常加载 JSON 配置"""
        cfg = {"llm": {"api_key": "sk-test", "model": "gpt-4"}}
        p = tmp_path / "config.json"
        p.write_text(json.dumps(cfg), encoding="utf-8")

        result = load_config(str(p))
        assert result["llm"]["api_key"] == "sk-test"
        assert result["llm"]["model"] == "gpt-4"

    def test_load_json_with_nested(self, tmp_path: Path):
        """嵌套 JSON 配置"""
        cfg = {
            "agents": {"curator": {"name": "C"}},
            "skills": ["search", "validate"],
        }
        p = tmp_path / "config.json"
        p.write_text(json.dumps(cfg), encoding="utf-8")

        result = load_config(str(p))
        assert result["agents"]["curator"]["name"] == "C"
        assert result["skills"] == ["search", "validate"]


# ─── YAML 加载 ───

class TestYamlConfig:
    """YAML 配置文件加载"""

    def test_load_yaml(self, tmp_path: Path):
        """正常加载 YAML 配置（PyYAML 已安装）"""
        pytest.importorskip("yaml")
        p = tmp_path / "config.yaml"
        p.write_text("llm:\n  api_key: sk-yaml\n  model: claude\n", encoding="utf-8")

        result = load_config(str(p))
        assert result["llm"]["api_key"] == "sk-yaml"
        assert result["llm"]["model"] == "claude"

    def test_load_yml_extension(self, tmp_path: Path):
        """.yml 扩展名同样支持"""
        pytest.importorskip("yaml")
        p = tmp_path / "config.yml"
        p.write_text("project: test\n", encoding="utf-8")

        result = load_config(str(p))
        assert result["project"] == "test"

    def test_yaml_missing_raises_runtime_error(self, tmp_path: Path):
        """PyYAML 未安装时抛出 RuntimeError"""
        p = tmp_path / "config.yaml"
        p.write_text("x: 1\n", encoding="utf-8")

        with mock.patch("agent_teams_sdk.infra.config.yaml", None):
            with pytest.raises(RuntimeError, match="PyYAML"):
                load_config(str(p))


# ─── 环境变量覆盖 ───

class TestEnvOverrides:
    """ATS_ 前缀环境变量覆盖"""

    def test_env_override_top_level(self, tmp_path: Path, monkeypatch):
        """顶层 key 可被环境变量覆盖"""
        cfg = {"project": "original"}
        p = tmp_path / "config.json"
        p.write_text(json.dumps(cfg), encoding="utf-8")

        monkeypatch.setenv("ATS_PROJECT", "overridden")
        result = load_config(str(p))
        assert result["project"] == "overridden"

    def test_env_override_nested(self, tmp_path: Path, monkeypatch):
        """嵌套 key 可被 ATS_XXX_YYY 覆盖"""
        cfg = {"llm": {"api_key": "original"}}
        p = tmp_path / "config.json"
        p.write_text(json.dumps(cfg), encoding="utf-8")

        monkeypatch.setenv("ATS_LLM_API_KEY", "sk-overridden")
        result = load_config(str(p))
        assert result["llm"]["api_key"] == "sk-overridden"

    def test_env_override_no_match_keeps_original(self, tmp_path: Path):
        """无匹配环境变量时保留原始值"""
        cfg = {"llm": {"model": "gpt-4"}}
        p = tmp_path / "config.json"
        p.write_text(json.dumps(cfg), encoding="utf-8")

        result = load_config(str(p))
        assert result["llm"]["model"] == "gpt-4"

    def test_env_override_list_unchanged(self, tmp_path: Path, monkeypatch):
        """列表类型不受 env 覆盖影响"""
        cfg = {"skills": ["search", "validate"]}
        p = tmp_path / "config.json"
        p.write_text(json.dumps(cfg), encoding="utf-8")

        result = load_config(str(p))
        assert result["skills"] == ["search", "validate"]

    def test_custom_env_prefix(self, tmp_path: Path, monkeypatch):
        """自定义 env_prefix 生效"""
        cfg = {"key": "original"}
        p = tmp_path / "config.json"
        p.write_text(json.dumps(cfg), encoding="utf-8")

        monkeypatch.setenv("CUSTOM_KEY", "custom-val")
        result = load_config(str(p), env_prefix="CUSTOM_")
        assert result["key"] == "custom-val"


# ─── 错误处理 ───

class TestConfigErrors:
    """配置文件错误场景"""

    def test_file_not_found(self, tmp_path: Path):
        """文件不存在时抛出 FileNotFoundError"""
        p = tmp_path / "does_not_exist.json"
        with pytest.raises(FileNotFoundError, match="配置文件不存在"):
            load_config(str(p))

    def test_unsupported_format(self, tmp_path: Path):
        """不支持的格式抛出 ValueError"""
        p = tmp_path / "config.txt"
        p.write_text("hello", encoding="utf-8")
        with pytest.raises(ValueError, match="不支持的配置格式"):
            load_config(str(p))

    def test_unsupported_format_toml(self, tmp_path: Path):
        """.toml 也是不支持的格式"""
        p = tmp_path / "config.toml"
        p.write_text("[tool]\n", encoding="utf-8")
        with pytest.raises(ValueError, match="不支持的配置格式"):
            load_config(str(p))

    def test_invalid_json_raises(self, tmp_path: Path):
        """JSON 格式错误时抛出 json.JSONDecodeError"""
        p = tmp_path / "config.json"
        p.write_text("{invalid", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            load_config(str(p))

    def test_path_object_accepted(self, tmp_path: Path):
        """支持 Path 对象作为参数"""
        cfg = {"x": 1}
        p = tmp_path / "config.json"
        p.write_text(json.dumps(cfg), encoding="utf-8")
        result = load_config(p)
        assert result["x"] == 1
