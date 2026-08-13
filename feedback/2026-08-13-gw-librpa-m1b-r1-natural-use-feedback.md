# GW/LibRPA 补充自然使用反馈：M1b-R1 实装后的信噪比与证据生命周期

日期：2026-08-13  
Topic：`/home/bhjia/physics/GW_librpa`（`.aitp/topic/`）  
使用场景：ABACUS/LibRPA SOC 磁群长周期开发，fish 与 Dongfang 双远端 Slurm，数百条历史 Entry  
协议版本：M1a + 已通过 deterministic gate 的 M1b-R1（`check-0.1`、compact `enter` text）

## 1. 反馈边界

这是 M1b-R1 落地后的真实自然使用反馈，不是 gate、spec、freeze revision 或功能授权。它仍属于 2026-08-11 开始的同一条 GW/LibRPA 长会话链，不增加独立自然 session 数量，也不声称 AITP 优于普通文件。本文件只记录可复现实测、实际摩擦和窄改进建议；既有候选的正式处置仍以 `docs/archive/m1b-adjudication.md` 为准。

本轮研究状态同时包含：

- 228 条 active Entry、46 条 superseded Entry；
- 26 条 unresolved failure；
- 新旧 ABACUS/LibRPA binary、远端 immutable run 和下游数值链；
- 一个被上游 PR #7804 推翻的生产公式判断；
- 同时更新的 `PROJECT_MEMORY.md`、JHEP note 和最终报告；
- 外部 goal 已明确，但 AITP `TOPIC.md` 仍保留 `Not established yet`。

因此，本轮主要检验的不是小型 clean store，而是 M1b-R1 在长期可变科研工作区中的信噪比。

## 2. 可复现实测

在同一 Topic 根目录，以 Python 3.12 调用 bundled CLI，得到：

| 命令 | exit | stdout | wall time |
|---|---:|---:|---:|
| `aitp check --json` | 1（存在 findings，符合契约） | 75,674 bytes | 0.407 s |
| `aitp check` | 1（存在 findings，符合契约） | 59,208 bytes | 0.384 s |
| `aitp enter --recent 20 --json` | 0 | 82,861 bytes | 0.303 s |
| `aitp enter --recent 20` | 0 | 4,348 bytes | 0.293 s |

`check` 共报告 199 errors、2 warnings：

- `hash_mismatch`: 162；
- `missing_ref`: 37；
- `empty_topic_goal`: 1 warning；
- `invalid_timestamp`: 1 warning。

199 个 ref errors 只涉及 91 个不同 target，说明明细中存在大量重复目标。最高频目标包括：

- `PROJECT_MEMORY.md`: 17 次；
- `symmetry/jhep-note/main.tex`: 9 次；
- `symmetry/jhep-note/main.pdf`: 8 次；
- 一个持续演化的 GW harness 源文件：8 次；
- 一个持续演化的 merge audit：8 次。

`enter` 的当前结构信号是：

- `memory_status = available`；
- `active = 228`，`omitted_active = 208`；
- `unresolved_failures = 26`；
- `latest_working_note = null`；
- handoff 仍指向 2026-08-11 的 jobs 1355/1358/1375/1379/1380，而当前工作已经进入 2026-08-13 的 PR #7804 修复与 Dongfang 最终 binary 构建；
- 最近的新 failure 已触发结构性的 handoff review 信号；
- `counts.malformed = 0`，但 warnings 中仍有一条 `invalid_timestamp`。两者按实现可以有不同含义，但对普通使用者不够直观。

## 3. M1b-R1 已经解决的问题

### 3.1 Compact `enter` 的改进是实质性的

同一数据下，text 输出约 4.3 KiB，而 JSON 约 82.9 KiB。人类定向不再被完整 Entry body 淹没，机器接口也没有被削弱。`recent_entries shown/active/omitted`、working Note 年龄、goal 和 handoff review 提示都能在短输出里出现。

### 3.2 `check` 暴露了以前不可见的整库债务

旧反馈只能看到一条非法 timestamp；现在一次只读扫描即可发现：

- 漂移的 SHA pin；
- 已不存在的 artifact；
- 未建立的 Topic goal；
- 非法 timestamp；
- Entry/Note 与当前文件系统之间的完整 ref 健康状态。

这说明选择 read-side slice 是合理的。当前瓶颈已从“没有诊断入口”转变为“诊断结果怎样可操作地呈现和预防”。

### 3.3 运行成本不是当前问题

在 274 条 Entry、3 条 Note 的实际 store 上，`check` 和 `enter` 都低于 0.5 秒。本轮没有证据支持数据库、持久索引、daemon、MCP server 或向量检索。

## 4. 当前最主要的问题

### 4.1 最大问题不是 store 损坏，而是把可变 canonical 文件当成长期 SHA pin

`PROJECT_MEMORY.md`、`main.tex`、`main.pdf`、持续修改的 harness 和 audit 文件本来就会演化。历史 Entry 若直接 pin 这些 canonical 路径的旧 SHA，下一次正常编辑就必然产生 `hash_mismatch`。因此，162 条 mismatch 中相当一部分不是一次性的文件损坏，而是**证据生命周期与 pin 类型不匹配**。

当前 Skill 已要求对“可能变化的证据”使用 pin，但没有足够醒目地区分：

- **immutable evidence**：可以直接 `sha256:` pin；
- **mutable canonical artifact**：不应让历史 Entry 依赖其未来仍保持旧 SHA；
- **versioned source state**：更适合 `git:` commit/blob pin；
- **阶段快照**：应先复制到 immutable provenance/snapshot 文件，再 pin snapshot；
- **持续更新的综合文档**：正文可引用其位置，但若要做强证据，应 pin 该时点的 immutable manifest 或版本化 commit，而不是当前工作副本。

这是本轮最值得立即修正的 Skill 规则。否则 `check` 越准确，长期 Topic 的错误数越会随正常工作单调增长。

### 4.2 `check` 明细完整，但对重复 ref failure 的人类信噪比偏低

59 KiB text 输出对于自动审计是可接受的，但人工处理 199 条明细时，首先需要知道“哪些 target 造成了最多 Entry 失效”。当前一个 target 被 17 条历史 Entry 引用，就打印 17 条独立 finding；这保证了精确性，却掩盖了修复优先级。

窄改进方向可以是：

1. 保持 `check --json` v0.1 的逐 finding 精确输出不变；
2. 人类 text renderer 先打印按 `(code, target)` 聚合的摘要，如 occurrences、涉及 Entry 数和前几个 Entry ID；
3. 仍允许查看完整明细，不引入持久索引或自动修复；
4. 若不能在既有 envelope 内兼容完成，则等待新的 reviewed version，而不是静默改 JSON schema。

这是一项显示层需求，不是新的语义判断。

### 4.3 `check` exit 1 在通用 shell/agent 工具中容易被误判为“命令执行失败”

契约明确规定 exit 1 表示“检查成功且有 findings”，但通用 Bash 包装器通常把任意非零退出显示为失败。Skill 已写明应解析 exits 0/1，不过缺少一个可直接复制的 shell 示例。实际 agent 若写：

```bash
aitp check --json
```

可能在还没读取 JSON 前就按 shell failure 分支处理。

无需改 runtime；在 Skill/README 补一个 fail-closed 示例即可：保存 stdout，捕获 rc，只在 rc > 1 时视为 cannot-run，然后解析 0/1 的报告。

### 4.4 Handoff review 能指出“需要复核”，但无法提供当前结论

M1b-R1 正确发现 2026-08-11 handoff 早于 2026-08-13 unresolved failure；这比静默显示旧 handoff 好。但它只能告诉使用者“旧了”，不能替代当前综合结论。根因仍是：

- dense campaign 没有及时写新 closeout；
- 3 条现有 theory Note 不等于 current-state working Note；
- `latest_working_note = null`；
- 228 条 active Entry 中，返回会话必须依赖 `rg`、`show` 和外部 handoff 才能重建 critical path。

不建议 runtime 自动生成语义 handoff。更现实的优化是加强 Skill：当 `handoff_status: review` 且 `latest_working_note = None` 时，在本次恢复完成后把“写一条 current-state working Note 或新 closeout”列为明确收尾动作，而不是软性建议。

### 4.5 外部 goal 与 Topic goal 双轨，当前没有自然同步点

本轮 host goal 很明确：在 Dongfang 完成四材料 ABACUS/LibRPA 验证并产出 PDF；但 AITP `TOPIC.md` 仍显示 `Not established yet`，因此 `enter`/`check` 持续诚实地报告 goal 未建立。

不建议 AITP 自动读取某个特定 agent host 的 goal，也不应引入平台耦合。可行的 Skill 改进是：

- 在已有明确、长期且经研究者确认的目标时，提醒操作者一次性补写 Topic goal；
- 明确 Topic goal 是研究主题的持久目标，不等同于某个 session/task 的临时目标；
- 若当前 CLI 没有安全更新 Topic 元数据的入口，先给出受审查的手工流程，未来再依据自然需求决定是否需要窄命令。

### 4.6 `malformed = 0` 与 `invalid_timestamp` warning 同时出现，术语容易误读

实现上可能是在区分“无法解析的 record”与“可解析但字段异常的 record”。但普通使用者会把 invalid timestamp 也理解为 malformed。建议只改文档或 text label，明确：

- `malformed` 计数覆盖什么；
- warnings 中的 field-level validity finding 是否计入该数；
- 为什么两者可以同时为 0 和非空。

本轮没有证据要求改变 JSON 语义。

### 4.7 Remote pointer manifest 仍然有真实需求，但当前文档示例已足够继续工作

本轮仍需在 remote immutable run、本地 provenance、AITP Entry、`PROJECT_MEMORY.md` 和论文之间重复搬运身份信息。现有 Skill 已加入 pointer-manifest 非规范示例，确实减少了“裸 remote path 被误当成 pin”的风险。

当前新增证据支持继续观察 roster D，但不支持立即实现新 runtime/schema。优先级仍低于修正 mutable-target pin 纪律，因为后者已经造成 162 条可见 mismatch。

## 5. 建议的最小优化顺序

### 5.1 立即修改 Skill/文档，不改 runtime

1. 新增“证据生命周期与 pin 选择”小节：
   - immutable snapshot / manifest → `sha256:`；
   - tracked evolving source → `git:`；
   - mutable canonical note/memory/report → 先快照或 pin commit，不直接长期 pin 当前工作副本；
   - remote run → 本地 immutable pointer manifest + SHA。
2. 为 `check` exit 0/1/2 给出可复制的 shell 解析范式，防止通用工具把 exit 1 当运行失败。
3. 当 `handoff_status: review` 且无 working Note 时，把“补 current-state working Note/closeout”升级为明确的 session 收尾检查。
4. 解释 `malformed` 计数与 field-level warnings 的差别。
5. 明确 Topic durable goal 与 host/session goal 的区别，并给出一次性建立 goal 的流程。

### 5.2 下一次 reviewed slice 再考虑

1. 为 `check` text view 增加按 `(code, target)` 聚合的人类摘要；JSON 完整 findings 保持不变或使用新版本 envelope。
2. 可选的 `--summary` / `--group-by-target` 只读显示模式；不缓存、不修复、不改 store。
3. 若更多自然 session 仍显示因果链恢复困难，再复核窄 relations/lineage read view；本轮不新增授权。

### 5.3 不建议

- 自动重写旧 Entry 的 SHA；
- 将所有 mismatch 降级为 warning；
- 允许裸 remote path 充当 evidence pin；
- 自动判断某个 failure 是否仍在 critical path；
- 自动从 host goal 改写 Topic goal；
- 引入数据库、向量搜索、持久索引、daemon 或 MCP server。

## 6. 对当前候选的更新判断

| 候选 | 本轮新增自然证据 | 建议 |
|---|---|---|
| `check` 后续显示优化 | 199 ref errors / 91 targets，text 59 KiB，重复目标明显 | 值得形成窄 read-side 候选；先文档化，后续 reviewed slice 决定 |
| mutable evidence pin 纪律 | 162 hash mismatch，多个最高频目标是正常演化文件 | 立即改 Skill/文档；不需要 runtime |
| roster D pointer bundle | 双远端 provenance 仍重复 | 保持 deferred；现有非规范 manifest 示例先继续使用 |
| relations/lineage | stale handoff 仍需人工 `rg` + `show` 重建 | 保持 deferred；先补 working Note/closeout 纪律 |
| structured prepare | 本轮主要摩擦在证据生命周期，不在 draft 填写 | 保持 deferred |
| quick record | 没有新的独立 session 证据 | 保持 deferred |
| 数据库/索引/语义搜索 | `check`/`enter` 均 <0.5 s，`rg` + `show` 仍可工作 | 不需要 |

## 7. 可直接执行的优化 Prompt

> 请在 AITP Research Protocol 仓库中，基于 `feedback/2026-08-13-gw-librpa-m1b-r1-natural-use-feedback.md` 做一个**仅 Skill/文档层**的最小修订，不改变 CLI、schema、stage status 或任何 archived spec/adjudication。重点补充：
> 1. 证据生命周期与 pin 选择规则：immutable snapshot 用 `sha256:`，演化中的 tracked source 用 `git:`，mutable canonical note/memory/report 必须先快照或 pin commit，remote run 用本地 immutable pointer manifest；
> 2. `aitp check` exit 0/1/2 的 fail-closed shell 示例，明确 exit 1 是成功生成 findings；
> 3. `handoff_status: review` 且无 working Note 时的明确收尾检查；
> 4. `malformed` 计数与 field-level warning 的术语说明；
> 5. Topic durable goal 与 host/session goal 的边界和一次性建立流程。
> 保持 runtime 简单，不增加 search、index、daemon、MCP、自动 repair 或自动语义判断。修改前检查当前 branch、dirty worktree 和适用 `AGENTS.md`；保留现有未跟踪文件，不提交、不 push；完成后运行相关文档/Skill 一致性检查并给出精确 diff 与验证结果。

## 8. 总结

M1b-R1 已解决“无法整库诊断”和“`enter` 文本过长”两个真实问题；性能也足够。现在暴露出的首要问题是**证据生命周期纪律**：历史 Entry 直接 SHA-pin 持续演化的 canonical 文件，使正常科研编辑被准确但高噪声地报告为 162 条 mismatch。最小、最有效的下一步不是扩大 runtime，而是先把 pin 选择、`check` exit 解析、working Note/closeout 和 goal 双轨边界写清楚。之后若多个独立自然 session 仍出现 199 条级别的重复 finding，再考虑只改人类 text view 的分组摘要。
