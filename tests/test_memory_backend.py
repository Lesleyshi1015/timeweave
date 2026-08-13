# @agent: session-260808-fleet-spruce | module: test_memory_backend | ts: 2026-08-13T20:42+08:00
"""TimeWeaveBackend 热插拔接口测试（合并底座 MemoryBackend 契约）。"""
import pytest

from memory_palace_goai.memory_backend import TimeWeaveBackend


class TestTimeWeaveBackend:
    """TimeWeaveBackend 单元测试"""

    @pytest.fixture
    def backend(self):
        """默认 stub 引擎的后端"""
        return TimeWeaveBackend()

    def test_search_contract_structure(self, backend):
        """search 返回契约格式（query/results/memory_paths）"""
        out = backend.search("API 响应慢的根因", top_k=5)
        assert set(out.keys()) == {"query", "results", "memory_paths"}
        assert out["query"] == "API 响应慢的根因"
        assert isinstance(out["results"], list)
        assert isinstance(out["memory_paths"], list)

    def test_search_results_nonempty(self, backend):
        """stub 引擎返回至少 1 条结果"""
        out = backend.search("告警", top_k=5)
        assert len(out["results"]) >= 1
        r = out["results"][0]
        assert "id" in r and "title" in r and "score" in r

    def test_search_top_k_limit(self, backend):
        """results 数量受 top_k 限制"""
        out = backend.search("告警", top_k=2)
        assert len(out["results"]) <= 2

    def test_search_memory_paths_match_results(self, backend):
        """memory_paths 数量与 results 一致"""
        out = backend.search("数据库", top_k=3)
        assert len(out["memory_paths"]) == len(out["results"])
        assert all(p.startswith("L1/") for p in out["memory_paths"])

    def test_custom_engine_injected(self):
        """支持注入自定义引擎（可替换性演示）"""
        class FakeEngine:
            def layer1_search(self, query, top_k=10, context=None):
                return {"results": [{"id": "fake-1", "title": "假结果", "score": 0.9}]}

        backend = TimeWeaveBackend(engine=FakeEngine())
        out = backend.search("x")
        assert out["results"][0]["id"] == "fake-1"
        assert out["results"][0]["confidence"] == 0.9
