# @agent: session-260808-vital-prairie | module: apps/memory_palace/demo | ts: 2026-08-08T17:00+08:00
"""
TimeWeave 端到端演示。

运行方式：
    python -m memory_palace_goai.demo.end_to_end

包含两个演示：
- run_query_demo(): 查询流程演示
- run_store_demo(): 存储流程演示
"""

from memory_palace_goai.demo.end_to_end import run_query_demo, run_store_demo

__all__ = ["run_query_demo", "run_store_demo"]
