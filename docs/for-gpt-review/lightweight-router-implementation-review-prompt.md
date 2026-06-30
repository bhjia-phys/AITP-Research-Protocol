# 给 GPT 的 lightweight record router 实现审查任务

你是一位资深 AI 系统架构师 + 代码审查专家。下面是关于 **AITP v5 lightweight record router** 实现的完整信息,由另一个 AI(Zhipu)基于你之前给的实现规划(`aitp-lightweight-record-router-zhipu-plan.md`,见后文附录)逐条实现。你的任务是:**审查这次实现是否符合规划、有没有真正的缺陷,并给出明确的 APPROVE / REQUEST CHANGES / BLOCK 结论。**

请用中文回答。请直言不讳——如果某个判断是错的,明确说"这是错的"并给理由,不要为了配合而附和。

---

## 0. 背景:AITP 是什么

AITP 是一套为"理论物理研究"设计的 AI 研究协议 + 运行时系统,把 AI coding agent 变成有纪律的理论物理研究协作者。用 Python 实现,存储是纯文件(`.aitp/` 目录下的 Markdown + YAML frontmatter,无数据库),提供 ~60 个 MCP 工具给 agent。

**AITP 的核心纪律(四个不变量,任何优化都不能破坏):**
1. `context ≠ evidence`(背景不是证据)
2. `tool 执行 ≠ validation`(跑过不等于验证过)
3. `summary ≠ truth`(总结不是真相)
4. `claim 状态 ≠ proof`(claim 置信度不等于证明)

**关键事实:v5 已经抛弃了 v4 的 L0-L4 层级 pipeline 模型,换成了 typed-record 图谱 + 信任状态机/门控。**

---

## 1. 你(给 Zhipu)的原始规划要点(审查依据)

完整规划在附录,这里是关键约束:

### surface 定义
新增 `lightweight_record_write_plan` surface + MCP 工具 `aitp_v5_plan_lightweight_record_write` + CLI `aitp-v5 recording plan-lightweight-write`。

**核心定位:这个 surface 只生成计划(plan),绝不写记录、绝不推进 trust。** 默认只读 typed records 和输入事件,返回 plan-only payload。`execute_now` 本次必须恒为 `false`。

### 硬信任边界(必须全部满足)
- `can_update_claim_trust=false`(所有路径)
- `summary_inputs_trusted=false`
- `orientation_only=true`
- `can_update_kernel_state=false`
- relation map 只能用于定位/边界,不能当 evidence
- runtime failure 只能记录为运行/环境/工具失败,不能自动判为算法失败
- 旧图/旧口径不能自动当成新报告 evidence
- event_summary 提到 claim 不等于提升 confidence
- 一个 sensemaking_report 够用时不要拆成多条冗余 record

### 路由规则(§5)
- `decision=plan_write` 只在 6 种情况:durable artifact / claim 边界 / 旧新口径冲突 / open gap / negative result / 下一步义务
- `decision=no_write`:普通聊天、重复总结、临时推测、纯解释概念
- **不要因为出现 claim 名称就写入**

### 目标 claim 选择(§5.2)——保守
顺序:hint 是 claim id → hint 是 statement 片段(扫 sibling,多候选则 needs_human)→ active claim 与 event 匹配才用 → 不匹配则建议 sibling 或 needs_human → artifact-only 且 claim 不明时 needs_human(因为 ArtifactRecord 要求 claim_id 非空)

### record 类型选择(§5.3)——固定优先级
1. `artifact`(有文件/图/JSON/log/report/notebook;已有 canonical ref 则只作 ref 不重复 attach)
2. `sensemaking_report`(口径/边界/旧新冲突/runtime-vs-algorithm failure)
3. `proof_obligation`(open gap/validation gap/missing proof;用现有 ProofObligationRecord,obligation_type 用 `validation_gap`/`proof_gap` 等)
4. `evidence`(**只有**输入含 `tool_run:<id>` 或 `validation_result:<id>` 才规划;relation map/chat summary/runtime failure/old plot alone 都不能产 evidence)
5. `trust_preflight`(**只有**明确要求 trust/L2 promotion 才出现;只规划 preflight,不调 apply)

### 字段填充规范(§6)
- proof_obligation 的 `maturity_level`:规划原文写了 `"hypothesis"`,但加了警告"Before coding, inspect `brain/v5/research_state.py::MATURITY_LEVELS`. Do not invent a value that fails tests."
- evidence 的 `tool_run_ids`/`validation_result_ids` 在 optional_fields;`verification_refs` 对已有输入 ref 必须保留 canonical 形式(如 `tool_run:run-abc`),对未创建的用占位符 `evidence:<to-be-created>`
- sensemaking_report 当前 dataclass 无 `metadata` 字段——plan payload 可包含 metadata,但不要传给写入工具除非扩展 schema

### contract 要求(§8)
- `kind == "lightweight_record_write_plan"`
- `decision` ∈ {no_write, plan_write, needs_human_target_claim, unsupported}
- `trust_boundary.can_update_claim_trust is False`
- 顶层 `summary_inputs_trusted is False` / `orientation_only is True` / `can_update_kernel_state is False` / `can_update_claim_trust is False`
- no_write → typed_write_plan 空 + no_write_reason 非空
- plan_write → target_claim.target_claim_id 非空 + selected_record_types 非空 + typed_write_plan 非空
- 每个 plan item 有:record_type / target_claim_id / summary / required_fields / verification_refs / recommended_mcp_tool / execute_now==False

### 常见错误(§12,实现必须避免)
- 不要在 planner 内调 record_sensemaking_report/attach_artifact/record_evidence/create_proof_obligation
- 不要加新数据库/索引守护
- 不要把 validation_gap 做成新 record family
- 不要让 relation-map 输出当 source/evidence ref
- 不要用 prose/文件路径填 evidence_refs
- 不要把 plan-only metadata 传给不支持它的写入工具
- 不要把所有 negative result 提升到 L2
- 不要改 ClaimRecord.confidence_state
- 不要调 aitp_v5_apply_trust_update

### 验收标准(§10)
- 新 public surface 通过 require_valid_public_surface 验证
- MCP 工具被 native MCP 列出
- CLI 返回与 MCP 相同 payload 形状
- 规划 surface 不写任何 typed record
- 不暴露 trust apply 路径
- 不从 relation map/chat summary/runtime failure/old plot alone 产 evidence
- artifact path alone 只产 artifact plan,不产 evidence
- open gap 产 proof obligation plan
- claim 不匹配时不默认用 active claim
- plan 最小:sensemaking 够用时一条就够

---

## 2. Zhipu 的实现摘要

### 文件
- `brain/v5/lightweight_record_router.py`(~630 行)——核心纯规划函数 `plan_lightweight_record_write`,加一堆内部 helper
- `brain/v5/lightweight_record_router_contracts.py`——`validate_lightweight_record_write_plan` / `require_valid_lightweight_record_write_plan`
- `brain/v5/mcp_tools.py`——加了 `aitp_v5_plan_lightweight_record_write` wrapper
- `brain/v5/cli.py`——加了 `recording plan-lightweight-write` 子命令 + dispatch
- `brain/v5/public_surfaces.py`——注册 surface(name + purpose + validator + dict)
- `brain/v5/runtime_entrypoint_catalog.py` + `runtime_entrypoint_samples.py`——加 entrypoint + sample args
- `tests/test_v5_lightweight_record_router.py`——15 个测试

### 核心实现说明(由 Zhipu 自述)

**信任边界:** 用模块级常量 `_TRUST_BOUNDARY` 和 `_TOP_LEVEL_TRUTH` 构造,所有 4 个 decision 路径(no_write / plan_write / needs_human / unsupported)都返回这组字段。**Zhipu 声称**每条路径都满足 can_update_claim_trust=false / orientation_only=true / summary_inputs_trusted=false / can_update_kernel_state=false。MCP wrapper 和 CLI 都通过 `require_valid_public_surface("lightweight_record_write_plan", ...)` 包裹输出。

**路由:** 用关键词 substring 匹配(`kw in text_lower`)判断是否触发各种 record 类型。

**第一轮代码审查(由另一个 AI 做)发现 3 个 IMPORTANT + 1 个 nit,Zhipu 已全部修复:**
- **I-1(已修)**:substring 匹配误匹配普通英文词——`log`⊂`logic`、`dat`⊂`update`、`table`⊂`acceptable`、`path`⊂`empathy` 等,导致普通聊天被误判成 artifact/runtime failure plan,违反 §5.1 no_write 规则。**修复:对歧义短英文 token(log/dat/table/path/chart/dump/report/image)加 word-boundary 匹配(`\bkw\b`),并把过泛的 `path`/`缺少`/`final lane` 从关键词列表移除。**
- **I-2(已修)**:artifact path alone → 不产 evidence 这条 §10 验收标准原本没测,加了测试锁定。
- **I-3(已修)**:四条 `forbidden_interpretations` 字符串原本是约定非断言,加了测试 pin 住。
- **nit(已修)**:`_wants_sensemaking` 有个冗余 clause,删了。

**15 个测试覆盖:**
1. no_write for casual chat
2. artifact + sensemaking for old/new plot boundary
3. gap routes to proof_obligation only
4. tool_run verified result can plan evidence
5. runtime failure not algorithm failure
6. active claim mismatch does not default to active
7. trust request only preflight no apply
8. native MCP tools/list advertises planner
9. runtime entrypoint catalog includes planner
10. contract rejects plan that can update trust
11. planner writes nothing to disk(byte count 不变)
12. malformed ref → unsupported
13. (I-2) artifact path alone → only artifact, not evidence
14. (I-3) plan_write carries all 4 forbidden_interpretations
15. (I-1 regression) ordinary prose with embedded fragments does not write

**测试结果:** 15 router 测试 + 66 相关套件(recording_navigator/public_surfaces/runtime_entrypoints/cli)测试全过,0 回归。

### maturity_level 的事实
代码里真实的 `MATURITY_LEVELS = {"exploratory", "finite-size evidence", "formula-identified", "theorem-candidate", "publishable"}`(没有 "hypothesis")。Zhipu 用了 `"exploratory"`(不是规划原文写的 "hypothesis"),符合规划的警告。

---

## 3. 给 GPT 的具体任务

请你基于以上信息审查,不需要访问代码库(但如果认为关键信息缺失请指出):

### 任务 1:符合性审查
逐条对照 §1 的约束,判断 Zhipu 的实现是否真的满足:
- 4 个信任边界字段是否在所有路径都满足?(Zhipu 自述满足,但你看实现摘要里有没有漏洞)
- "只规划不写入"——除了 byte-count 测试,实现层面有没有可能漏掉某个写盘路径?
- evidence 的触发条件(tool_run/validation_result canonical ref)——实现真的只在有这些 ref 时才产 evidence 吗?会不会有别的路径绕过?
- target claim 选择保守吗?会不会在某些情况下默认用 active claim 而违反 §5.2?
- "不要因为出现 claim 名称就写入"——这条做到了吗?

### 任务 2:第一轮审查的修复质量
- I-1 的修复(word-boundary 匹配 + 移除 path/缺少/final lane)是否真的解决了问题?有没有残留的 substring 陷阱?**请你想几个新的、第一轮审查和 Zhipu 都没测过的歧义词,推断它们会不会误匹配。**
- I-2/I-3 的测试是否真的锁定了对应行为?
- 你认为第一轮审查**漏掉了什么 Zhipu 和它都没发现的问题**?

### 任务 3:规划本身的问题(元审查)
- 这份规划(附录的 zhipu-plan)本身有没有设计缺陷?比如:关键词 substring 匹配这个根本方法是不是就不靠谱?有没有更稳的路由判据?
- "plan-only,不执行"这个定位对不对?还是说应该直接支持 execute=true(规划 §0 提到"除非后续明确实现 execute=false/true 的执行层")?
- 这个 surface 真的解决了 AITP 的核心问题(可追溯/跨会话/成败路线明确)吗,还是只是又加了一个 read-only 工具?

### 任务 4:明确结论
给出:**APPROVE / REQUEST CHANGES / BLOCK**,并说明:
- 哪些是 merge-blocking(必须改)
- 哪些是 should-fix(应该改但不阻塞)
- 哪些是 nice-to-have
- 如果 REQUEST CHANGES,列出具体要改什么

### 输出格式
1. 符合性审查(逐条)
2. 第一轮修复质量评估 + 你发现的新问题
3. 规划本身的元审查
4. 明确结论(APPROVE/REQUEST CHANGES/BLOCK)+ 必改清单

请直言。如果实现确实扎实,直接说 APPROVE 并简述理由;如果有问题,明确指出来。

---

## 附录:完整实现规划(aitp-lightweight-record-router-zhipu-plan.md)

```markdown
# AITP v5 轻量记录路由器优化方案 / Zhipu 执行版

本文档是给 Zhipu 执行的实现规格,不是头脑风暴。请严格按本文改动,不要另起架构,不要把记录路由器写成自动证据生成器,不要削弱 AITP v5 的 trust / validation / provenance 底座。

## 0. 目标

在现有 AITP v5 progressive recording navigator 之上,新增一个轻量记录路由器 surface:

科研过程短事件 -> 判断是否需要记录 -> 选择目标 claim -> 选择最小 record 集合 -> 输出可执行 typed write plan

这个 surface 的职责是生成计划,不是推进科研结论。默认只读 typed records 和输入事件,返回 plan-only payload。除非后续明确实现 `execute=false/true` 的执行层,本次不要直接写入记录。

必须保持以下边界:
- can_update_claim_trust=false
- summary_inputs_trusted=false
- orientation_only=true
- relation map 只能用于定位/边界,不能当 evidence
- runtime failure 只能记录为运行/环境/工具失败,不能自动判为算法失败
- 旧图/旧口径不能自动当成新报告 evidence
- event_summary 提到 claim 不等于提升 confidence
- 一个 sensemaking_report 足够时,不要拆成多条冗余 record

## 1. 当前代码基础

复用这些现有模块:
- brain/v5/recording_navigator.py(classify_recording_candidate / build_recording_navigation_state / expand_recording_slot / verify_recording_effect + _SLOT_EXPANSIONS)
- brain/v5/mcp_tools.py(已暴露的 recording navigator 工具)
- brain/v5/models.py(ArtifactRecord / SensemakingReportRecord / ProofObligationRecord / EvidenceRecord / ValidationContractRecord / ValidationResultRecord / TrustUpdateRequest)
- brain/v5/research_state.py + mcp_research_state.py(artifact/proof obligation/claim status helper)
- brain/v5/sensemaking.py(record_sensemaking_report;validation_status 必须是 not_validation)
- brain/v5/record_refs.py(canonical refs 格式 <kind>:<id>,lookup_record_refs)
- tests/test_v5_recording_navigator.py

不要改 legacy brain/mcp_server.py。不要把新逻辑放进旧 L0-L4 pipeline。

## 2. 新增 public surface

lightweight_record_write_plan

新增 MCP tool: aitp_v5_plan_lightweight_record_write
推荐 CLI: aitp-v5 recording plan-lightweight-write <args>

名字必须体现这是 plan,不是 write。

## 3. 输入 schema

def aitp_v5_plan_lightweight_record_write(
    base: str, *,
    topic_id: str,              # 必填
    current_session_id: str,    # 必填
    event_summary: str,         # 必填,短事件
    active_claim_id: str = "",  # 可空,只是候选
    target_claim_hint: str = "",# 可空,claim id/statement 片段/关键词
    touched_files_or_artifacts: list[str] | None = None,    # 文件路径/artifact ref/图路径
    touched_tool_runs_or_evidence_refs: list[str] | None = None,  # 必须 canonical refs
    risk_hint: str = "",        # 只用于路由严格度,不触发 trust update
) -> dict

## 4. 输出 schema(关键字段)

{
  "kind": "lightweight_record_write_plan",
  "decision": "no_write | plan_write | needs_human_target_claim | unsupported",
  "topic_id", "current_session_id", "active_claim_id",
  "target_claim": {"target_claim_id", "reason_for_target_claim", "confidence": "high|medium|low"},
  "write_reasons": [...],
  "no_write_reason": "",
  "selected_record_types": ["artifact", "sensemaking_report"],
  "typed_write_plan": [{record_type, target_claim_id, summary, required_fields, optional_fields, verification_refs, recommended_mcp_tool, execute_now: false}],
  "trust_boundary": {
    "can_update_claim_trust": false, "trust_update_requested": false, "trust_preflight_required": false,
    "forbidden_interpretations": ["relation_map_is_not_evidence","runtime_failure_is_not_algorithm_failure","old_plot_is_not_new_report_evidence","event_summary_does_not_raise_confidence"]
  },
  "final_human_readable_summary": "...",
  "truth_source": "event_metadata_and_typed_records",
  "summary_inputs_trusted": false, "orientation_only": true,
  "can_update_kernel_state": false, "can_update_claim_trust": false
}

注意:verification_refs 对未创建记录用占位符 artifact:<to-be-created>,已有 ref 保留 canonical 形式。execute_now 本次必须恒为 false。

## 5. 路由规则

### 5.1 write / no_write 判断

plan_write 只在 6 种情况:
1. 产生/定位 durable artifact(有 touched_files 或 event 含文件/图/JSON/log/report/notebook/dump/table)
2. 澄清 claim 边界(关键词:边界/scope/limitation/cannot mix/non-claim/口径/final lane/diagnostic lane)
3. 旧新口径冲突(不能混用/old plot/stale/legacy result/old convention/contaminated)
4. open gap/validation gap(open gap/validation gap/proof gap/missing check/未验证/缺少证明/缺少复现)
5. negative result/undefined object(negative result/inconclusive/failed physics/undefined object)
6. 下一步复现/证明义务(next action/reproduce/rerun/proof obligation/下一步/复现实验/证明义务)

no_write:普通聊天/重复总结/临时推测/只有"我觉得可能也许"且无 artifact/gap/boundary/failure/义务/只要求解释概念。
不要因为出现 claim 名称就写入。

### 5.2 目标 claim 选择(保守)

1. target_claim_hint 是现有 claim id 且属本 topic → 用它,confidence=high
2. hint 是 statement 片段 → 扫 sibling:完全/高相似命中 medium/high;多候选 needs_human
3. active_claim_id 与 event 明显匹配 → 用 active,medium(非常明显才 high)
4. event 不匹配 active → 能建议 sibling 就建议,否则 needs_human
5. record_type 仅 artifact 且 claim 不明 → needs_human(因为 ArtifactRecord 要求 claim_id 非空)
用 list_valid_records 扫 topic claims;简单 token overlap 足够,不引入新依赖;排除泛 token(claim/result/figure/plot/evidence);不改 session binding。

### 5.3 record 类型选择(固定优先级)

1. artifact:已有 canonical ref 则只作 ref 不重复 attach
2. sensemaking_report:默认一条合并,不要拆五条
3. proof_obligation:用现有 ProofObligationRecord,不要新造 ValidationGapRecord;validation gap 用 obligation_type="validation_gap"
4. evidence:只有含 tool_run:<id> 或 validation_result:<id> 才规划;只 runtime failure 不 evidence;只 artifact 不 evidence
5. trust_preflight:只有明确要求 trust update/L2 promotion 才出现;只规划 preflight 不调 apply

最小集合规则:
- artifact + 口径解释:artifact + sensemaking_report
- 只有口径/边界/不能混用:只用 sensemaking_report
- 只有 open gap/义务:只用 proof_obligation
- artifact + open gap:artifact + proof_obligation
- tool_run/validation_result + verified result:可用 evidence,必要时加 artifact
- trust update request:trust_preflight + 必要 evidence refs;缺 passed validation 必须在 final summary 说明不能提升 trust

## 6. 字段填充规范

### 6.1 artifact plan
recommended_mcp_tool: aitp_v5_attach_artifact_auto
required_fields: topic_id/claim_id/path(若本地文件)/artifact_type/inferred/summary
artifact_type inference: .png/.jpg/.svg→plot; .pdf→report; .json→result_json; .jsonl→jsonl_log; .log/.out/.err→log; .ipynb→notebook; .csv/.tsv/.dat/.npy/.h5→data; 其他 other
verification_refs: artifact:<to-be-created> 或已有 canonical ref

### 6.2 sensemaking_report plan
recommended_mcp_tool: aitp_v5_record_sensemaking_report
required_fields: topic_id/claim_id/title/summary(明确说 not evidence/trust)
注意:当前 SensemakingReportRecord 无 metadata 字段;plan payload 可含 metadata 但不要传给写入工具除非扩展 schema

### 6.3 proof_obligation plan
recommended_mcp_tool: aitp_v5_create_proof_obligation
required_fields: topic_id/claim_id/statement/obligation_type(proof_gap|validation_gap|reproducibility_gap|undefined_object_gap)/status=open/maturity_level/next_action
**用现有 MATURITY_LEVELS,编码前查 research_state.py::MATURITY_LEVELS,不要造会失败的值**

### 6.4 evidence plan
只有输入含 canonical tool_run:<id> 和/或 validation_result:<id> 才产
recommended_mcp_tool: aitp_v5_record_evidence
不从 relation map/chat summary/无新 provenance 的 old plot/runtime failure alone/artifact path alone 产 evidence

### 6.5 trust_preflight plan
只有明确要求 confidence/trust/L2/promotion 才产
recommended_mcp_tool: aitp_v5_preflight_trust_update
**不要暴露或调 aitp_v5_apply_trust_update**

## 7. Canonical refs

接受输入 ref:artifact/tool_run/evidence/validation_result/reference_location/code_state
用 lookup_record_refs 校验已有 ref;MCP 写工具通常要 bare id;verification_refs 用 canonical prefixed ref。
malformed → decision=unsupported 或 needs_human,带清晰 diagnostic,不要静默 strip 未知 prefix。

## 8. Contract 和 public surface 注册

加:lightweight_record_router.py + lightweight_record_router_contracts.py
更新:public_surfaces.py(加 surface name/purpose/validator)/ mcp_tools.py(import planner + 加工具)/ cli.py(加 recording plan-lightweight-write)/ runtime_entrypoint_catalog.py(加 entrypoint)/ native_mcp.py(mcp_tools 暴露即可,不需手改)

Contract 要求:
- kind == lightweight_record_write_plan
- decision ∈ {no_write, plan_write, needs_human_target_claim, unsupported}
- typed_write_plan 是 list
- trust_boundary.can_update_claim_trust is False
- 顶层 summary_inputs_trusted is False / orientation_only is True / can_update_kernel_state is False / can_update_claim_trust is False
- no_write → typed_write_plan 空 + no_write_reason 非空
- plan_write → target_claim.target_claim_id 非空 + selected_record_types 非空 + typed_write_plan 非空
- 每个 plan item:有 record_type/target_claim_id/summary/required_fields/verification_refs/recommended_mcp_tool/execute_now==False

## 9. 测试(最少这些)

1. test_no_write_for_casual_chat
2. test_artifact_and_sensemaking_for_old_new_plot_boundary(selected types 恰好 ["artifact","sensemaking_report"],无 evidence)
3. test_gap_routes_to_proof_obligation_only(一个 proof_obligation,无 evidence)
4. test_tool_run_verified_result_can_plan_evidence(造 ToolRunRecord,refs 含 tool_run:<id>,evidence 允许,refs 规范化)
5. test_runtime_failure_not_algorithm_failure(sensemaking_report 或 proof_obligation,无 evidence,final summary 明确说 not algorithm failure)
6. test_active_claim_mismatch_does_not_default_to_active(两个 sibling claim,active 是 A,event 是 B → 目标 B 或 needs_human)
7. test_trust_request_only_preflight_no_apply(trust_preflight 出现,顶层 can_update_claim_trust false,无 apply 工具)
8. test_native_mcp_tools_list_advertises_planner(工具出现,description 含 plan)
9. test_runtime_entrypoint_catalog_includes_planner
10. test_contract_rejects_plan_that_can_update_trust(can_update_claim_trust=True → ContractError)

## 10. 验收标准

- 新 public surface 通过 require_valid_public_surface
- MCP 工具被 native MCP 列出
- CLI 返回与 MCP 相同 payload 形状
- 规划 surface 不写任何 typed record
- 不暴露 trust apply 路径
- 不从 relation map/chat summary/runtime failure/old plot alone 产 evidence
- artifact path alone 只产 artifact plan 不产 evidence
- open gap 产 proof obligation plan
- claim 不匹配时不默认用 active claim
- plan 最小:sensemaking 够用时一条

## 11. 实现顺序

1. lightweight_record_router.py(纯规划 helper,无写)
2. lightweight_record_router_contracts.py
3. 注册 public surface
4. 加 MCP wrapper
5. 加 CLI 命令
6. 加 runtime entrypoint catalog
7. 加测试
8. 跑测试
9. 测试通过后可选更新 docs/README

## 12. 常见错误

- 不要在 planner 内调 record_sensemaking_report/attach_artifact/record_evidence/create_proof_obligation
- 不要加新数据库/索引守护/非文件存储
- 不要把 validation_gap 做成新 record family
- 不要让 relation-map 输出当 source/evidence ref
- 不要用 prose/文件路径填 evidence_refs
- 不要把 plan-only metadata 传给不支持它的写入工具
- 不要把所有 negative result 提升到 L2
- 不要改 ClaimRecord.confidence_state
- 不要调 aitp_v5_apply_trust_update
- 不要每次 write plan 都要求 human checkpoint;只在 target claim 不清时返回 needs_human_target_claim
```

---

## 附:关键约束(审查必须对照)

- **不能动信任底座**:四个核心不变量(context≠evidence 等)、trust update preflight、validation contract 绑定、append-only provenance。优化只能在读端/聚合层加东西。
- **存储保持纯文件**:Markdown+YAML,无数据库。
- **向后兼容**:老记录(没新字段)必须继续可读。
- **Python 实现**:不换语言。
- **agent 通过 MCP 工具消费**:优化产物最好是新 MCP surface 或增强现有 surface。
