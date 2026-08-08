# @agent: session-260808-vital-prairie | module: apps/memory_palace/demo/end_to_end | ts: 2026-08-08T17:00+08:00
"""
Memory Palace 端到端演示脚本。

演示两个核心流程：
1. 查询流程：用户提问 → L1检索 → L2时间线 → L2.5图谱 → 返回答案
2. 存储流程：内容输入 → L3归档 → L2.5实体 → L2时间 → L1索引 → Validator核查

运行方式：
    python -m memory_palace_goai.demo.end_to_end
"""

import sys
from pathlib import Path

# 允许未安装时直接运行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from agent_teams_sdk import TeamRoom
from memory_palace_goai.agents import (
    MemoryCurator,
    L1Agent,
    L2Agent,
    L2_5Agent,
    L2_7Agent,
    L3Agent,
    MemoryValidator,
)


def _create_agents(task_id: str = "demo-001"):
    """创建所有 Agent 实例。"""
    room = TeamRoom(task_id)

    l1 = L1Agent(room)
    l2 = L2Agent(room)
    l2_5 = L2_5Agent(room)
    l2_7 = L2_7Agent(room)
    l3 = L3Agent(room)
    validator = MemoryValidator(room)

    workers = {
        "l1-agent": l1,
        "l2-agent": l2,
        "l2-5-agent": l2_5,
        "l2-7-agent": l2_7,
        "l3-agent": l3,
    }

    curator = MemoryCurator(room)

    return curator, workers, validator, room


def run_query_demo(query: str = "上周的告警根因"):
    """
    查询流程演示。

    模拟用户查询 "上周的告警根因"，展示完整的 L1→L2→L2.5 查询流程。
    打印每个步骤的执行痕迹和完整度变化。
    """
    print("=" * 60)
    print("Memory Palace 查询流程演示")
    print("=" * 60)
    print(f"用户查询: {query}")
    print("-" * 60)

    curator, workers, _, room = _create_agents("demo-query-001")

    # 执行查询流程
    result = curator.query(query, workers=workers)

    print("-" * 60)
    print("查询结果:")
    print(f"  完整度: {result['completeness']:.0%}")
    print(f"  执行层: {', '.join(result['layers_executed'])}")
    print()

    # 打印各层结果摘要
    blackboard = room.read_all()

    if "l1-agent_result" in blackboard:
        l1 = blackboard["l1-agent_result"]
        print(f"[L1 检索] {l1.get('summary', 'N/A')}")
        print(f"         置信度: {l1.get('confidence', 0):.0%}")
        print(f"         结果数: {len(l1.get('results', []))}")

    if "l2-agent_result" in blackboard:
        l2 = blackboard["l2-agent_result"]
        events = l2.get("timeline_events", [])
        print(f"[L2 时间线] {len(events)} 个事件")
        for e in events[:3]:
            print(f"           - {e.get('timestamp', 'N/A')}: {e.get('summary', 'N/A')[:40]}...")

    if "l2-5-agent_result" in blackboard:
        l2_5 = blackboard["l2-5-agent_result"]
        paths = l2_5.get("paths", [])
        root_cause = l2_5.get("root_cause")
        print(f"[L2.5 图谱] {len(paths)} 条关系路径")
        if root_cause:
            print(f"           根因: {root_cause}")

    print()
    print("=" * 60)
    print("查询流程演示完成")
    print("=" * 60)

    return result


def run_store_demo(content: str = "昨天告警: API 5xx升高"):
    """
    存储流程演示。

    模拟存储 "昨天告警: API 5xx升高"，展示完整的 L3→L2.5→L2→L1→Validator 流程。
    打印每个步骤的执行痕迹和 6 维核查结果。
    """
    print("=" * 60)
    print("Memory Palace 存储流程演示")
    print("=" * 60)
    print(f"存储内容: {content}")
    print("-" * 60)

    curator, workers, validator, room = _create_agents("demo-store-001")

    # 执行存储流程
    result = curator.store(content, workers=workers, validator=validator)

    print("-" * 60)
    print("存储结果:")
    print(f"  memory_id: {result.get('memory_id', 'N/A')}")
    print()

    # 打印各层结果
    blackboard = room.read_all()

    if "l3-agent_result" in blackboard:
        l3 = blackboard["l3-agent_result"]
        print(f"[L3 归档] memory_id={l3.get('memory_id', 'N/A')}")

    if "l2-5-agent_result" in blackboard:
        l2_5 = blackboard["l2-5-agent_result"]
        entities = l2_5.get("entity_ids", [])
        print(f"[L2.5 实体] {len(entities)} 个实体: {entities}")

    if "l2-agent_result" in blackboard:
        l2 = blackboard["l2-agent_result"]
        # 存储模式下 L2 可能没有 timeline_events
        mode = l2.get("mode", "N/A")
        print(f"[L2 时间] mode={mode}")

    if "l1-agent_result" in blackboard:
        l1 = blackboard["l1-agent_result"]
        print(f"[L1 索引] status={l1.get('status', 'N/A')}, memory_id={l1.get('memory_id', 'N/A')}")

    # 打印 6 维核查结果
    validator_result = blackboard.get("validator_result")
    if validator_result:
        print()
        print("[Validator 6 维核查]")
        print(f"  通过: {validator_result.get('passed', False)}")
        dimensions = validator_result.get("dimensions", {})
        for dim, passed in dimensions.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {dim}: {passed}")
        errors = validator_result.get("errors", [])
        if errors:
            print(f"  错误: {errors}")

    print()
    print("=" * 60)
    print("存储流程演示完成")
    print("=" * 60)

    return result


if __name__ == "__main__":
    # 运行查询演示
    run_query_demo("上周的告警根因")

    print("\n\n")

    # 运行存储演示
    run_store_demo("昨天告警: API 5xx升高")
