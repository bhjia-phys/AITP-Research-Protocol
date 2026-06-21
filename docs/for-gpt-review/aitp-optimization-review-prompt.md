# 给 GPT 的 AITP 优化审查任务

你是一位资深的 AI 系统架构师 + 科研工程方法论专家。下面是一份关于 **AITP(AI 研究协议)** 项目的现状诊断和优化计划,由另一个 AI(Claude/ZCode)基于实际代码阅读得出。你的任务是:**审查这份诊断是否准确、计划是否合理,并给出一个更好的优化规划。**

请用中文回答。

---

## 0. 关于 AITP(你需要知道的背景)

AITP 是一套为"理论物理研究"设计的 **AI 研究协议 + 运行时系统**。它的目标是:把一个 AI coding agent 变成一个**有纪律的理论物理研究协作者**——强制区分"已知 / 推导 / 猜测 / 投机",把每个研究步骤变成磁盘上可检查的 artifact,让可复用的知识必须通过显式验证才能"晋升"。

它用 Python 实现,存储是纯文件(`.aitp/` 目录下的 Markdown + YAML frontmatter,无数据库)。提供 ~60 个 MCP 工具给 agent 调用。

AITP 经历了 v4 → v5 的重构。**关键事实:正常研究写入路径已经从 v4 的 L0-L4 层级 pipeline 转向 v5 typed-record 图谱 + 信任状态机/门控。旧 L0-L4 文件和 legacy server 仍作为历史、迁移、审计、兼容层存在,但不应再被描述为当前主架构。** 部分文档和项目记忆还没有完全跟上这个转向,这是本次优化的一个导火索。

### 用户的三个核心诉求(这是优化的北极星)
1. **可追溯**:研究过程能完整重建(试过什么、为什么这个结论)。
2. **跨会话**:一个全新 AI 会话打开工作区,能直接拿到答案,不用重新推导。
3. **成败路线都明确**:失败路线(试过但失败的路径)和成功路线都要显式记录,让新会话直接知道"这条路死过,别再试;这条路通了"。

---

## 1. v5 的真实架构(基于代码核实,非文档)

| 维度 | v4(已废弃) | v5(实际) |
|---|---|---|
| 组织模型 | L0-L4 层级 pipeline | **typed-record 图谱**:约 30 个 record 族,通过 id 互链,append-only Markdown+YAML |
| 信任表达 | "在哪一层" | **claim.confidence_state 状态词表** + **TrustUpdate 状态迁移**(preflight token 门控)+ **ValidationContract/Result** + **PromotionPacket** |
| 门控 | 层级路由规则 | **gate_protocols.py**:每个 adapter action 带 `truth_source` / `summary_inputs_trusted` / `human_checkpoint_required` / `can_update_kernel_state` |
| 导航 | 隐含层间流转 | **session 绑定 + relation-map + execution brief**;冷启动支持 `topic:<id>` 虚拟 token |

### Record 族(节选)
`Topic` / `Session` / `Claim`(带 confidence_state)/ `Evidence` / `ToolRun` / `CodeState` / `Artifact` / `ValidationContract` / `ValidationResult` / `PromotionPacket` / `MemoryEntry`(L2 可信记忆)/ `ObjectRelation` / `ResearchRoute` / `ResearchRun` / `StrategyMemory` / `LifecycleEvent`(刚加的,记录 rehome/supersede)/ `HumanCheckpoint` / `FailureModeReviewResult`...

### 信任状态机的关键机制
- `ClaimRecord.confidence_state` 词表:核心 6 个(`hypothesis`/`coherent`/`unverified`/`partial`/`verified`/`open`)+ 特殊场景(`framing_only`/`legacy_seed`/`review_blocked`/`conditional_theorem_candidate`)
- `TrustUpdateRequest` → `TrustUpdateRecord`:带 `preflight_token`,要求 preflight 允许才应用;显式记录 `applied`/`preflight_allowed`/`status`
- 高风险 tool run 必须绑定 `ValidationContract`,记录 `ValidationResult`(passed/failed/partial)
- L2 记忆提升要走 `PromotionPacket`(打包 evidence + validation)
- 每个 adapter action 在 `gate_protocols.py` 声明 `truth_source`/`summary_inputs_trusted`/`human_checkpoint_required`

### 四个核心不变量(v4 v5 都坚守)
1. `context ≠ evidence`(背景不是证据)
2. `tool 执行 ≠ validation`(跑过不等于验证过)
3. `summary ≠ truth`(总结不是真相)
4. `claim 状态 ≠ proof`(claim 置信度不等于证明)

---

## 2. 诊断:强弱评估(基于代码)

### 强项(差异化护城河,不该动)
- **L0-L4 被换成状态机+门控,这比层级更精细**:不是"你在第几层",而是"这个具体动作的可信来源是什么、要不要人审、能不能改 kernel 状态"。
- **append-only + 强 provenance**:每条结论能追到 evidence → tool_run → code_state → 上游 commit。
- **信任是显式递进的**:L1→L2 promotion 要 packet + 过的 validation;trust update 要 preflight token。
- **刚补的 record lifecycle(rehome/supersede)**:记录能被安全地标记 misrouted/superseded/voided,不删文件,relation-map 按状态过滤。

### 弱项(对照三个诉求打分)

| 诉求 | 现状评分 | 核心问题 |
|---|---|---|
| 可追溯 | 7/10 | claim→evidence→tool_run→code_state 链路通;brief 聚合好。但要知道 id + 绑对 session 才能追 |
| 跨会话 | 6/10 | 已有 `topic:<id>` 虚拟 token 冷启动(不必先有 session)。但没"topic 级、跨所有 session 的当前结论"汇总 |
| 成败路线 | 3/10(最弱) | 成功路线还行;**失败路线基本散落** |

### 三个最具体的"断点"
1. **`ResearchRunRecord.terminal_answer_state`(含 `negative_or_inconclusive`)已经能被写入并出现在单个 research-run 记录/runtime 文件中,但没有被聚合进 topic 级"当前答案 / 死路 / 未决路线"surface。** 失败数据有记录,但新会话不能一眼读到。
2. **`StrategyMemoryRecord`(失败 lesson / next_time_rule)是 run-local JSONL,`load_strategy_memory(..., limit=8)`会把最近 active 项暴露到 execution brief / topic status,但它不是 typed registry 记录,也没有跨 topic / 跨 run 的 dead-end 查询和提升路径。** 所以问题不是"完全读不出",而是"读端太局部、太近因、不可系统查询"。
3. **L2 `Pitfall` / `negative_result` 的实现状态容易误读。** legacy L2 文档和老 MCP server 里有这些角色/索引,但 active v5 的 `PromotionPacket`→`MemoryEntry` 路径还没有把失败路线、pitfall、negative result 变成一等的 typed 查询面。换句话说:概念和遗留实现存在,但 v5 主路径的读端还没闭环。
4. **文档 drift**:`AITP_SPEC.md` 还是整份 v4 文档(标着 v4,讲 L0-L4);`PROJECT_MEMORY.md` 开头和 Protocol Layer Map 仍把 L0-L4 写成主架构。README 已经更接近 v5 现实,但 spec / project memory 的入口叙事仍会误导新 agent。

### 结构性观察
AITP 的强项和弱项是**同一个设计取向的两面**:几乎全部精力放在"如何确保每条记录可信"(写入端+校验端),很少放在"如何让人/新会话快速得到结论"(读取端+导航端)。它像一个设计精良、每条记录都带详细元数据的数据库,但缺好的视图层和查询接口。**数据都在、质量高,但"问出答案"很费劲。**

---

## 3. 已经完成的优化(供你了解上下文)

1. **record lifecycle(rehome/supersede/audit-routing)**:已实现+合并+代码审查+对真实数据跑了 3 条误路由 Si claim 的修复。新增 `LifecycleEventRecord` 族 + 4 个可选 frontmatter 字段(lifecycle_status/rehome_event_id/rehome_target_topic/replaced_by)+ relation-map 四区过滤(active/historical/misrouted/cross_topic_references)+ 4 个 CLI + 4 个 MCP 工具。25 个测试全过。

---

## 4. 待做的优化计划(请你审查并改进)

### 计划 A:修文档 drift(低风险,马上做)
- **新建 `docs/AITP_SPEC_v5.md`**:写真实架构(图谱+状态机+门控),保留一段 v4→v5 变更说明。精炼版(~200-300 行),结构:S1 身份 / S2 三阶段路线图(替代 L0-L4 作为主路径)/ S3 架构模型(替代 Layer Model)/ S4 四个核心区分 / S5 存储 / S6 人类在环。
- **`AITP_SPEC.md`(v4)顶部加 superseded 横幅**,正文不动(留历史)。
- **`PROJECT_MEMORY.md` 定点清理会误导主架构理解的 L0-L4 引用**:把 L0-L4 当当前核心架构的(如 "AITP protocol (L0-L4 layers)"、Gate model、Protocol Layer Map)改成图谱+状态机;"L2 memory"、legacy migration、historical L0/L1/L3/L4 这类语义/兼容引用保留。

### 计划 B(研究图谱改进,R1-R7,按优先级)

- **R1(已完成)**:对真实数据跑 rehome。
- **R2(高)**:加 `aitp_v5_write_topic_state_of_the_art(topic_id)`(无需 session),复用/补强现有 topic status 思路,但以 topic 为入口聚合 `ResearchRunRecord.terminal_answer_state`、`stop_reason`、`StrategyMemoryRecord`、relation-map 结论和 lifecycle 状态,输出 `current_best_answer` + `dead_ends`(每个带 stop_reason/lesson/next_time_rule/replaced_by)+ `open_runs`,写 `topics/<topic>/runtime/state_of_the_art.{json,md}`,挂到 SessionStart。
- **R3(高,但要拆小)**:先做 `aitp_v5_list_dead_ends(topic_id?)` / derived dead-end index,从现有 research-run + strategy-memory + lifecycle 记录派生,不要一开始就把所有失败 lesson 提升为 L2 memory。第二步再评估是否把 `StrategyMemoryRecord` 升级为 `registry/strategy_memory/` typed family,以及是否通过 `PromotionPacket`→`MemoryEntry` 只提升"可复用、经审查"的 Pitfall / negative_result。
- **R4(中)**:给 `EvidenceRecord`/`ToolRunRecord` 加封闭词表 `outcome_disposition`(`attempted_passed`/`attempted_failed_runtime`/`attempted_failed_physics`/`attempted_inconclusive`/`superseded_by:<id>`/`misrouted`),让 relation-map 的失败桶分 deterministic 而非靠正则启发式。
- **R5(中)**:session 结束自动持久化 goal-continuation,和 R2 的 current_best_answer 对账,若 active_claim 已被 rehome/supersede 则警告 stale_resume_target。
- **R6(中,可作为 R2 前置或并入 R2)**:加 `build_topic_relation_map(ws, topic_id)`,解析 topic 当前最佳 active claim,委托现有逻辑,去掉"必须先绑 session"的冷启动摩擦。
- **R7(低)**:TopicRecord 加 `last_activity_at`/`superseded_by_topic`/`abandonment_reason` + `aitp_v5_audit_topic_lifecycle`,标记废弃 topic。

---

## 5. 给 GPT 的具体任务

请你做以下几件事,**基于上面的信息,不需要访问代码库**(但如果你认为关键信息缺失,请指出):

### 任务 1:诊断审查
- 我对 v5 架构的理解(图谱+状态机+门控)是否准确?有没有我漏掉或误判的?
- 强弱评估的打分(7/6/3)你认同吗?哪个该调整?
- "写入端强、读取端弱"这个结构性观察,你认为是抓住了本质,还是片面?

### 任务 2:计划审查与改进
- 计划 A(修文档 drift)的做法合理吗?新建 v5 spec vs 原地改 v4,哪个更好?有没有更轻量的方案?
- R1-R7 的优先级排序你认同吗?有没有该提前或该砍掉的?
- 有没有我**完全没提到**但更重要的优化方向?(比如:图谱的查询/索引层、agent 如何消费这些数据、跨工作区/跨项目的知识迁移、记忆的衰减与去重、时间感知的可信度衰减、失败路线的"为什么失败"的结构化表达...)
- 特别关注**"成败路线明确"这个最弱项(3/10)**:你认为最有效、最小成本的改进是什么?R3(提升 strategy memory + 实现 L2 Pitfall)是正解吗,还是有更聪明的办法?

### 任务 3:给一个更好的优化规划
基于你的审查,**重新给一个优化规划**:
- 按你重新排的优先级,分阶段(立即做 / 短期 / 中期)
- 每个改动:解决什么问题、改哪个 record/surface、预估工作量(S/M/L)、风险
- 明确指出:哪些是"高 ROI 必做",哪些是"锦上添花",哪些是"看起来有用其实不该做"
- 如果你要重新设计 AITP 的"读端/查询/导航层",你会怎么设计?(这是当前最大短板)

### 输出格式
1. 诊断审查(逐条,赞同/反对 + 理由)
2. 计划审查(逐条)
3. 你没提到但我认为重要的方向
4. 重新优化规划(分阶段表格 + 读端/导航层设计)

请直言不讳。如果你认为我的某个判断是错的,明确说"这是错的",并给理由。不要为了配合我而附和。

---

## 附:关键约束(优化必须遵守)

- **不能动信任底座**:四个核心不变量(context≠evidence 等)、trust update preflight、validation contract 绑定、append-only provenance——这些是护城河,优化只能在读端/聚合层加东西,不能削弱写入端的纪律。
- **存储保持纯文件**:Markdown+YAML,无数据库。任何新机制必须能用文件表达。
- **向后兼容**:老记录(没新字段)必须继续可读。新增字段一律 optional with defaults。
- **Python 实现**:不换语言(不考虑改 TS)。
- **agent 通过 MCP 工具消费**:优化产物最好是新的 MCP surface 或增强现有 surface,而不是要求 agent 自己写复杂查询。
