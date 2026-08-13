# @agent: session-260808-clever-orchid | module: skills/plugin_manager | ts: 2026-08-08T16:37+08:00
# 设计依据：跨项目接口开发需求-MemoryPalace-SelfBrain.md §2.1（PluginManager）
import importlib
import importlib.metadata
import inspect
import os
import pkgutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Type

from agent_teams_sdk.skills.base_skill import BaseSkill


class PluginManager:
    """
    PluginManager - Skill 注册/加载/发现

    - register() 显式注册 Skill 实例
    - auto_discover() 从包目录自动发现 BaseSkill 子类
    - get() / list_skills() 供 Agent 查询可用能力
    """

    def __init__(self) -> None:
        self._skills: Dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill, name: str | None = None) -> None:
        key = name or skill.name
        if not key:
            raise ValueError("Skill 必须有名（构造或 register 时指定）")
        if key in self._skills:
            raise ValueError(f"Skill '{key}' 已注册")
        self._skills[key] = skill

    def unregister(self, name: str) -> None:
        self._skills.pop(name, None)

    def get(self, name: str) -> BaseSkill:
        if name not in self._skills:
            raise KeyError(f"Skill '{name}' 未注册")
        return self._skills[name]

    def list_skills(self) -> List[Dict[str, Any]]:
        return [
            {"name": skill.name, "version": skill.version, "schema": skill.get_schema()}
            for skill in self._skills.values()
        ]

    def execute(self, name: str, **kwargs) -> Any:
        skill = self.get(name)
        skill.validate_input(**kwargs)
        return skill.execute(**kwargs)

    @staticmethod
    def auto_discover(package: str) -> List[Type[BaseSkill]]:
        """
        从指定包（模块路径或目录）自动发现 BaseSkill 子类。

        扫描策略：
        1. 若 package 是 Python 模块路径（如 "my_pkg.skills"），则导入该模块并遍历其
           所有属性，收集 BaseSkill 的非抽象子类。
        2. 若 package 是文件系统目录路径，则遍历目录下所有 .py 文件，动态导入并收集。

        自动跳过：
        - BaseSkill 本身
        - 抽象类（含未实现的抽象方法）
        - 私有模块（以 _ 开头）

        Parameters
        ----------
        package : str
            Python 模块路径（如 "agent_teams_sdk.skills"）或文件系统目录路径。

        Returns
        -------
        List[Type[BaseSkill]]
            发现的所有可实例化 BaseSkill 子类列表。
        """
        discovered: List[Type[BaseSkill]] = []
        seen: set = set()

        # 判断是目录路径还是模块路径
        if os.path.isdir(package):
            discovered.extend(
                PluginManager._discover_from_directory(Path(package), seen)
            )
        else:
            discovered.extend(
                PluginManager._discover_from_module(package, seen)
            )

        return discovered

    @staticmethod
    def _discover_from_module(
        module_path: str, seen: set
    ) -> List[Type[BaseSkill]]:
        """从 Python 模块路径发现 BaseSkill 子类。"""
        discovered: List[Type[BaseSkill]] = []
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:  # pragma: no cover
            raise ImportError(f"无法导入模块 '{module_path}': {e}") from e

        for name, obj in inspect.getmembers(module, inspect.isclass):
            candidate = PluginManager._check_skill_class(obj, seen)
            if candidate is not None:
                discovered.append(candidate)

        # 递归扫描子模块
        pkg_path = getattr(module, "__path__", None)
        if pkg_path is not None:
            for _finder, sub_name, _ispkg in pkgutil.iter_modules(pkg_path):
                full_sub = f"{module_path}.{sub_name}"
                if not sub_name.startswith("_"):
                    discovered.extend(
                        PluginManager._discover_from_module(full_sub, seen)
                    )

        return discovered

    @staticmethod
    def _discover_from_directory(
        directory: Path, seen: set
    ) -> List[Type[BaseSkill]]:
        """从文件系统目录发现 BaseSkill 子类。"""
        discovered: List[Type[BaseSkill]] = []
        for py_file in directory.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue
            rel = py_file.relative_to(directory)
            module_name = str(rel.with_suffix("")).replace(os.sep, ".")
            # 尝试将目录作为包导入（需要 __init__.py）
            # 若目录不在 sys.path 中，临时添加
            dir_parent = str(directory.parent)
            added = False
            if dir_parent not in sys.path:
                sys.path.insert(0, dir_parent)
                added = True
            try:
                module_name = directory.name + "." + module_name
                sub_discovered = PluginManager._discover_from_module(
                    module_name, seen
                )
                discovered.extend(sub_discovered)
            except ImportError:
                pass  # 目录不是合法包，跳过
            finally:
                if added:
                    sys.path.remove(dir_parent)

        return discovered

    @staticmethod
    def _check_skill_class(
        obj: type, seen: set
    ) -> Type[BaseSkill] | None:
        """检查一个类是否为合法的 BaseSkill 子类（非抽象、未重复）。"""
        if obj in seen:
            return None
        if obj is BaseSkill:
            return None
        if not issubclass(obj, BaseSkill):
            return None
        if inspect.isabstract(obj):
            return None
        seen.add(obj)
        return obj  # type: ignore[return-value]

    def discover_and_register(self, package: str) -> List[str]:
        """
        自动发现指定包中的 BaseSkill 子类并注册到当前 manager。

        Parameters
        ----------
        package : str
            Python 模块路径或文件系统目录路径（同 auto_discover）。

        Returns
        -------
        List[str]
            成功注册的 skill 名称列表。
        """
        classes = PluginManager.auto_discover(package)
        if not classes:
            return []

        registered: List[str] = []
        for cls in classes:
            try:
                instance = cls()
                self.register(instance)
                registered.append(instance.name)
            except ValueError as e:
                # 重复注册时抛出明确错误
                raise ValueError(
                    f"自动发现 Skill '{cls.__name__}' 时注册失败: {e}"
                ) from e
        return registered

    @staticmethod
    def discover_entry_points(group: str = "agent_teams_skills") -> List[Type[BaseSkill]]:
        """
        通过 importlib.metadata 读取已声明的 entry points 并加载 Skill 类。

        第三方 Skill 包可在 pyproject.toml 中声明：

        .. code-block:: toml

            [project.entry-points.agent_teams_skills]
            my_skill = "my_package.skills:MySkill"

        Parameters
        ----------
        group : str
            entry_points 组名，默认 "agent_teams_skills"。

        Returns
        -------
        List[Type[BaseSkill]]
            从 entry points 加载的所有 BaseSkill 子类列表。
        """
        discovered: List[Type[BaseSkill]] = []
        try:
            eps = importlib.metadata.entry_points()
            # Python 3.12+ 使用 select()；Python 3.11 及以下使用 dict-style get()
            try:
                skill_eps = eps.select(group=group)
            except AttributeError:  # pragma: no cover
                skill_eps = eps.get(group, [])
        except Exception:
            return discovered

        for ep in skill_eps:
            try:
                cls = ep.load()
                if inspect.isclass(cls) and issubclass(cls, BaseSkill) and not inspect.isabstract(cls):
                    discovered.append(cls)
            except Exception:  # pragma: no cover
                # entry point 加载失败，静默跳过
                continue

        return discovered
