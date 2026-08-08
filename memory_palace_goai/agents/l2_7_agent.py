# @agent: session-260808-vital-prairie | module: apps/memory_palace/agents/l2_7_agent | ts: 2026-08-08T17:00+08:00
"""
L2.7 Agent — 时序预测层（Time Series Predict）

职责：
- 读取 L2 时间线事件序列
- 调用 TimeSeriesPredict Skill 预测未来趋势
- 将预测结果写入黑板 l2-7-agent_result
- 预留主动监控能力（autonomous_monitoring）
"""

from typing import Any, Dict, List

from agent_teams_sdk.roles.worker import WorkerAgent
from memory_palace_goai.skills.time_series_predict import TimeSeriesPredict


class L2_7Agent(WorkerAgent):
    """
    Layer 2.7 Worker — 时序预测 Agent。

    基于 L2 时间线事件序列预测未来趋势。
    预留主动监控能力，可定时触发预测。
    """

    def __init__(self, team_room):
        super().__init__("l2-7-agent", team_room)

    def do_work(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行时序预测工作。

        读取 L2 时间线 → 转换为事件序列 → TimeSeriesPredict.predict()
        """
        skill = TimeSeriesPredict()
        l2_result = self.team_room.read("l2-agent_result")

        if not l2_result:
            self._log("L2.7: L2 结果不存在，使用空序列预测")
            return self._predict(skill, [])

        # 将 L2 时间线事件转换为预测所需的事件序列格式
        event_series = self._convert_to_event_series(l2_result)
        return self._predict(skill, event_series)

    def _predict(self, skill: TimeSeriesPredict, event_series: List[dict]) -> Dict[str, Any]:
        """调用预测 Skill。"""
        # 如果事件序列为空，提供一个默认事件（stub 兼容）
        if not event_series:
            event_series = [{
                "timestamp": "2026-08-08T00:00:00Z",
                "metric": "default",
                "value": 0.0,
            }]
        result = skill.execute(event_series=event_series, horizon="24h")
        predictions = result.get("predictions", [])
        risk = result.get("risk_level", "unknown")
        self._log(f"L2.7 预测完成: {len(predictions)} 条预测, 风险等级={risk}")
        return result

    def _convert_to_event_series(self, l2_result: dict) -> List[dict]:
        """将 L2 时间线结果转换为事件序列格式。"""
        events = []
        timeline = l2_result.get("timeline_events", [])
        for event in timeline:
            if isinstance(event, dict):
                events.append({
                    "timestamp": event.get("timestamp", ""),
                    "metric": "event",
                    "value": 1.0,
                })
        return events

    def autonomous_monitoring(self) -> Dict[str, Any]:
        """
        主动监控逻辑（stub，预留扩展）。

        定时检查黑板上的事件序列，自动触发预测。
        当检测到异常模式时，主动通知 Curator。

        当前实现为 stub，返回空结果。
        """
        self._log("L2.7 主动监控触发（stub）")
        # TODO: 实现主动监控逻辑
        # 1. 定期检查黑板上的 timeline_events
        # 2. 检测异常模式（如错误率突增）
        # 3. 自动触发预测并通知 Curator
        return {
            "triggered": False,
            "reason": "autonomous_monitoring is a stub",
        }

    def _log(self, message: str) -> None:
        """内部日志。"""
        print(f"[{self.name}] {message}")
