# AITP — AI Theoretical Physicist

> 追求真理而非沽名钓誉 · *Pursue truth, not fame.*

**AITP 是一个研究协议**——为 AI 理论物理学家设定纲领、研究规范和 harness 约束。当前仓库是协议在 Claude Code 等 agent 平台上的一种实现：在已有 agent 能力之上叠加一层强制执行层。未来协议可能有更高效的载体，但规范本身是持久的。

路线图：**Phase 1** (当前) — 正确性 harness，用硬拦截保证研究纪律。**Phase 2** — cron/openclaw 自主判断，更少讨论，更高可靠性。**Phase 3** — ideas-bubble 产生新研究方向，真正的 AI 理论物理学家。人的角色：审核 idea 的合理性与价值，把背后的物理搞懂，把推导做对。

---

## Why

Agent + Skill 已经能做不少事——告诉它协议规则，它会遵循。但仅靠 Skill 有几个根本问题：

**1. 没有强制力。** Skill 是文本注入。Agent 可以 Write 绕过 MCP 直接写文件，跳过推导声称结论，编造 source reference。Skill 说"请溯源"——Agent 不听的时候，Skill 拦不住。

**2. 没有状态持久化。** Chat 会话压缩后，Agent 忘了推导到哪一步。上下文窗口是易失的——你今天讨论的物理，明天可能被截断。人类博士后靠 lab notebook 解决这个问题，Agent 需要等价物。

**3. 没有可复现性。** 另一名物理学家能追溯你的工作吗？L0 的源 → L1 的提取 → L3 的推导步 → L4 的验证结果 → L2 的知识积累——这条链必须在文件系统里完整存在，不是藏在某次 chat 的上下文里。

**4. 没有对抗性审查。** Agent 对自己的推导有确认偏误。需要不同策略的审查者（代数、物理、数值、盲审 Skeptic）各自独立验证，分歧矩阵决定是否通过。

**5. 没有跨会话记忆。** 今天在 QSGW 课题里验证了一个 pitfall，明天开新课题时应该自动可查。L2 知识图让已验证的事实跨课题积累，而不是每次都从零开始。

AITP harness 解决这五个问题：

```
                  纯 Agent + Skill        Agent + AITP Harness
─────────────────────────────────────────────────────────────────
强制力           advisory 文本           硬拦截 (preflight + contracts + stage gate)
状态持久化      上下文窗口 (易失)        Markdown 文件系统 (永久)
可复现性        藏在 chat 历史里         L0→L1→L3→L4→L2 完整文件链
对抗性审查      无                       4-agent 独立审查 + 分歧矩阵 + Skeptic gate
跨会话记忆      每次从零开始              L2 知识图自动累积，新课题继承旧发现
crash 恢复      上下文丢失                session resume 恢复完整上下文
研究轨迹        chat log (不可查询)      research.md + runtime/log.md 自动追加
错误指引        "something went wrong"   "Step d1 缺 source_ref。aitp derive record --source ..."
```

Skill 告诉 Agent **应该怎么做**。Harness 保证 Agent **确实这么做了**——并且留下完整的、可审查的、跨会话的物证。

## What it does

```
你: "我想研究 GW 近似中 head-wing correction"
AITP: 创建课题 → 注册论文 → 拆解章节 → 记录推导 → 打包候选 → 
     SymPy 验证 / HPC 计算 → 4-agent 对抗审查 → 晋升到全局知识图
```

Every step is enforced — you can't submit a claim without derivation steps, can't promote without Skeptic review. State is plain Markdown files, never lost between sessions.

## Workflow

```
   L0: SOURCE ──→ L1: READ ──→ L3: DERIVE ──→ L4: VERIFY ──→ L2: MEMORY
     ↑ 发现        ↑ 拆解        ↑ 推导          │  审查          ↑  晋升
     │             │             │               │               │
     └─── retreat ──────────────┴───────────────┘               │
          任何阶段可退回 L0/L1 重新读源/修正推导                   │
```

```
           ┌─────────────────────────────────┐
           │          L4: VERIFY             │
           │                                 │
           │  Algebraic  │  逐步代数验证     │
           │  Physical   │  极限/对称性/守恒  │
           │  Numerical  │  HPC 输出校验     │
           │  Skeptic    │  盲审，只看结论   │
           │             ↓                   │
           │  分歧矩阵 → 判决 → promote/L3   │
           └─────────────────────────────────┘
```

**L3 ⇄ L4 是核心循环**：验证失败 → 退回 L3 修正 → 重新提交。最多 3 轮。任何阶段可 retreat 到 L0/L1 重新读源。

## Architecture

```
CLI 强制 ──── MCP 便利 ──── Skill 指导 ──── Hook 监视

  硬拦截          转发           文本注入         事后检测
```

| 层 | 位置 | 做什么 |
|----|------|--------|
| **CLI** | `brain/cli/` | 强制执行引擎。Preflight + Pydantic 合同 + state validator。唯一能改 topic 状态的路径。21 个命令 |
| **MCP** | `brain/mcp_server.py` | 给 Agent 用的便利层。参数解析 → dispatch 到 CLI。~55 个 tool |
| **Skill** | `skills/`, `deploy/skills/` | 告诉 Agent 协议规则、红线、常见用户短语→CLI 命令的映射 |
| **Hook** | `hooks/` | SessionStart 注入网关 skill。Stop 写 HUD 状态 + 日志 |

## AITP v5 kernel work

AITP v5 is the current typed-kernel implementation track. It keeps durable
research state in structured v5 records under `brain/v5/`; generated summaries,
adapter packets, README text, and external note pointers are orientation-only.
The v5 hook path exposes pre-commit/pre-tool/post-tool shell adapters, a shared
context-aware pre-tool policy surface, Codex hook bridge materialization, Claude
Code hook settings generation and safe settings merge installation, Claude
`PreToolUse` typed policy mapping for high-risk tool calls and trust-changing
AITP MCP calls, OpenCode plugin bridge materialization, and post-tool
trace-event persistence through CLI/MCP/runtime public surfaces.
For code-state provenance, validation, human-checkpoint request/decision,
promotion-packet creation/application, and L2 promotion MCP calls, Claude
`PreToolUse` resolves the active typed claim plus evidence and code-state refs,
then reuses kernel policy before the tool runs. Other adapters can call the same
contract through
`aitp-v5 policy pre-tool <args>` or `aitp_v5_evaluate_pre_tool_policy`; the
returned `pre_tool_policy_decision` is orientation/permission output only and
cannot update kernel state or claim trust. The same shared surface also blocks
`record_code_state`, `record_evidence`, `record_tool_run`, `execute_tool`, and
`ingest_subagent_result` attempts, plus validation-contract and
human-checkpoint request/decision and promotion-packet creation/application,
when their requested source is only a summary/task-plan/findings/progress
orientation surface. Generated
Codex/OpenCode bridge
payloads carry this shared entrypoint plus `runtime_gate_protocols` explicitly,
so adapter authors do not need to reconstruct code-state/evidence/checkpoint/
validation/promotion-packet sequencing from prose. Its `policy_reasons` list exposes machine-readable policy
IDs and severities, so reviewers do not need to parse free-form hook messages. Adapter
policy calls also carry `risk_level` and optional `human_checkpoint_id`; in
adversarial risk, trust-changing actions require an approved typed human
checkpoint before they can proceed. Adapter
packets and generated bridge files put `aitp_v5_evaluate_pre_tool_policy` into
the code-state/record-evidence/tool-run/execute-tool/subagent-ingestion,
validation-contract, human-checkpoint request/decision, promotion-packet
creation/application, validation, and promotion gate sequences, so runtimes can see that policy evaluation comes
before typed record creation, preflight, or promotion. The small
`brain.v5.adapter_runtime.evaluate_bridge_gate_pre_tool_policy` helper consumes
that generated gate metadata and delegates the actual decision back to typed
kernel records; `evaluate_bridge_lifecycle_event` is the adapter-neutral
pre-tool event wrapper over the same path. `evaluate_platform_pre_tool_event`
adds a thin Codex/OpenCode event normalizer for live-style pre-tool payloads,
then reuses the same typed decision path. Agents can invoke that normalizer
through `aitp-v5 adapter pre-tool-event <runtime> <session-id> ...` or
`aitp_v5_evaluate_adapter_pre_tool_event`; generated Codex/OpenCode bridges
advertise that event entrypoint alongside the lower-level policy entrypoint.
Those generated payloads and sidecars also advertise machine-readable
`pre_tool_policy_entrypoint.input_schema` and
`pre_tool_event_entrypoint.platform_event_schema`, including `risk_level`,
optional `human_checkpoint_id`, optional `checkpoint_id`, and optional nested
`packet` input, so adapters can discover required policy inputs without
treating Markdown or summaries as authority.
The bridge materializers also write a JSON sidecar next to the generated
Markdown and return its `payload_path`; hook runners should pass that sidecar to
`adapter pre-tool-event` with `--bridge-path` rather than scrape Markdown or
embed large JSON in a shell command. Generated bridges now include a
machine-readable `pre_tool_event_runner.argv` with the concrete runtime,
session id, `payload_path`, and `<platform-event-json>` placeholder for that
call. Hosts that provide hook events on stdin can use
`hooks/aitp_v5_adapter_event_runner.py pre-tool --base <workspace> --runtime <runtime> --session-id <session-id> --bridge-path <payload-path>`;
the script fills runtime/session/pre-tool defaults, validates the bridge runner,
and returns the same typed `pre_tool_policy_decision` payload and hook exit code.
The generated `pre_tool_event_runner.stdin_runner.argv` field advertises that
host-facing command directly in the bridge sidecar. Codex can also materialize a
native-ish hook fixture with
`aitp-v5 adapter install-hooks codex <session-id> --output .codex/AITP_V5_HOOKS.json`;
OpenCode has the matching plugin fixture at
`aitp-v5 adapter install-hooks opencode <session-id> --output .opencode/AITP_V5_PLUGIN_HOOKS.json`.
Both fixtures write the bridge and sidecar, then point pre-tool hooks at the
stdin runner with a declared repository `cwd`, without granting generated files
authority over typed records.
Trust-changing confidence updates use a request-bound preflight proof token:
`trust preflight`/`aitp_v5_preflight_trust_update` returns the token, and
`trust apply`/`aitp_v5_apply_trust_update` must carry the matching token before
typed claim state can change.

Current planning and review entry points:

- [AITP v5 goal instructions](docs/superpowers/plans/2026-05-20-aitp-v5-goal-instructions.md)
- [AITP v5 next-agent implementation plan](docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md)
- [AITP v5 hook installation templates](docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md)
- [AITP v5 implementation ledger](docs/superpowers/progress/2026-05-20-aitp-v5-implementation-ledger.md)

## Folder structure

```
AITP-Research-Protocol/
├── brain/
│   ├── cli/                  CLI 强制执行引擎
│   │   ├── state.py              原子写入、stage 转换 (advance/retreat)
│   │   ├── preflight.py          10 项注册检查、两速设计
│   │   ├── contracts.py          Pydantic 验证 (extra="forbid")
│   │   ├── decorators.py         @require_stage + @with_preflight
│   │   └── commands/             9 个命令模块 (21 个 CLI 命令)
│   ├── commands/              23 个策略文件 (YAML frontmatter)
│   ├── agents/                4 个审查 Agent 模板
│   └── mcp_server.py          MCP 服务器
├── hooks/                     SessionStart / Stop / 事件记录
├── skills/                    协议 skills (L0-L4 + domain)
├── deploy/                    安装部署源 (skills / hooks / config)
└── scripts/                   aitp CLI 入口 + 包管理器
```

**每个研究课题的文件树**（由 `aitp topic init` 创建）：

```
<topic-slug>/
├── state.md           课题状态 (stage, lane, gate, cycle...)
├── MEMORY.md          记录 (Steering, Decisions, Pitfalls)
├── research.md        自动追加的研究轨迹
├── compute/targets.yaml  HPC 目标配置
├── L0/sources/        注册的论文/代码
├── L1/intake/         提取的章节笔记 (按 source 嵌套)
├── L2/graph/          局部知识图 (promote 后→全局 L2)
├── L3/candidates/     候选声明
├── L4/reviews/        审查报告
├── L4/scripts/        Slurm 脚本
├── L4/outputs/        HPC 输出
├── L4/reports/        验证报告
└── notebook/          LaTeX 笔记
```

## Install

```bash
git clone git@github.com:bhjia-phys/AITP-Research-Protocol.git
cd AITP-Research-Protocol
AITP_TOPICS_ROOT=~/research/aitp-topics python scripts/aitp-pm.py install
```

After install, use `aitp` from anywhere:

```bash
aitp doctor          # 健康检查
aitp update          # 同步部署文件
aitp upgrade         # git pull + 重部署
```

## Quick start

```bash
# 1. 创建课题
aitp topic init gw-headwing --lane code_method

# 2. 绑定会话
aitp session resume gw-headwing

# 3. 注册论文
aitp source add gw-headwing --id hedin1965 --title "Hedin 1965" --type paper

# 4. 推进到阅读阶段
aitp state advance gw-headwing L1
aitp source parse-toc gw-headwing --source hedin1965 --sections "Intro, Eqs, GW"
aitp source extract gw-headwing --source hedin1965 --section "GW Approx" --content "..."

# 5. 推进到推导阶段
aitp state advance gw-headwing L3
aitp derive record gw-headwing --step D1 --source "hedin1965:Eq20" \
    --input "Sigma=iGW" --output "Sigma_head=..." --justification approximation

# 6. 打包提交
aitp derive pack gw-headwing --candidate-id v1
aitp candidate submit gw-headwing --candidate-id v1 --type research_claim \
    --claim "Head-wing correction modifies GW self-energy by..."

# 7. 形式化验证或数值计算
aitp sympy execute gw-headwing --candidate v1       # formal_theory lane
aitp compute prepare gw-headwing --candidate-id v1   # code_method lane

# 8. 对抗审查 → 晋升
aitp verify run gw-headwing --candidate v1
aitp verify results gw-headwing --candidate v1
aitp promote gw-headwing --candidate v1
```

每个命令都有 `--help`。完整的 21 个命令参考运行 `aitp --help`。

## Design principles

- **溯源优先** — 每个 claim 必须有 source_ref，每个 L2 node 必须有 provenance
- **人类拥有信任** — promotion gate 存在是因为 "AI 看起来很自信" 不是有效理由
- **文件即状态** — 纯 Markdown + YAML frontmatter，不依赖数据库、不丢失于会话
- **两速设计** — 探索时零阻力 (quick mode)，提交时硬拦截 (standard/full)
- **两条 lane** — `code_method` (HPC + domain invariants) 和 `formal_theory` (SymPy + analytic)，可在项目中切换
- **Agent 无关** — 任何能说 MCP 的 Agent 都能驱动协议

## License

MIT. See [LICENSE](LICENSE).
