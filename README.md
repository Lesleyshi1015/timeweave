<!-- @agent: session-260808-fleet-spruce | module: memory-palace-goai-skeleton | ts: 2026-08-08T17:00+08:00 -->

# memory-palace-goai

**Memory Palace × GOAI 赛道一（新智基座 | AgentInfra）业务层**

7 个 Agent + 6 个 Skill + mp_api 桥接层，基于 [agent-teams-sdk](F:\agent-teams-sdk) 框架（TeamRoom 黑板模式）。

## 仓库定位

```
F:\agent-teams-sdk        通用框架（两项目共用，可开源）
F:\memory-palace-goai     本仓库：MP 业务层（本仓库独享）
F:\selfbrain-goai         SelfBrain 业务层（SelfBrain 独享）
```

- **开源部分**（本仓库）：Agent 调用逻辑、Skill Schema + Wrapper、API 契约、Demo
- **闭源部分**：Memory Palace 核心引擎（主项目 `F:\memory-palace-v3.0\src`，黑盒保护）

## 安装

```bash
pip install -e F:\agent-teams-sdk     # 先装框架
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
