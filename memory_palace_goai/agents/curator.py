# @agent: session-260808-vital-prairie | module: apps/memory_palace/agents/curator | ts: 2026-08-08T17:00+08:00
"""
Memory Curator — 记忆管理调度器

职责：
- 发布任务给 Worker Agents（轮番喊人）
- 评估黑板完整度
- 主动重建结果
- 唯一对接用户的 Agent

查询流程：L1 → 评估 → L2 → 评估 → L2.5 → 重建返回
存储流程：L3 → L2.5 → L2 → L1 → Validator
"""

from typing import Any, Dict, List, Optional

from agent_teams_sdk.roles.curator import CuratorAgent
from agent_teams_sdk.roles.worker import WorkerAgent
from agent_teams_sdk.roles.validator import ValidatorAgent, ValidationResult


class MemoryCurator(CuratorAgent):
    """
    Memory Palace Curator — 记忆管理调度器。

    管理 5 个 Worker Agent（L1/L2/L2.5/L2.7/L3）和 1 个 Validator，
    实现查询和存储两种核心流程。

    Attributes
    ----------
    workers : List[str]
        Worker 名称列表
    completeness_thresholds : Dict[str, float]
        各层完整度阈值（递增：L1=0.7, L2=0.85, L2.5=0.95）
    """

    def __init__(
        self,
        team_room,
        workers: Optional[List[str]] = None,
        completeness_thresholds: Optional[Dict[str, float]] = None,
    ):
        if workers is None:
            workers = [
                "l1-agent",
                "l2-agent",
                "l2-5-agent",
                "l2-7-agent",
                "l3-agent",
            ]
        super().__init__("memory-curator", team_room, workers)

        # 完整度阈值（递增）
        self.completeness_thresholds = completeness_thresholds or {
            "l1-agent": 0.70,
            "l2-agent": 0.85,
            "l2-5-agent": 0.95,
            "l2-7-agent": 1.00,
        }

    def evaluate_completeness(self, blackboard: Dict[str, Any]) -> float:
        """
        评估黑板完整度。

        根据各层 Worker 结果的可用性计算完整度分数：
        - 仅 L1: 0.70
        - L1 + L2: 0.85
        - L1 + L2 + L2.5: 0.95
        - 全部（含 L2.7）: 1.00
        """
        score = 0.0

        if blackboard.get("l1-agent_result"):
            score = 0.70

        if blackboard.get("l2-agent_result"):
            score = 0.85

        if blackboard.get("l2-5-agent_result"):
            score = 0.95

        if blackboard.get("l2-7-agent_result"):
            score = 1.00

        return score

    def query(
        self,
        user_query: str,
        workers: Optional[Dict[str, WorkerAgent]] = None,
    ) -> Dict[str, Any]:
        """
        完整查询流程。

        流程：L1 → 评估 → L2 → 评估 → L2.5 → 重建返回

        Parameters
        ----------
        user_query : str
            用户查询字符串
        workers : Dict[str, WorkerAgent], optional
            Worker Agent 实例映射（stub 模式使用）

        Returns
        -------
        Dict[str, Any]
            重建后的查询结果
        """
        self._log(f"开始查询流程: {user_query}")

        # 1. 写入用户查询到黑板
        self.team_room.write("user_query", user_query, updated_by=self.name)

        # 2. Layer 1: 混合检索
        self.dispatch_task("l1-agent", f"@l1-agent 请检索: {user_query}")
        self._trigger_worker("l1-agent", workers)

        completeness = self.evaluate_completeness(self.team_room.read_all())
        self.team_room.write("completeness", completeness, updated_by=self.name)
        self._log(f"L1 完成后完整度: {completeness:.0%}")

        # 3. Layer 2: 时间映射（如果完整度不够）
        if completeness < self.completeness_thresholds.get("l2-agent", 0.85):
            self.dispatch_task("l2-agent", "@l2-agent 请构建时间线")
            self._trigger_worker("l2-agent", workers)

            completeness = self.evaluate_completeness(self.team_room.read_all())
            self.team_room.write("completeness", completeness, updated_by=self.name)
            self._log(f"L2 完成后完整度: {completeness:.0%}")

        # 4. Layer 2.5: 实体图谱（如果完整度仍不够）
        if completeness < self.completeness_thresholds.get("l2-5-agent", 0.95):
            self.dispatch_task("l2-5-agent", "@l2-5-agent 请构建实体图谱")
            self._trigger_worker("l2-5-agent", workers)

            completeness = self.evaluate_completeness(self.team_room.read_all())
            self.team_room.write("completeness", completeness, updated_by=self.name)
            self._log(f"L2.5 完成后完整度: {completeness:.0%}")

        # 5. 重建结果
        result = self.reconstruct_result(self.team_room.read_all())
        self._log(f"查询流程完成，完整度: {completeness:.0%}")

        return {
            "answer": result,
            "completeness": completeness,
            "layers_executed": self._get_executed_layers(),
        }

    def store(
        self,
        content: str,
        workers: Optional[Dict[str, WorkerAgent]] = None,
        validator: Optional[ValidatorAgent] = None,
    ) -> Dict[str, Any]:
        """
        完整存储流程。

        流程：L3 → L2.5 → L2 → L1 → Validator

        Parameters
        ----------
        content : str
            待存储的内容
        workers : Dict[str, WorkerAgent], optional
            Worker Agent 实例映射（stub 模式使用）
        validator : ValidatorAgent, optional
            Validator Agent 实例（stub 模式使用）

        Returns
        -------
        Dict[str, Any]
            存储结果，包含 memory_id 和验证结果
        """
        self._log("开始存储流程")

        # 1. 写入存储内容到黑板
        self.team_room.write("store_content", content, updated_by=self.name)

        # 2. Layer 3: 归档压缩
        self.dispatch_task("l3-agent", "@l3-agent 请归档")
        self._trigger_worker("l3-agent", workers)

        # 3. Layer 2.5: 实体提取
        self.dispatch_task("l2-5-agent", "@l2-5-agent 请提取实体")
        self._trigger_worker("l2-5-agent", workers)

        # 4. Layer 2: 时间提取
        self.dispatch_task("l2-agent", "@l2-agent 请提取时间信息")
        self._trigger_worker("l2-agent", workers)

        # 5. Layer 1: 索引写入
        self.dispatch_task("l1-agent", "@l1-agent 请建立索引")
        self._trigger_worker("l1-agent", workers)

        # 6. Validator: 6 维核查
        if validator:
            self.dispatch_task("validator", "@validator 请验证")
            validator_result = validator.execute({"action": "validate"})
            self._log(f"验证结果: passed={validator_result.passed}")
        else:
            validator_result = None

        # 收集结果
        result = self.reconstruct_result(self.team_room.read_all())
        self._log("存储流程完成")

        l3_result = self.team_room.read("l3-agent_result")
        memory_id = l3_result.get("memory_id") if isinstance(l3_result, dict) else None
        return {
            "memory_id": memory_id,
            "layers": result,
            "validation": validator_result,
        }

    def _trigger_worker(
        self,
        worker_name: str,
        workers: Optional[Dict[str, WorkerAgent]] = None,
    ) -> None:
        """
        触发 Worker 执行（stub 模式）。

        在真实异步系统中，Worker 会通过消息总线监听黑板。
        在 stub/demo 模式中，我们直接调用 Worker 的 on_message。
        """
        if workers and worker_name in workers:
            worker = workers[worker_name]
            worker.on_message(f"@{worker_name} 执行任务")

    def _get_executed_layers(self) -> List[str]:
        """获取已执行的层列表。"""
        executed = []
        blackboard = self.team_room.read_all()
        for layer in ["l1-agent", "l2-agent", "l2-5-agent", "l2-7-agent", "l3-agent"]:
            if blackboard.get(f"{layer}_result"):
                executed.append(layer)
        return executed

    def _log(self, message: str) -> None:
        """内部日志。"""
        print(f"[{self.name}] {message}")
