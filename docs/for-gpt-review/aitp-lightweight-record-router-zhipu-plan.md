# AITP v5 轻量记录路由器优化方案 / Zhipu 执行版

本文档是给 Zhipu 执行的实现规格,不是头脑风暴。请严格按本文改动,不要另起架构,不要把记录路由器写成自动证据生成器,不要削弱 AITP v5 的 trust / validation / provenance 底座。

## 0. 目标

在现有 AITP v5 progressive recording navigator 之上,新增一个轻量记录路由器 surface:

```text
科研过程短事件 -> 判断是否需要记录 -> 选择目标 claim -> 选择最小 record 集合 -> 输出可执行 typed write plan
```

这个 surface 的职责是生成计划,不是推进科研结论。默认只读 typed records 和输入事件,返回 plan-only payload。除非后续明确实现 `execute=false/true` 的执行层,本次不要直接写入记录。

必须保持以下边界:

- `can_update_claim_trust=false`
- `summary_inputs_trusted=false`
- `orientation_only=true`
- relation map 只能用于定位/边界,不能当 evidence
- runtime failure 只能记录为运行/环境/工具失败,不能自动判为算法失败
- 旧图/旧口径不能自动当成新报告 evidence
- event_summary 提到 claim 不等于提升 confidence
- 一个 `sensemaking_report` 足够时,不要拆成多条冗余 record

## 1. 当前代码基础

请复用这些现有模块:

- `brain/v5/recording_navigator.py`
  - 已有 read-only surfaces:
    - `classify_recording_candidate`
    - `build_recording_navigation_state`
    - `expand_recording_slot`
    - `verify_recording_effect`
  - 已有 slot 概念和 `_SLOT_EXPANSIONS`,不要重复造一套 slot registry。
- `brain/v5/mcp_tools.py`
  - 已暴露 `aitp_v5_classify_recording_candidate`, `aitp_v5_get_recording_navigation_state`, `aitp_v5_expand_recording_slot`, `aitp_v5_verify_recording_effect`。
- `brain/v5/models.py`
  - 相关 record:
    - `ArtifactRecord`
    - `SensemakingReportRecord`
    - `ProofObligationRecord`
    - `EvidenceRecord`
    - `ValidationContractRecord`
    - `ValidationResultRecord`
    - `TrustUpdateRequest`
- `brain/v5/research_state.py` / `brain/v5/mcp_research_state.py`
  - artifact / proof obligation / claim status helper 已存在。
- `brain/v5/sensemaking.py`
  - `record_sensemaking_report` 已存在,且 `validation_status` 必须是 `not_validation`。
- `brain/v5/record_refs.py`
  - canonical refs 格式为 `<kind>:<id>`,例如 `artifact:artifact-xxx`, `tool_run:run-xxx`, `evidence:evidence-xxx`。
- `tests/test_v5_recording_navigator.py`
  - 新测试应优先加在这里,除非新增独立模块后拆出 `tests/test_v5_lightweight_record_router.py` 更清晰。

不要改 legacy `brain/mcp_server.py`。不要把新逻辑放进旧 L0-L4 pipeline。

## 2. 新增 public surface

新增 public surface:

```text
lightweight_record_write_plan
```

新增 MCP tool:

```text
aitp_v5_plan_lightweight_record_write
```

推荐 CLI:

```text
aitp-v5 recording plan-lightweight-write <args>
```

如果认为名字过长,可以用:

```text
aitp_v5_plan_recording_write
aitp-v5 recording plan-write <args>
```

但必须保持一个原则:名字里要体现这是 plan,不是 write。

## 3. 输入 schema

MCP tool 入参:

```python
def aitp_v5_plan_lightweight_record_write(
    base: str,
    *,
    topic_id: str,
    current_session_id: str,
    event_summary: str,
    active_claim_id: str = "",
    target_claim_hint: str = "",
    touched_files_or_artifacts: list[str] | None = None,
    touched_tool_runs_or_evidence_refs: list[str] | None = None,
    risk_hint: str = "",
) -> dict:
    ...
```

字段含义:

- `topic_id`: 必填。AITP topic id。
- `current_session_id`: 必填。当前 session id; 可用于读取 active focus,但不能默认把事件写入 active claim。
- `active_claim_id`: 可空。只是候选,不是默认目标。
- `target_claim_hint`: 可空。可以是 claim id、claim statement 片段、关键词。
- `event_summary`: 必填。短事件、澄清、失败原因、结果边界、图表口径、open gap 或下一步计划。
- `touched_files_or_artifacts`: 可空。可以是文件路径、已存在 artifact ref,或图/JSON/log 路径。
- `touched_tool_runs_or_evidence_refs`: 可空。必须支持 canonical refs,例如 `tool_run:run-xxx`, `evidence:evidence-xxx`, `validation_result:result-xxx`。
- `risk_hint`: 可空。只用于路由严格度和 trust boundary 文案,不能触发 trust update。

## 4. 输出 schema

返回 payload:

```json
{
  "kind": "lightweight_record_write_plan",
  "decision": "no_write | plan_write | needs_human_target_claim | unsupported",
  "topic_id": "...",
  "current_session_id": "...",
  "active_claim_id": "...",
  "target_claim": {
    "target_claim_id": "...",
    "reason_for_target_claim": "...",
    "confidence": "high | medium | low"
  },
  "write_reasons": ["..."],
  "no_write_reason": "",
  "selected_record_types": ["artifact", "sensemaking_report"],
  "typed_write_plan": [
    {
      "record_type": "artifact",
      "target_claim_id": "...",
      "summary": "...",
      "required_fields": {
        "topic_id": "...",
        "claim_id": "...",
        "artifact_type": "plot | json | log | report | notebook | data | other",
        "uri": "...",
        "summary": "..."
      },
      "optional_fields": {
        "size_bytes": 0,
        "metadata": {
          "status": "orientation_only_not_claim_trust",
          "event_summary": "...",
          "source": "lightweight_record_router"
        }
      },
      "verification_refs": ["artifact:<to-be-created>"],
      "recommended_mcp_tool": "aitp_v5_attach_artifact",
      "execute_now": false
    }
  ],
  "trust_boundary": {
    "can_update_claim_trust": false,
    "trust_update_requested": false,
    "trust_preflight_required": false,
    "forbidden_interpretations": [
      "relation_map_is_not_evidence",
      "runtime_failure_is_not_algorithm_failure",
      "old_plot_is_not_new_report_evidence",
      "event_summary_does_not_raise_confidence"
    ]
  },
  "final_human_readable_summary": "一句话说明记录了什么、没声称什么。",
  "truth_source": "event_metadata_and_typed_records",
  "summary_inputs_trusted": false,
  "orientation_only": true,
  "can_update_kernel_state": false,
  "can_update_claim_trust": false
}
```

注意:

- `typed_write_plan[].verification_refs` 对尚未创建的记录可用占位符,例如 `artifact:<to-be-created>`,但对输入中已有 refs 必须保留 canonical ref,例如 `tool_run:run-abc`。
- 如果输入已有 canonical artifact ref,用真实 ref,不要再建议创建 artifact。
- `execute_now` 本次必须恒为 `false`。

## 5. 路由规则

实现一个纯函数,建议放在新模块:

```text
brain/v5/lightweight_record_router.py
```

核心函数:

```python
def plan_lightweight_record_write(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    current_session_id: str,
    event_summary: str,
    active_claim_id: str = "",
    target_claim_hint: str = "",
    touched_files_or_artifacts: list[str] | None = None,
    touched_tool_runs_or_evidence_refs: list[str] | None = None,
    risk_hint: str = "",
) -> dict:
    ...
```

### 5.1 write / no_write 判断

只在以下情况 `decision=plan_write`:

1. 产生或定位了 durable artifact
   - 有 `touched_files_or_artifacts`
   - 或 event_summary 包含明显文件/图表/JSON/log/report/notebook/dump/table 等 durable 输出。
2. 澄清 claim 边界
   - 关键词: 边界, scope, limitation, cannot mix, non-claim, 口径, 图表口径, final lane, diagnostic lane。
3. 发现旧结果和新口径不能混用
   - 关键词: 不能混用, old plot, old figure, stale, outdated, legacy result, old convention, new convention, contaminated, not final evidence。
4. 产生 open gap / validation gap
   - 关键词: open gap, validation gap, proof gap, missing check, 未验证, 缺少证明, 缺少复现, missing validation。
5. 记录 negative result / undefined object
   - 关键词: negative result, inconclusive, failed physics, undefined object, 未定义对象, object undefined, no solution。
6. 明确下一步复现实验或证明义务
   - 关键词: next action, reproduce, rerun, proof obligation, validation contract needed, 下一步, 复现实验, 证明义务。

返回 `decision=no_write`:

- 普通聊天。
- 重复总结。
- 临时推测。
- 只有“我觉得/可能/也许”的想法,且没有 artifact、gap、claim boundary、路线失败、下一步义务。
- 只要求解释概念,没有 durable event。

不要因为出现 claim 名称就写入。

### 5.2 目标 claim 选择

目标 claim 选择必须保守。

顺序:

1. 如果 `target_claim_hint` 是现有 claim id,且属于 `topic_id`,用它,confidence=`high`。
2. 如果 `target_claim_hint` 是 statement 片段,扫描同 topic sibling claims:
   - 完全或高相似命中: confidence=`medium` 或 `high`。
   - 多个接近候选: `decision=needs_human_target_claim`,不要生成写计划。
3. 如果 `active_claim_id` 与 event_summary 明显匹配,可用 active claim:
   - 匹配依据: active claim statement / scope / uncertainty 的关键名词出现在 event_summary。
   - confidence=`medium`,除非非常明显才 high。
4. 如果 event_summary 明显不匹配 active claim,不要写 active claim:
   - 如果能建议 sibling claim,返回 suggested target。
   - 如果不能,`decision=needs_human_target_claim`。
5. 如果 record_type 仅为 artifact 且 claim 不明:
   - 当前 `ArtifactRecord` 要求 `claim_id` 非空,所以不能创建 claimless artifact。
   - 返回 `needs_human_target_claim`,并说明 artifact 需要 claim binding。

实现提示:

- 用 `list_valid_records(ws.registry_dir("claims"), ClaimRecord)` 扫 topic claims。
- 简单 token overlap 足够,不要引入新依赖。
- 排除太泛的 token,如 claim, result, figure, plot, evidence。
- 目标 claim 选择只能输出建议,不能改 session binding。

### 5.3 record 类型选择

优先顺序必须固定:

1. `artifact`
   - 已有文件、图、JSON、日志、report、notebook、raw dump。
   - 如果输入是普通路径,计划调用 `aitp_v5_attach_artifact` 或 `aitp_v5_attach_artifact_auto`。
   - 如果输入已经是 `artifact:<id>`,不要重复 attach,只作为 ref。
2. `sensemaking_report`
   - 解释口径、边界、不能混用、old/new convention、final vs diagnostic lane、runtime failure vs algorithm failure。
   - 默认优先用一条 sensemaking_report 合并解释,不要拆五条。
3. `proof_obligation`
   - open gap / validation gap / missing proof / missing reproducibility / required next check。
   - AITP 现有 record 名为 `ProofObligationRecord`; 不要新造 `ValidationGapRecord`。
   - validation gap 用 `obligation_type="validation_gap"` 或 `"proof_gap"`。
4. `evidence`
   - 只有当输入含有可复现 `tool_run:<id>` 或 `validation_result:<id>` 时才规划 evidence。
   - 如果只有 artifact 没有 tool run / validation result,不要自动 evidence。
   - 如果只是 runtime failure,不要 evidence; 用 sensemaking_report 或 proof_obligation。
5. `trust_preflight`
   - 只有 event_summary 或 risk_hint 明确要求 trust update / confidence promotion / L2 promotion 时才出现。
   - 本 surface 只规划 preflight,不调用 `apply_trust_update`。

最小集合规则:

- artifact + 口径解释: `artifact` + `sensemaking_report`
- 只有口径/边界/不能混用: 只用 `sensemaking_report`
- 只有 open gap/下一步义务: 只用 `proof_obligation`
- artifact + open gap: `artifact` + `proof_obligation`
- tool_run/validation_result + verified result: 可用 `evidence`,必要时加 `artifact`
- trust update request: `trust_preflight` + 必要 evidence refs,但如果缺 passed validation,必须在 final summary 说明不能提升 trust

## 6. 字段填充规范

### 6.1 artifact plan

```json
{
  "record_type": "artifact",
  "recommended_mcp_tool": "aitp_v5_attach_artifact_auto",
  "required_fields": {
    "topic_id": "<topic_id>",
    "claim_id": "<target_claim_id>",
    "path": "<local path if local file>",
    "artifact_type": "<inferred>",
    "summary": "<event_summary compressed>"
  },
  "optional_fields": {
    "metadata": {
      "status": "orientation_only_not_claim_trust",
      "event_summary": "<event_summary>",
      "router_reason": "durable_artifact_located"
    }
  },
  "verification_refs": ["artifact:<to-be-created>"]
}
```

Artifact type inference:

- `.png`, `.jpg`, `.jpeg`, `.svg`, `.pdf` -> `plot` or `report`; use `plot` for figures, `report` for prose PDF.
- `.json`, `.jsonl` -> `result_json` or `jsonl_log`; prefer `result_json` unless event says log.
- `.log`, `.out`, `.err` -> `log`.
- `.ipynb` -> `notebook`.
- `.csv`, `.tsv`, `.dat`, `.npy`, `.h5`, `.hdf5` -> `data`.
- otherwise `other`.

### 6.2 sensemaking_report plan

```json
{
  "record_type": "sensemaking_report",
  "recommended_mcp_tool": "aitp_v5_record_sensemaking_report",
  "required_fields": {
    "topic_id": "<topic_id>",
    "claim_id": "<target_claim_id>",
    "title": "<short title>",
    "summary": "<explain boundary; explicitly say this is not evidence/trust>"
  },
  "optional_fields": {
    "evidence_refs": [],
    "open_questions": ["..."],
    "next_actions": ["..."]
  },
  "metadata": {
    "status": "orientation_only_not_claim_trust"
  },
  "verification_refs": ["sensemaking_report:<to-be-created>"]
}
```

Important: current `SensemakingReportRecord` has no `metadata` field. In the plan payload you may include `metadata` for the router plan, but do not pass it to `aitp_v5_record_sensemaking_report` unless the model/schema is extended. If extending the schema, do it separately and keep backward compatibility.

### 6.3 proof_obligation plan

```json
{
  "record_type": "proof_obligation",
  "recommended_mcp_tool": "aitp_v5_create_proof_obligation",
  "required_fields": {
    "topic_id": "<topic_id>",
    "claim_id": "<target_claim_id>",
    "statement": "<missing proof/check/gap>",
    "obligation_type": "proof_gap | validation_gap | reproducibility_gap | undefined_object_gap",
    "status": "open",
    "maturity_level": "hypothesis",
    "next_action": "<specific next action>"
  },
  "optional_fields": {
    "required_evidence": ["..."],
    "proof_strategy": [],
    "failure_modes": [],
    "source_refs": [],
    "evidence_refs": [],
    "artifact_ids": []
  },
  "metadata": {
    "status": "orientation_only_not_claim_trust"
  },
  "verification_refs": ["proof_obligation:<to-be-created>"]
}
```

Use existing accepted `maturity_level` values. Before coding, inspect `brain/v5/research_state.py::MATURITY_LEVELS`. Do not invent a value that fails tests.

### 6.4 evidence plan

Only produce when there is a canonical `tool_run:<id>` and/or `validation_result:<id>` ref.

```json
{
  "record_type": "evidence",
  "recommended_mcp_tool": "aitp_v5_record_evidence",
  "required_fields": {
    "topic_id": "<topic_id>",
    "claim_id": "<target_claim_id>",
    "evidence_type": "tool_run | validation_result | bounded_numerical_evidence | negative_result",
    "status": "supports | contradicts | inconclusive | diagnostic_only",
    "summary": "<scoped summary>"
  },
  "optional_fields": {
    "supports_outputs": [],
    "source_refs": [],
    "tool_run_ids": ["<id without prefix>"],
    "validation_result_ids": ["<id without prefix>"],
    "artifact_ids": ["<id without prefix>"]
  },
  "metadata": {
    "status": "orientation_only_not_claim_trust unless verified evidence is explicit"
  },
  "verification_refs": ["evidence:<to-be-created>"]
}
```

Do not create evidence from:

- relation map
- chat summary
- old plot without new provenance
- runtime failure alone
- artifact path alone

### 6.5 trust_preflight plan

Only if user explicitly asks for confidence / trust / L2 / promotion.

```json
{
  "record_type": "trust_preflight",
  "recommended_mcp_tool": "aitp_v5_preflight_trust_update",
  "required_fields": {
    "action": "set_confidence | promote_to_l2 | other",
    "session_id": "<current_session_id>",
    "topic_id": "<topic_id>",
    "claim_id": "<target_claim_id>",
    "requested_state": "<only if explicit>"
  },
  "optional_fields": {
    "source_kind": "typed_records",
    "source_ref": "",
    "evidence_refs": [],
    "code_state_ids": [],
    "rationale": "<why requested, not why approved>"
  },
  "verification_refs": ["trust_update_preflight:<request-id-or-to-be-created>"]
}
```

Do not expose or call `aitp_v5_apply_trust_update`.

## 7. Canonical refs

The router must normalize and validate refs:

- Accepted input refs:
  - `artifact:<id>`
  - `tool_run:<id>`
  - `evidence:<id>`
  - `validation_result:<id>`
  - `reference_location:<id>`
  - `code_state:<id>`
- Use `lookup_record_refs` for existing refs when possible.
- In write plan fields, MCP write tools usually want bare ids, not prefixed refs:
  - `artifact_ids=["artifact-xxx"]`
  - `tool_run_ids=["run-xxx"]`
  - `evidence_refs=["evidence-xxx"]` or existing convention in target tool
- In `verification_refs`, always use canonical prefixed refs:
  - `artifact:artifact-xxx`
  - `tool_run:run-xxx`
  - `evidence:evidence-xxx`

If a ref is malformed, return `decision=unsupported` or `needs_human_target_claim` with a clear diagnostic. Do not silently strip unknown prefixes.

## 8. Contract and public surface registration

Add:

- `brain/v5/lightweight_record_router.py`
- `brain/v5/lightweight_record_router_contracts.py`

Update:

- `brain/v5/public_surfaces.py`
  - add `"lightweight_record_write_plan"` to `_PUBLIC_SURFACE_NAMES`
  - add purpose string
  - import and register `require_valid_lightweight_record_write_plan`
- `brain/v5/mcp_tools.py`
  - import planner
  - add `aitp_v5_plan_lightweight_record_write`
- `brain/v5/cli.py`
  - add `recording plan-lightweight-write`
- `brain/v5/runtime_entrypoint_catalog.py`
  - add entrypoint metadata
- `brain/v5/native_mcp.py`
  - no direct manual edit should be needed if `mcp_tools.py` exposes function through `aitp_v5_*` naming.

Contract requirements:

- `kind == "lightweight_record_write_plan"`
- `decision` in `{"no_write", "plan_write", "needs_human_target_claim", "unsupported"}`
- `typed_write_plan` is list
- `trust_boundary.can_update_claim_trust is False`
- top-level `summary_inputs_trusted is False`
- top-level `orientation_only is True`
- top-level `can_update_kernel_state is False`
- top-level `can_update_claim_trust is False`
- if `decision == "no_write"`, `typed_write_plan == []` and `no_write_reason` non-empty
- if `decision == "plan_write"`, `target_claim.target_claim_id` non-empty, `selected_record_types` non-empty, `typed_write_plan` non-empty
- every plan item:
  - has `record_type`
  - has `target_claim_id`
  - has `summary`
  - has `required_fields`
  - has `verification_refs`
  - has `recommended_mcp_tool`
  - has `execute_now == False`

## 9. Tests Zhipu must add

Create `tests/test_v5_lightweight_record_router.py` or extend `tests/test_v5_recording_navigator.py`.

Minimum tests:

1. `test_no_write_for_casual_chat`
   - summary: "只是解释一下这个概念,没有新结果"
   - expected: `decision=no_write`, no typed plan, trust false.

2. `test_artifact_and_sensemaking_for_old_new_plot_boundary`
   - input has `touched_files_or_artifacts=["reports/old_kconv.png"]`
   - summary says old plot and new final report口径不能混用
   - expected: selected record types are exactly `["artifact", "sensemaking_report"]` or same order with artifact first.
   - no evidence.

3. `test_gap_routes_to_proof_obligation_only`
   - summary says missing validation check / open gap
   - no artifact, no tool run
   - expected: one `proof_obligation`, no evidence.

4. `test_tool_run_verified_result_can_plan_evidence`
   - create or fake valid `ToolRunRecord` in test store
   - input refs include `tool_run:<id>`
   - summary says reproducible tool run produced checked result
   - expected: evidence plan allowed, refs normalized.

5. `test_runtime_failure_not_algorithm_failure`
   - summary says job failed due runtime/import/path issue
   - expected: `sensemaking_report` or `proof_obligation`, no evidence, final summary explicitly says not algorithm failure.

6. `test_active_claim_mismatch_does_not_default_to_active`
   - create two sibling claims
   - active claim about A, event summary about B
   - expected: target claim B if clear; otherwise `needs_human_target_claim`.

7. `test_trust_request_only_preflight_no_apply`
   - summary says "promote confidence to verified"
   - expected: `trust_preflight` appears, top-level can_update_claim_trust false, no apply tool.

8. `test_native_mcp_tools_list_advertises_planner`
   - `brain.v5.native_mcp._handle_request(... tools/list ...)`
   - expected tool `aitp_v5_plan_lightweight_record_write` appears and description says "plan" or "plan-only".

9. `test_runtime_entrypoint_catalog_includes_planner`
   - expected key maps to CLI/MCP/surface.

10. `test_contract_rejects_plan_that_can_update_trust`
   - manually build payload with `can_update_claim_trust=True`
   - contract raises `ContractError`.

Run at least:

```powershell
uv run --with pytest --with pyyaml --with jsonschema --with fastmcp python -m pytest tests/test_v5_lightweight_record_router.py tests/test_v5_recording_navigator.py tests/test_v5_runtime_entrypoints.py
```

If `uv` is unavailable, use the repo's established test runner, but report the exact command.

## 10. Acceptance criteria

Implementation is not done until all are true:

- New public surface validates through `require_valid_public_surface`.
- MCP tool is listed by native MCP.
- CLI returns same payload shape as MCP.
- No typed record is written by the planning surface.
- No trust apply path is exposed.
- No evidence plan is produced from relation map, chat summary, runtime failure, or old plot alone.
- Artifact path alone creates only artifact plan, not evidence.
- Open gap creates proof obligation plan.
- Claim mismatch avoids defaulting to active claim.
- Plan is minimal: one sensemaking report when that is enough.

## 11. Implementation order

1. Add `lightweight_record_router.py` with pure planning helpers and no writes.
2. Add `lightweight_record_router_contracts.py`.
3. Register public surface in `public_surfaces.py`.
4. Add MCP wrapper in `mcp_tools.py`.
5. Add CLI command in `cli.py`.
6. Add runtime entrypoint catalog item.
7. Add tests.
8. Run targeted tests.
9. Only after tests pass, optionally update docs / README mention.

## 12. Common mistakes to avoid

- Do not call `record_sensemaking_report`, `attach_artifact`, `record_evidence`, or `create_proof_obligation` inside the planner.
- Do not add a new database, index daemon, or non-file storage.
- Do not make `validation_gap` a new record family unless explicitly requested later.
- Do not make relation-map output a source ref or evidence ref.
- Do not fill `evidence_refs` with prose or file paths.
- Do not pass plan-only `metadata` into existing record write tools if the dataclass does not support it.
- Do not promote all negative results to L2 memory.
- Do not change `ClaimRecord.confidence_state`.
- Do not call `aitp_v5_apply_trust_update`.
- Do not require a human checkpoint for every write plan; only return `needs_human_target_claim` when target claim is unclear or ambiguous.

## 13. Example payloads

### 13.1 No write

Input:

```json
{
  "topic_id": "qsgw-headwing-update-librpa",
  "current_session_id": "s1",
  "active_claim_id": "claim-a",
  "event_summary": "我们只是讨论一下下一段话怎么表达,没有新结果。"
}
```

Expected:

```json
{
  "decision": "no_write",
  "no_write_reason": "ordinary_chat_or_repeat_summary_without_durable_research_event",
  "typed_write_plan": [],
  "can_update_claim_trust": false
}
```

### 13.2 Old/new plot boundary

Input:

```json
{
  "topic_id": "qsgw-headwing-update-librpa",
  "current_session_id": "s1",
  "active_claim_id": "claim-qsgw-final",
  "event_summary": "旧的 kconv 图使用 diagnostic lane 口径,不能和新 final report allowlist 混用。",
  "touched_files_or_artifacts": ["research/librpa/reports/old_kconv.png"]
}
```

Expected:

```json
{
  "decision": "plan_write",
  "selected_record_types": ["artifact", "sensemaking_report"],
  "trust_boundary": {
    "can_update_claim_trust": false
  },
  "final_human_readable_summary": "将旧图与新报告口径的混用风险记录为 artifact 指针和 orientation-only 口径说明,没有声称旧图支持新 final claim。"
}
```

### 13.3 Open validation gap

Input:

```json
{
  "topic_id": "qsgw-headwing-update-librpa",
  "current_session_id": "s1",
  "active_claim_id": "claim-qsgw-final",
  "event_summary": "BN 的 final lane 还缺少可复现的 k 点收敛 validation gap,下一步要重跑 allowlist 后再画 final 图。"
}
```

Expected:

```json
{
  "decision": "plan_write",
  "selected_record_types": ["proof_obligation"],
  "typed_write_plan": [
    {
      "record_type": "proof_obligation",
      "required_fields": {
        "obligation_type": "validation_gap",
        "status": "open"
      }
    }
  ],
  "final_human_readable_summary": "记录了 BN final lane 的 validation gap 和下一步复现义务,没有把当前结果提升为证据或 trust。"
}
```

### 13.4 Runtime failure

Input:

```json
{
  "topic_id": "qsgw-headwing-update-librpa",
  "current_session_id": "s1",
  "active_claim_id": "claim-qsgw-final",
  "event_summary": "脚本失败是因为远端环境缺少 matplotlib,不是算法路线失败。"
}
```

Expected:

```json
{
  "decision": "plan_write",
  "selected_record_types": ["sensemaking_report"],
  "final_human_readable_summary": "记录了 runtime failure 的边界:这是环境/依赖问题,没有声称算法失败或 claim 被反驳。"
}
```
