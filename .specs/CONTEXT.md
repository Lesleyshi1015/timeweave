<!-- @agent: session-260808-fleet-spruce | module: memory-palace-goai-skeleton | ts: 2026-08-08T17:00+08:00 -->

# CONTEXT — memory-palace-goai 项目上下文

> I-intel-scan · 2026-08-08 · 仓库创建时

## 项目一句话

Memory Palace 的 GOAI 赛道一业务层：7 Agents + 6 Skills + mp_api，基于 agent-teams-sdk 框架（黑板模式）。

## 仓库结构

```
memory_palace_goai/
├── mp_api/      # MPService 契约 + StubEngine + Engine 骨架（黑盒边界）
├── skills/      # 6 Skill（Schema+Wrapper 开源）
├── agents/      # 7 Agent（继承框架角色基类）
└── demo/        # 端到端闭环演示
```

## 依赖

- agent-teams-sdk（框架，F:\agent-teams-sdk，pip install -e）
- Memory Palace 主项目引擎（F:\memory-palace-v3.0\src，闭源，Engine 接入）

## 下一步

- B1/B2/B3 完成 → 验收 → 迁移代码到本仓库 → 真实引擎接入（8.10+）→ PPT 材料采集
