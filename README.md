<!-- @agent: session-260808-fleet-spruce | module: memory-palace-goai-skeleton | ts: 2026-08-08T17:00+08:00 -->
<!-- @agent: session-260813-keen-orbit | module: README提交说明 | ts: 2026-08-13T18:30+08:00 -->

# TimeWeave 织时（memory-palace-goai）

> 品牌名：TimeWeave 织时（编织你的记忆，预见你的未来）

**Memory Palace × GOAI 赛道一（新智基座 | AgentInfra）业务层**

7 个 Agent + 6 个 Skill + mp_api 桥接层，基于 [agent-teams-sdk](F:\agent-teams-sdk) 框架（TeamRoom 黑板模式）。

## 仓库定位

```
agent-teams-sdk        通用框架（两项目共用，可开源）
memory-palace-goai     本仓库：MP 业务层（本仓库独享）
selfbrain-goai         SelfBrain 业务层（SelfBrain 独享）
```

- **开源部分**（本仓库）：Agent 调用逻辑、Skill Schema + Wrapper、API 契约、Demo
- **闭源部分**：Memory Palace 核心引擎（主项目，黑盒保护）

## 安装

```bash
pip install -e ../agent-teams-sdk     # 先装框架（或从 PyPI）
pip install -e .                      # 本仓库
```

## 运行 Demo

```bash
python -m memory_palace_goai.demo.end_to_end
```

演示两个完整闭环（stub 引擎）：
1. **查询闭环**：Curator 发布 → L1 检索 → 完整度评估 → L2 时序 → L2.5 图谱 → 主动重建
2. **存储闭环**：L3 归档 → L2.5 提取实体 → L2 提取时间 → L1 建索引 → Validator 6 维核查

## 结构

```
memory_palace_goai/
├── mp_api/      # 引擎桥接（MPService 契约 + StubEngine + Engine 骨架）
├── skills/      # 6 个 Skill（hybrid-search / temporal-mapping / entity-graph / time-series-predict / archive-compression / data-validation）
├── agents/      # 7 个 Agent（MemoryCurator + L1/L2/L2.5/L2.7/L3/Validator）
└── demo/        # 端到端演示
```

## 黑盒边界

- Skill Wrapper 只调用 `mp_api`（开源接口）
- 引擎实现（HNSW/BM25/RRF/压缩算法）在主项目闭源 SDK，通过 `Engine` 接入（`MP_ENGINE_PATH` 配置）

## GOAI 初赛提交说明

> 提交日期：2026-08-16 | 赛道：GOAI 赛道一（新智基座 | AgentInfra）

### 运行入口

```bash
# 安装
pip install -e ../agent-teams-sdk   # 先装框架
pip install -e .

# 运行 Demo（stub 引擎，无需闭源 SDK）
python -m memory_palace_goai.demo.end_to_end

# 运行全部测试
pytest
```

### 依赖

- Python 3.10+
- 内置 agent_teams_sdk 框架（本仓库包含）
- 标准库（json, logging, datetime 等）

### 样例输入输出

**查询闭环（摘录）：**
```
[Curator] 发布查询: 分析用户最近的销售对话
[L1-Search] 检索到 3 条相关记录
[L2-Temporal] 提取时间实体: 2026-08-10, 2026-08-12
[L2.5-Graph] 构建实体关系图: {用户→对话→销售}
[Curator] 完整度评估: 0.85 → 触发 L2 时序预测
[Curator] 重建结果: {趋势: 上升, 置信度: 0.9}
```

**存储闭环（摘录）：**
```
[L3-Archive] 归档对话记录 batch_id=20260813
[L2.5-Graph] 提取实体: ["Alice", "产品A", "订单#1234"]
[L2-Temporal] 提取时间: 2026-08-13T14:30:00
[L1-Index] 建立索引: entity→doc_id 映射
[Validator] 6维核查: 完整性✓ 一致性✓ 时效性✓ 准确性✓ 去重✓ 合规✓
```

### 运行证据

```
pytest
# 102 passed
```

**评测引用（来自 Memory Palace 主项目，非本仓库）：**
- LoCoMo Hit@3: **89.58%**
- LongMemEval: **84.8%**

> 注：以上评测在 Memory Palace 主项目（`memory-palace-v3.0`）完成，使用完整引擎。本仓库为 AgentTeams 协同层，通过 `mp_api` 桥接主项目引擎。

### 黑盒说明

本仓库**不包含** Memory Palace 核心引擎（HNSW 索引、BM25 检索、RRF 融合、压缩算法等）。核心引擎位于主项目（闭源），通过以下方式桥接：

1. **Stub 引擎**（`mp_api/stub_engine.py`）：Demo 和测试使用，无需闭源 SDK
2. **真实引擎**（`MP_ENGINE_PATH` 配置）：生产环境加载主项目 `.so`/`.dll`

评审运行 Demo 和测试无需闭源引擎，全部 102 个测试均基于 stub 引擎通过。
