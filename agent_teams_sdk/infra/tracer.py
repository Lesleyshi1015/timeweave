# @agent: session-260808-vital-stag | module: infra/tracer | ts: 2026-08-08T16:37+08:00
# 设计依据：跨项目接口开发需求-MemoryPalace-SelfBrain.md §5.x + GOAI 可观测要求
from typing import Any, Dict, List
from datetime import datetime
from enum import Enum
import json
import threading
import uuid


class SpanType(str, Enum):
    """
    Span 类型枚举（GOAI 可观测要求：Agent/Skill/MCP/RAG/LLM 五类 Span）

    继承 str 以支持与字符串直接比较（向后兼容），
    继承 Enum 以提供类型约束与 IDE 自动补全。
    """
    AGENT = "agent"
    SKILL = "skill"
    MCP = "mcp"
    RAG = "rag"
    LLM = "llm"


class Tracer:
    """
    Tracer - 简易 Trace 记录（GOAI 可观测要求：Agent/Skill/MCP/RAG/LLM Span）

    - 每个任务一个 trace_id；每个调用一个 span（parent/child 关系）
    - 可扩展：后续对接 OpenTelemetry GenAI 标准或 AgentLoop
    """

    def __init__(self) -> None:
        self._spans: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def start_trace(self, name: str) -> str:
        trace_id = uuid.uuid4().hex[:16]
        with self._lock:
            self._spans.append({
                "trace_id": trace_id,
                "span_id": uuid.uuid4().hex[:12],
                "name": name,
                "type": "trace",
                "parent_span_id": None,
                "start": datetime.now().isoformat(),
                "end": None,
                "attrs": {},
            })
        return trace_id

    def start_span(self, trace_id: str, name: str, span_type: str | SpanType = "agent",
                   parent_span_id: str | None = None, attrs: Dict[str, Any] | None = None) -> str:
        """
        在指定 trace 下创建一个新 Span。

        Args:
            trace_id: 所属 trace 的 ID（由 start_trace 返回）
            name: Span 名称（如 "research_skill", "linear_mcp"）
            span_type: Span 类型，支持 SpanType 枚举或字符串。
                       默认值为 "agent"（向后兼容）。
                       非法值将抛出 ValueError。
            parent_span_id: 父 Span ID（可选，用于构建父子关系）
            attrs: 附加属性字典（可选）

        Returns:
            新 Span 的 span_id

        Raises:
            ValueError: 当 span_type 不是 SpanType 枚举值或合法字符串时
        """
        # 统一 span_type 为字符串并校验
        if isinstance(span_type, SpanType):
            type_str = span_type.value
        elif isinstance(span_type, str):
            valid_types = {t.value for t in SpanType}
            if span_type not in valid_types:
                raise ValueError(
                    f"非法 span_type: {span_type!r}。"
                    f"合法值: {sorted(valid_types)}"
                )
            type_str = span_type
        else:
            raise TypeError(
                f"span_type 必须为 str 或 SpanType，收到: {type(span_type).__name__}"
            )
        span_id = uuid.uuid4().hex[:12]
        with self._lock:
            self._spans.append({
                "trace_id": trace_id,
                "span_id": span_id,
                "name": name,
                "type": type_str,
                "parent_span_id": parent_span_id,
                "start": datetime.now().isoformat(),
                "end": None,
                "attrs": attrs or {},
            })
        return span_id

    def end_span(self, span_id: str, status: str = "ok", result: Any = None) -> None:
        with self._lock:
            for span in self._spans:
                if span["span_id"] == span_id:
                    span["end"] = datetime.now().isoformat()
                    span["status"] = status
                    if result is not None:
                        span["result"] = result
                    break

    def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [s for s in self._spans if s["trace_id"] == trace_id]

    def export(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._spans)

    def clear(self) -> None:
        with self._lock:
            self._spans.clear()

    def export_json(self, path: str) -> None:
        """
        将所有 spans 导出为 JSON 文件（UTF-8 编码）。

        Args:
            path: 输出文件的绝对或相对路径

        文件结构为包含所有 span 字典的 JSON 数组。
        """
        with self._lock:
            data = list(self._spans)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def to_otlp_exportable(self) -> List[Dict[str, Any]]:
        """
        将内部 spans 转换为符合 OpenTelemetry (OTel) 语义的结构（尽力而为）。

        Returns:
            转换后的 span 列表，每个元素包含 OTel 推荐字段：
            - trace_id (hex, 32字符，不足补零)
            - span_id (hex, 16字符，不足补零)
            - parent_span_id (hex 或 null)
            - name
            - kind (由 type 映射: AGENT→INTERNAL, SKILL→INTERNAL, MCP→CLIENT,
                    RAG→CLIENT, LLM→CLIENT)
            - start_time_unix_nano
            - end_time_unix_nano (可为 0，表示未结束)
            - status_code ("OK" / "ERROR" / "UNSET")
            - attributes (原始 attrs)

        迁移路径说明（TODO）：
            1. 引入 opentelemetry-sdk 后，将本方法替换为真正的 OTLP exporter
            2. 使用 opentelemetry.trace.get_tracer() 创建 Span，
               替代本模块的手动字典结构
            3. 通过 OTEL_EXPORTER_OTLP_ENDPOINT 配置，
               将 spans 推送至 Jaeger / Tempo / Honeycomb 等后端
            4. 参考 OpenTelemetry GenAI 语义约定（semconv）
               为 LLM/RAG spans 添加 llm.system, llm.request.model 等属性
        """
        kind_map = {
            SpanType.AGENT.value: "INTERNAL",
            SpanType.SKILL.value: "INTERNAL",
            SpanType.MCP.value: "CLIENT",
            SpanType.RAG.value: "CLIENT",
            SpanType.LLM.value: "CLIENT",
        }

        result: List[Dict[str, Any]] = []
        with self._lock:
            for span in self._spans:
                start_dt = datetime.fromisoformat(span["start"]) if span["start"] else None
                end_dt = datetime.fromisoformat(span["end"]) if span["end"] else None

                # status_code 映射
                status_raw = span.get("status", "")
                if status_raw == "ok":
                    status_code = "OK"
                elif status_raw == "error":
                    status_code = "ERROR"
                else:
                    status_code = "UNSET"

                result.append({
                    "trace_id": span["trace_id"].ljust(32, "0"),
                    "span_id": span["span_id"].ljust(16, "0"),
                    "parent_span_id": span["parent_span_id"].ljust(16, "0") if span["parent_span_id"] else None,
                    "name": span["name"],
                    "kind": kind_map.get(span["type"], "INTERNAL"),
                    "start_time_unix_nano": int(start_dt.timestamp() * 1e9) if start_dt else 0,
                    "end_time_unix_nano": int(end_dt.timestamp() * 1e9) if end_dt else 0,
                    "status_code": status_code,
                    "attributes": span.get("attrs", {}),
                })
        return result
