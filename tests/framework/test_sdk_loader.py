# @agent: session-260808-young-raven | module: agent-teams-sdk-docs-tests | ts: 2026-08-08T16:43+08:00
"""SDKLoader 单元测试

覆盖：
- 文件不存在报错
- 不支持的扩展名报错
- .so 加载成功（mock ctypes.CDLL）
- .dll 加载成功（mock ctypes.WinDLL）
- call 方法转发调用
- is_loaded 状态
"""
from pathlib import Path
from unittest import mock

import pytest

from agent_teams_sdk.protection.sdk_loader import SDKLoader


# ─── 文件不存在 ───

class TestFileNotFound:
    """SDK 文件不存在场景"""

    def test_file_not_found_raises(self, tmp_path: Path):
        """文件不存在时抛出 FileNotFoundError"""
        p = tmp_path / "missing.so"
        with pytest.raises(FileNotFoundError, match="SDK not found"):
            SDKLoader(str(p))

    def test_file_not_found_with_dll(self, tmp_path: Path):
        """dll 文件不存在同样报错"""
        p = tmp_path / "missing.dll"
        with pytest.raises(FileNotFoundError, match="SDK not found"):
            SDKLoader(str(p))


# ─── 不支持的扩展名 ───

class TestUnsupportedExtension:
    """不支持的 SDK 后缀"""

    def test_unsupported_extension_py(self, tmp_path: Path):
        """.py 文件抛出 ValueError"""
        p = tmp_path / "sdk.py"
        p.write_text("pass", encoding="utf-8")
        with pytest.raises(ValueError, match="不支持的 SDK 后缀"):
            SDKLoader(str(p))

    def test_unsupported_extension_txt(self, tmp_path: Path):
        """.txt 文件抛出 ValueError"""
        p = tmp_path / "sdk.txt"
        p.write_text("hello", encoding="utf-8")
        with pytest.raises(ValueError, match="不支持的 SDK 后缀"):
            SDKLoader(str(p))


# ─── .so 加载 ───

class TestSoLoading:
    """.so 文件加载（mock ctypes）"""

    def test_so_load_success(self, tmp_path: Path):
        """.so 文件成功加载"""
        p = tmp_path / "libtest.so"
        p.write_bytes(b"\x7fELF")  # ELF magic

        with mock.patch("ctypes.CDLL") as mock_cdll:
            mock_lib = mock.MagicMock()
            mock_cdll.return_value = mock_lib

            loader = SDKLoader(str(p))

            mock_cdll.assert_called_once_with(str(p))
            assert loader.is_loaded() is True
            assert loader._lib is mock_lib

    def test_so_call_function(self, tmp_path: Path):
        """.so 加载后 call 方法转发调用"""
        p = tmp_path / "libtest.so"
        p.write_bytes(b"\x7fELF")

        with mock.patch("ctypes.CDLL") as mock_cdll:
            mock_lib = mock.MagicMock()
            mock_lib.my_func.return_value = 42
            mock_cdll.return_value = mock_lib

            loader = SDKLoader(str(p))
            result = loader.call("my_func", 1, 2)

            mock_lib.my_func.assert_called_once_with(1, 2)
            assert result == 42

    def test_so_call_missing_function(self, tmp_path: Path):
        """调用不存在的函数抛出 AttributeError"""
        p = tmp_path / "libtest.so"
        p.write_bytes(b"\x7fELF")

        with mock.patch("ctypes.CDLL") as mock_cdll:
            mock_lib = mock.MagicMock()
            del mock_lib.nonexistent  # 确保属性不存在
            mock_cdll.return_value = mock_lib

            loader = SDKLoader(str(p))
            with pytest.raises(AttributeError):
                loader.call("nonexistent")


# ─── .dll 加载 ───

class TestDllLoading:
    """.dll 文件加载（mock ctypes）"""

    def test_dll_load_success(self, tmp_path: Path):
        """.dll 文件成功加载"""
        p = tmp_path / "test.dll"
        p.write_bytes(b"MZ")  # PE magic

        with mock.patch("ctypes.WinDLL") as mock_windll:
            mock_lib = mock.MagicMock()
            mock_windll.return_value = mock_lib

            loader = SDKLoader(str(p))

            mock_windll.assert_called_once_with(str(p))
            assert loader.is_loaded() is True

    def test_dll_call_function(self, tmp_path: Path):
        """.dll 加载后 call 方法转发调用"""
        p = tmp_path / "test.dll"
        p.write_bytes(b"MZ")

        with mock.patch("ctypes.WinDLL") as mock_windll:
            mock_lib = mock.MagicMock()
            mock_lib.WinFunc.return_value = "win-result"
            mock_windll.return_value = mock_lib

            loader = SDKLoader(str(p))
            result = loader.call("WinFunc", "arg")

            mock_lib.WinFunc.assert_called_once_with("arg")
            assert result == "win-result"


# ─── Path 对象支持 ───

class TestPathSupport:
    """构造参数支持 Path 对象"""

    def test_path_object(self, tmp_path: Path):
        """Path 对象作为参数"""
        p = tmp_path / "libtest.so"
        p.write_bytes(b"\x7fELF")

        with mock.patch("ctypes.CDLL") as mock_cdll:
            mock_cdll.return_value = mock.MagicMock()
            loader = SDKLoader(p)
            assert loader.is_loaded()
