# @agent: session-260808-vital-prairie | module: apps/memory_palace/agents/validator | ts: 2026-08-08T17:00+08:00
"""
Memory Validator — 数据验证层（Data Validation）

职责：
- 读取黑板全部结果
- 调用 DataValidation Skill 执行 6 维核查
- 将验证结果写入黑板 validator_result

6 维核查：
- completeness: 完整性
- timestamp_consistency: 时间戳一致性
- entity_consistency: 实体一致性
- index_validity: 索引有效性
- timeline_correctness: 时间线正确性
- file_integrity: 文件完整性
"""

from typing import Any, Dict, List, Optional

from agent_teams_sdk.roles.validator import ValidatorAgent, ValidationResult
from memory_palace_goai.skills.data_validation import DataValidation


class MemoryValidator(ValidatorAgent):
    """
    TimeWeave 验证器 — 6 维数据质量核查。

    在查询流程和存储流程的末尾执行验证，
    确保输出结果满足质量要求。
    """

    def __init__(self, team_room):
        super().__init__("validator", team_room)

    def validate(self, blackboard: Dict[str, Any]) -> ValidationResult:
        """
        执行 6 维数据验证。

        Parameters
        ----------
        blackboard : Dict[str, Any]
            黑板完整快照

        Returns
        -------
        ValidationResult
            验证结果，包含 passed、errors、warnings
        """
        skill = DataValidation()

        # 从黑板提取各层结果，转换为 skill 期望的格式
        l1_results = self._extract_results(blackboard, "l1-agent_result")
        l2_results = self._extract_results(blackboard, "l2-agent_result")
        l2_5_results = self._extract_results(blackboard, "l2-5-agent_result")
        l3_results = self._extract_results(blackboard, "l3-agent_result")
        entities = self._extract_entities(blackboard)

        result = skill.execute(
            l1_results=l1_results,
            l2_results=l2_results,
            l2_5_results=l2_5_results,
            l3_results=l3_results,
            entities=entities,
        )

        # 解析 skill 返回结果
        validation_status = result.get("validation_status", "failed")
        errors = self._format_errors(result.get("errors", []))
        warnings: List[str] = []
        passed = validation_status == "passed"

        self._log(
            f"验证完成: passed={passed}, "
            f"errors={len(errors)}, warnings={len(warnings)}"
        )

        return ValidationResult(
            passed=passed,
            errors=errors,
            warnings=warnings,
        )

    def _extract_results(
        self, blackboard: Dict[str, Any], key: str
    ) -> Optional[List[Dict]]:
        """从黑板结果中提取列表数据。"""
        raw = blackboard.get(key)
        if raw is None:
            return None

        # 不同层的结果结构不同，尝试提取列表
        if isinstance(raw, list):
            return raw

        if isinstance(raw, dict):
            # 尝试常见列表字段
            for field in ("results", "timeline_events", "paths", "entities"):
                if field in raw and isinstance(raw[field], list):
                    return raw[field]
            # 如果是 index/archive 结果，包装为列表
            if "memory_id" in raw or "status" in raw:
                return [raw]

        return None

    def _extract_entities(self, blackboard: Dict[str, Any]) -> Optional[List[str]]:
        """从 L2.5 结果中提取实体 ID 列表。"""
        l2_5 = blackboard.get("l2-5-agent_result")
        if not isinstance(l2_5, dict):
            return None

        # 从 entity_ids 字段提取
        entity_ids = l2_5.get("entity_ids", [])
        if entity_ids:
            return entity_ids

        # 从 paths 中提取 from/to 实体
        entities = set()
        for path in l2_5.get("paths", []):
            if isinstance(path, dict):
                if path.get("from"):
                    entities.add(path["from"])
                if path.get("to"):
                    entities.add(path["to"])
                if path.get("source"):
                    entities.add(path["source"])
                if path.get("target"):
                    entities.add(path["target"])

        return list(entities) if entities else None

    def _format_errors(
        self, raw_errors: List[Dict[str, str]]
    ) -> List[str]:
        """将 skill 错误格式转换为字符串列表。"""
        errors = []
        for err in raw_errors:
            if isinstance(err, dict):
                dim = err.get("dimension", "unknown")
                msg = err.get("message", "")
                errors.append(f"{dim}: {msg}")
            else:
                errors.append(str(err))
        return errors

    def _log(self, message: str) -> None:
        """内部日志。"""
        print(f"[{self.name}] {message}")
