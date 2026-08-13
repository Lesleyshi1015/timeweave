# @agent: session-260808-fleet-spruce | module: agent-teams-sdk-skeleton | ts: 2026-08-08T16:35+08:00
# 设计依据：跨项目接口开发需求-MemoryPalace-SelfBrain.md §2.1（Config）
from typing import Any, Dict
from pathlib import Path
import json
import os

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def load_config(path: str | Path, env_prefix: str = "ATS_") -> Dict[str, Any]:
    """
    load_config - 加载 yaml/json 配置，并叠加环境变量覆盖（ATS_ 前缀）

    使用示例：
        cfg = load_config("config.yaml")
        api_key = cfg["llm"]["api_key"]  # 可用 ATS_LLM_API_KEY 覆盖
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"配置文件不存在: {p}")

    suffix = p.suffix.lower()
    if suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
    elif suffix in (".yaml", ".yml"):
        if yaml is None:
            raise RuntimeError("需要安装 PyYAML: pip install PyYAML")
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    else:
        raise ValueError(f"不支持的配置格式: {suffix}")

    return _apply_env_overrides(data, env_prefix)


def _apply_env_overrides(data: Any, env_prefix: str, path: str = "") -> Any:
    """递归将 ATS_XXX_YYY 环境变量覆盖到对应 key。"""
    # 叶子节点或字典节点：先检查当前路径是否有环境变量覆盖
    if path:
        env_key = env_prefix + path.upper().replace(".", "_")
        if env_key in os.environ:
            return os.environ[env_key]

    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            key_path = f"{path}.{k}" if path else k
            result[k] = _apply_env_overrides(v, env_prefix, key_path)
        return result
    elif isinstance(data, list):
        return [_apply_env_overrides(item, env_prefix, path) for item in data]
    return data
