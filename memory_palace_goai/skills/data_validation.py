# @agent: session-260808-golden-quasar | module: apps/memory_palace/skills/data_validation | ts: 2026-08-08T17:10+08:00
"""
Data Validation Skill（数据校验）

用途：
- 对黑板上的 L1/L2/L2.5/L3 结果进行 6 维数据质量核查
- 纯校验逻辑，不调用引擎，全部在本地执行

6 个校验维度：
1. 完整性（completeness）：检查各层结果是否包含必需字段
2. 时间戳一致性（timestamp_consistency）：检查时间戳格式和逻辑一致性
3. 实体一致性（entity_consistency）：检查实体 ID 在各层之间是否一致
4. 索引有效性（index_validity）：检查索引结果的状态字段
5. 时间线正确性（timeline_correctness）：检查时间线事件是否按时间排序
6. 文件完整性（file_integrity）：检查返回结构的完整性

开源部分：全部校验逻辑（本文件）
"""

from typing import Any, Dict, List

from agent_teams_sdk.skills.base_skill import BaseSkill


class DataValidation(BaseSkill):
    """
    数据校验 Skill — 对黑板数据进行 6 维质量核查。

    Attributes
    ----------
    name : str
        Skill 标识符："data-validation"
    version : str
        版本号："1.0.0"
    schema : dict
        输入/输出 JSON Schema
    """

    name = "data-validation"
    version = "1.0.0"
    schema = {
        "input": {
            "type": "object",
            "properties": {
                "l1_results": {
                    "type": ["array", "null"],
                    "items": {"type": "object"},
                    "description": "Layer 1 检索结果列表",
                },
                "l2_results": {
                    "type": ["array", "null"],
                    "items": {"type": "object"},
                    "description": "Layer 2 时间线结果列表",
                },
                "l2_5_results": {
                    "type": ["array", "null"],
                    "items": {"type": "object"},
                    "description": "Layer 2.5 图谱结果列表",
                },
                "l3_results": {
                    "type": ["array", "null"],
                    "items": {"type": "object"},
                    "description": "Layer 3 归档结果列表",
                },
                "entities": {
                    "type": ["array", "null"],
                    "items": {"type": "string"},
                    "description": "跨层共享的实体 ID 列表",
                },
            },
            "required": [],
        },
        "output": {
            "type": "object",
            "properties": {
                "validation_status": {
                    "type": "string",
                    "enum": ["passed", "failed"],
                },
                "errors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "dimension": {"type": "string"},
                            "message": {"type": "string"},
                        },
                    },
                },
                "details": {
                    "type": "object",
                    "properties": {
                        "completeness": {"type": "boolean"},
                        "timestamp_consistency": {"type": "boolean"},
                        "entity_consistency": {"type": "boolean"},
                        "index_validity": {"type": "boolean"},
                        "timeline_correctness": {"type": "boolean"},
                        "file_integrity": {"type": "boolean"},
                    },
                },
            },
            "required": ["validation_status", "errors"],
        },
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行 6 维数据校验。

        Parameters
        ----------
        l1_results : list | None
            Layer 1 检索结果
        l2_results : list | None
            Layer 2 时间线结果
        l2_5_results : list | None
            Layer 2.5 图谱结果
        l3_results : list | None
            Layer 3 归档结果
        entities : list | None
            跨层实体 ID 列表

        Returns
        -------
        dict
            {
                "validation_status": "passed" | "failed",
                "errors": [{"dimension": str, "message": str}, ...],
                "details": {各维度布尔结果}
            }
        """
        self.validate_input(**kwargs)

        l1_results: List[Dict] | None = kwargs.get("l1_results")
        l2_results: List[Dict] | None = kwargs.get("l2_results")
        l2_5_results: List[Dict] | None = kwargs.get("l2_5_results")
        l3_results: List[Dict] | None = kwargs.get("l3_results")
        entities: List[str] | None = kwargs.get("entities")

        errors: List[Dict[str, str]] = []
        details: Dict[str, bool] = {}

        # ── 维度 1：完整性 ──────────────────────────────────────────────
        completeness_ok = self._check_completeness(
            l1_results, l2_results, l2_5_results, l3_results, errors
        )
        details["completeness"] = completeness_ok

        # ── 维度 2：时间戳一致性 ────────────────────────────────────────
        timestamp_ok = self._check_timestamp_consistency(
            l1_results, l2_results, errors
        )
        details["timestamp_consistency"] = timestamp_ok

        # ── 维度 3：实体一致性 ──────────────────────────────────────────
        entity_ok = self._check_entity_consistency(
            l1_results, l2_5_results, entities, errors
        )
        details["entity_consistency"] = entity_ok

        # ── 维度 4：索引有效性 ──────────────────────────────────────────
        index_ok = self._check_index_validity(l1_results, l3_results, errors)
        details["index_validity"] = index_ok

        # ── 维度 5：时间线正确性 ────────────────────────────────────────
        timeline_ok = self._check_timeline_correctness(l2_results, errors)
        details["timeline_correctness"] = timeline_ok

        # ── 维度 6：文件完整性 ──────────────────────────────────────────
        file_ok = self._check_file_integrity(
            l1_results, l2_results, l2_5_results, l3_results, errors
        )
        details["file_integrity"] = file_ok

        validation_status = "passed" if not errors else "failed"

        return {
            "validation_status": validation_status,
            "errors": errors,
            "details": details,
        }

    # ──────────────────────────────────────────────────────────────────
    # 6 个校验维度的实现
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _check_completeness(
        l1: List[Dict] | None,
        l2: List[Dict] | None,
        l2_5: List[Dict] | None,
        l3: List[Dict] | None,
        errors: List[Dict[str, str]],
    ) -> bool:
        """
        维度 1：完整性检查。

        检查各层结果是否包含必需字段：
        - L1: memory_id, content
        - L2: memory_id, timestamp, event
        - L2.5: from, to, relation
        - L3: memory_id, content
        """
        ok = True

        if l1:
            for i, item in enumerate(l1):
                if not isinstance(item, dict):
                    errors.append({
                        "dimension": "completeness",
                        "message": f"L1 结果 #{i} 不是字典",
                    })
                    ok = False
                elif "memory_id" not in item:
                    errors.append({
                        "dimension": "completeness",
                        "message": f"L1 结果 #{i} 缺少 memory_id 字段",
                    })
                    ok = False

        if l2:
            for i, item in enumerate(l2):
                if not isinstance(item, dict):
                    ok = False
                    errors.append({
                        "dimension": "completeness",
                        "message": f"L2 结果 #{i} 不是字典",
                    })
                else:
                    for field in ("memory_id", "timestamp", "event"):
                        if field not in item:
                            errors.append({
                                "dimension": "completeness",
                                "message": f"L2 结果 #{i} 缺少 {field} 字段",
                            })
                            ok = False

        if l2_5:
            for i, item in enumerate(l2_5):
                if not isinstance(item, dict):
                    ok = False
                    errors.append({
                        "dimension": "completeness",
                        "message": f"L2.5 结果 #{i} 不是字典",
                    })
                else:
                    for field in ("from", "to", "relation"):
                        if field not in item:
                            errors.append({
                                "dimension": "completeness",
                                "message": f"L2.5 结果 #{i} 缺少 {field} 字段",
                            })
                            ok = False

        if l3:
            for i, item in enumerate(l3):
                if not isinstance(item, dict):
                    ok = False
                    errors.append({
                        "dimension": "completeness",
                        "message": f"L3 结果 #{i} 不是字典",
                    })
                elif "memory_id" not in item:
                    errors.append({
                        "dimension": "completeness",
                        "message": f"L3 结果 #{i} 缺少 memory_id 字段",
                    })
                    ok = False

        return ok

    @staticmethod
    def _check_timestamp_consistency(
        l1: List[Dict] | None,
        l2: List[Dict] | None,
        errors: List[Dict[str, str]],
    ) -> bool:
        """
        维度 2：时间戳一致性检查。

        检查时间戳是否为合法的 ISO 8601 格式字符串。
        """
        import re

        ok = True
        iso_pattern = re.compile(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
        )

        if l1:
            for i, item in enumerate(l1):
                ts = item.get("timestamp") if isinstance(item, dict) else None
                if ts and not iso_pattern.match(str(ts)):
                    errors.append({
                        "dimension": "timestamp_consistency",
                        "message": f"L1 #{i} 的时间戳格式不合法：{ts}",
                    })
                    ok = False

        if l2:
            for i, item in enumerate(l2):
                ts = item.get("timestamp") if isinstance(item, dict) else None
                if ts and not iso_pattern.match(str(ts)):
                    errors.append({
                        "dimension": "timestamp_consistency",
                        "message": f"L2 #{i} 的时间戳格式不合法：{ts}",
                    })
                    ok = False

        return ok

    @staticmethod
    def _check_entity_consistency(
        l1: List[Dict] | None,
        l2_5: List[Dict] | None,
        entities: List[str] | None,
        errors: List[Dict[str, str]],
    ) -> bool:
        """
        维度 3：实体一致性检查。

        检查 L2.5 图谱中的实体是否在提供的 entities 列表中存在。
        """
        ok = True

        if entities and l2_5:
            entity_set = set(entities)
            for i, item in enumerate(l2_5):
                if not isinstance(item, dict):
                    continue
                from_entity = item.get("from")
                to_entity = item.get("to")
                if from_entity and from_entity not in entity_set:
                    errors.append({
                        "dimension": "entity_consistency",
                        "message": f"L2.5 #{i} 的 from 实体「{from_entity}」不在 entities 列表中",
                    })
                    ok = False
                if to_entity and to_entity not in entity_set:
                    errors.append({
                        "dimension": "entity_consistency",
                        "message": f"L2.5 #{i} 的 to 实体「{to_entity}」不在 entities 列表中",
                    })
                    ok = False

        return ok

    @staticmethod
    def _check_index_validity(
        l1: List[Dict] | None,
        l3: List[Dict] | None,
        errors: List[Dict[str, str]],
    ) -> bool:
        """
        维度 4：索引有效性检查。

        检查 L1 和 L3 结果中的状态字段是否合法。
        """
        ok = True
        valid_statuses = {"indexed", "error", "archived", "read"}

        if l1:
            for i, item in enumerate(l1):
                if not isinstance(item, dict):
                    continue
                status = item.get("status")
                if status and status not in valid_statuses:
                    errors.append({
                        "dimension": "index_validity",
                        "message": f"L1 #{i} 的状态字段不合法：{status}",
                    })
                    ok = False

        if l3:
            for i, item in enumerate(l3):
                if not isinstance(item, dict):
                    continue
                status = item.get("status")
                if status and status not in valid_statuses:
                    errors.append({
                        "dimension": "index_validity",
                        "message": f"L3 #{i} 的状态字段不合法：{status}",
                    })
                    ok = False

        return ok

    @staticmethod
    def _check_timeline_correctness(
        l2: List[Dict] | None,
        errors: List[Dict[str, str]],
    ) -> bool:
        """
        维度 5：时间线正确性检查。

        检查时间线事件是否按时间戳升序排列。
        """
        ok = True

        if l2 and len(l2) > 1:
            timestamps = []
            for i, item in enumerate(l2):
                if not isinstance(item, dict):
                    continue
                ts = item.get("timestamp")
                if ts:
                    timestamps.append((i, str(ts)))

            for j in range(1, len(timestamps)):
                prev_idx, prev_ts = timestamps[j - 1]
                curr_idx, curr_ts = timestamps[j]
                if curr_ts < prev_ts:
                    errors.append({
                        "dimension": "timeline_correctness",
                        "message": (
                            f"时间线事件 #{prev_idx}（{prev_ts}）"
                            f" 晚于 #{curr_idx}（{curr_ts}），排序错误"
                        ),
                    })
                    ok = False

        return ok

    @staticmethod
    def _check_file_integrity(
        l1: List[Dict] | None,
        l2: List[Dict] | None,
        l2_5: List[Dict] | None,
        l3: List[Dict] | None,
        errors: List[Dict[str, str]],
    ) -> bool:
        """
        维度 6：文件完整性检查。

        检查返回结构是否为合法的列表/字典，无损坏数据。
        """
        ok = True

        for layer_name, layer_data in [
            ("L1", l1),
            ("L2", l2),
            ("L2.5", l2_5),
            ("L3", l3),
        ]:
            if layer_data is None:
                continue
            if not isinstance(layer_data, list):
                errors.append({
                    "dimension": "file_integrity",
                    "message": f"{layer_name} 结果不是列表类型",
                })
                ok = False
            else:
                for i, item in enumerate(layer_data):
                    if not isinstance(item, (dict, list, str, int, float, bool, type(None))):
                        errors.append({
                            "dimension": "file_integrity",
                            "message": f"{layer_name} 结果 #{i} 包含不支持的数据类型：{type(item).__name__}",
                        })
                        ok = False

        return ok
