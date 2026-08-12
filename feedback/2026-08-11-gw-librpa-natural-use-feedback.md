# GW/LibRPA 长周期课题中的 AITP 自然使用反馈

日期：2026-08-11（反馈整理于后续连续工作回合）
使用者：Kimi Code，配合研究者进行 ABACUS/LibRPA SOC 磁群对称性开发与数值验证
Topic：`/home/bhjia/physics/GW_librpa`（`.aitp/topic/`）
协议版本：当前 M1a 命令面，`enter-0.2` / `list-0.1` / `show-0.1`

## 1. 反馈边界

这不是对 AITP 优于 plain files 的对照实验，也不是 M1b gate review。它来自一个真实、非脚本化、持续多天且包含大量中断/续接的研究 Topic，但仍主要属于同一个长会话链，不能替代路线图要求的至少两个普通自然使用 session。

本课题同时涉及：

- 两个本地源码仓库和多个 dirty worktree；
- fish 与 Dongfang 两套远端 Slurm 环境；
- 不可变运行目录、构建/二进制/输入 SHA、job dependency；
- ABACUS producer、RPA、G0W0、QSGW、JHEP note 和最终 PDF；
- 多次被新证据推翻的因果解释；
- “计算完成”“固定门槛通过”“物理结论成立”三个不同层次。

这使它很适合作为记忆恢复、失败保留、证据边界和长结论链的压力测试。

## 2. 实际使用方式

实际反复使用了以下流程：

1. 每次恢复研究工作时运行 `aitp enter --recent N`；
2. 对需要精确回看的记录使用 `aitp show <entry-id> --json`；
3. 用 `aitp list --since ... --json` 获取时间窗口投影；
4. 语义检索仍使用 `rg` 搜索 `.aitp/topic/`；
5. durable result/failure/decision/run 用 `record prepare` → 编辑 draft → `record save`；
6. 多条结论需要综合时使用或计划使用 working/theory Note；
7. 远端运行本身不进入 store，先在 workspace 内写 provenance/result 文档，再用相对路径与 SHA pin 作为 AITP `refs`。

本次整理时，`aitp enter --recent 8` 报告：

```text
active = 179
superseded = 41
unresolved_failures = 20
omitted_active = 171
latest_working_note = None
```

`aitp list --since 2026-08-08 --json` 输出约 94 KiB。`enter` 还持续报告一条历史记录的非法时间戳警告：

```text
.aitp/topic/entries/entry-97bec98c58634e21aecbba57a2bee48e.md
unparseable created_at: +now+
```

这些数字只描述 ledger 状态，不代表科学状态。

## 3. 真正有帮助的地方

### 3.1 强制区分证据、解释和限制

最有价值的不是“记住结果”，而是每条记录都要求把 `summary`、`refs`、`limitations`、`resolves`、`supersedes`、`next_action` 分开。

例如 Fe real-space reverse-route 修复记录 `entry-3939a7e7e432441cabe6fb8188e09317` 没有把三数量级改善写成最终 PASS，而是明确保留：

- job 1349 复用了旧 restart，不是 fresh publication pair；
- raw-state `max <= 1e-4 eV` 仍失败；
- 简并两态对角和只能提示 gauge residual，不能替代 full-operator proof。

这在长时间调试中非常重要。没有这种结构，阶段性改善很容易在后续摘要里被误写成“问题已解决”。

### 3.2 失败记录确实防止了重复踩坑

以下失败后来都被重新定位时，AITP 记录提供了明确边界：

- wheel filename tag 写反导致 fish build 在 materialization 前失败；
- `n_aos` 与 `n_aos*n_spinor` 完整空间 gate 错误；
- r11 修复 `V(q)->V(R)` ownership 后 Fe QP 结果不变，排除了一个看似合理的根因；
- producer 缺 `vxc_out.dat` 导致多个 campaign job 只能 preflight FAIL。

保留失败比只维护一份“当前正确方案”更有用，因为它让后续会话知道哪些方向已经有反证，以及反证适用于哪个 binary/commit。

### 3.3 `show` 比直接解析 Markdown 可靠

`aitp show` 返回 exact Entry、status、frontmatter、body 和 schema。对单条关键记录，它显著减少了手工判断 YAML/frontmatter 的错误，也比从 `enter` 截断摘要推断可靠。

### 3.4 `enter` 的结构化健康信号有用

`memory_status`、`omitted_active`、`unresolved_failures`、非法时间戳 warning、Note-age 信号都能快速暴露“当前投影不是完整 ledger”。它们阻止 agent 把 `recent_entries` 当成全部历史。

### 3.5 本地相对 ref + SHA 迫使远端证据先落地

远端 fish/Dongfang 路径不能直接作为可验证 pin，实际 workaround 是：

1. 从远端只读检查 immutable result；
2. 在 GW workspace 写本地 provenance/result 文档；
3. 将 remote path、job ID、binary SHA 写入正文；
4. AITP ref 指向该本地文档并附 `sha256:`。

这增加了工作量，但同时阻止了把一个裸 `host:path` 当成证据。这个约束在科研计算中是正确的。

## 4. 最不顺手的地方

### 4.1 `enter` 能恢复“ledger 状态”，但不能自动恢复“当前结论链”

179 条 active Entry 中，最近窗口只显示 8 条；`omitted_active=171` 正确提醒了遗漏，但 agent 仍需知道该搜索什么。当前 `next_action` 仍来自较早的 build job 1290 closeout，而实际工作已经推进到 jobs 1350–1370。原因不是 `enter` 排序错误，而是自然使用中没有持续写 closeout。

结果是：

- closeout-first 机制在存在新 closeout 时很好；
- 高频调试中每个阶段都写 closeout 的维护成本太高；
- 不写 closeout 时，结构正确但语义过时的 handoff 仍会被突出显示；
- `latest_working_note=None` 说明“相关 Entry 超过四条时应综合 Note”的 Skill 纪律没有自然发生。

这首先是 Skill/工作流问题，不一定需要新 runtime。

### 4.2 写入摩擦与科研事件密度不匹配

完整 `prepare → 打开 draft → 填完所有 prompt → save` 对最终 result/decision 很合适，但对连续 Slurm campaign 太重。

一次九体系 campaign 可能同时产生：

- 3 个运行中状态；
- 3 个 preflight failure；
- 4 个 rescue job；
- 4 个 dependent retry；
- 2 个阶段性 RPA 数值；
- 1 个 analyzer bug；
- 1 个新的物理失败。

如果每个都立即写 Entry，研究工作被记录动作淹没；如果批量等到最后，又容易遗漏 job/binary boundary。实际做法是先写一份本地 submission/result Markdown，再用一条 AITP `run` Entry 索引它。这种“coarse durable index”可用，但需要 Skill 明确推荐，而不是让 agent误以为每个 job 都应一条 Entry。

目前只有一次长 session 的自然证据，尚不足以支持 roster E 的 `record quick` runtime。

### 4.3 远端运行的双重记账成本很高

科学证据主要在 `/data/users/bhj/ai-runs/...`，AITP refs 又必须指向 Topic 内文件。为了做到可追溯，需要同时维护：

- remote immutable run；
- local provenance JSON/Markdown；
- AITP Entry；
- `PROJECT_MEMORY.md`；
- 有时还要更新 JHEP note。

这里最强的自然需求不是允许裸 remote path，而是 roster D 所描述的**本地 pointer bundle**：它应保存 remote location、source/build/job identity 和一份本地 hash manifest，同时明确“未重新验证远端字节”的边界。是否实现仍应等第二个自然 session 和正式 adjudication。

### 4.4 因果依赖只能埋在正文

一个可接受结果通常依赖：

```text
ABACUS merge commit
  -> producer job
  -> LibRPA patch stack
  -> build job
  -> numerical job
  -> read-only postprocess
  -> final report
```

现有 `refs` 适合证据 pin，`resolves`/`supersedes` 适合关闭或替换，但不适合表达“本结果基于哪个 build/run Entry”。实际只能在 body 中写 job IDs 和 entry IDs。

这给 roster B 的窄 `based_on` 提供了真实需求，但需求应限制在显式依赖，不应扩展成自动 graph/index；`rg` 和 derived projection 已足够做发现。

### 4.5 unresolved failure 计数真实但可操作性弱

`unresolved_failures=20` 很诚实，但包含：

- 仍然阻塞当前工作的科学失败；
- 已被新路线绕过、但没有直接 `resolves` 证据的历史失败；
- harness/build 失败，对当前最终 binary 已无直接影响；
- 需要保留但不值得优先处理的旧问题。

计数不能告诉 agent 哪些 failure 仍在当前 critical path。实际需要 `list`/`show` + `rg` + 人工判断。不要让 runtime 做语义优先级判断；更现实的改进是让 working Note 明确列出“current blockers”和所依据的 active failures。

### 4.6 store health warning 缺少独立、可复现的汇总入口

`enter` 已经暴露非法 `created_at`，因此问题不会静默。但若要系统检查 179 个 active/41 个 superseded records，只能依赖各命令的局部读取或测试代码。该经验给 roster A 的 read-only `check` 提供了一点自然需求，尤其是：

- malformed timestamp；
- dangling refs；
- missing target；
- invalid relation；
- projection 与源文件不一致。

但目前只有一个可见 warning，尚不足以证明必须新增命令；也可以先用现有 validator/test 和一次人工 repair 解决。

### 4.7 `list --since` 对密集 Topic 仍然偏大

四天窗口已经约 94 KiB。`--kind` 有帮助，但缺少 subject/critical-path 语义，而 runtime 也不应尝试语义搜索。当前最佳实践仍是：

- `enter --recent N` 做 orientation；
- `rg` 找主题；
- `show` 打开精确记录；
- 必要时 `list --kind/--since` 做时间或类型投影。

因此没有证据支持数据库、向量搜索或新索引。

## 5. 维护成本

### 5.1 正向成本

- append-only 使得旧结论被推翻时不需要改写历史；
- idempotency key 防止同一逻辑事件重复保存；
- refs 与 limitations 让最终报告可以追溯到 exact result 文档；
- `show` 和 versioned JSON 降低了 agent 集成歧义。

### 5.2 负向成本

- Entry、local result、PROJECT_MEMORY 和论文 note 存在重复；
- 记录 save 前必须确保 workspace-relative ref 和 SHA，远端任务尤其繁琐；
- 关系维护全靠 agent 纪律，容易漏 `resolves`/`supersedes`/closeout；
- dense campaign 中，“何时记录”比“怎么记录”更难；
- 当前 store 已出现一个非法 timestamp 历史 warning，说明直接手写/旧工具路径仍会留下维护债务。

## 6. 对 A–H roster 的自然使用判断

这只是第一份自然反馈，不是 freeze revision。

| ID | 本次自然需求 | 暂定判断 |
|---|---|---|
| A — read-only `check` | 有轻度需求：长期存在 invalid timestamp warning，store 较大 | 继续 deferred；第二个 session 若再次需要整库健康审计，再考虑最小只读 slice |
| B — `based_on` / `used_by` | 有明确需求：producer→build→run→postprocess 依赖只能写正文 | 候选中优先级较高；只考虑显式 `based_on` 与 derived reverse view，不做 graph/index |
| C — typed open items | 当前主要使用 failure/result/decision 已能表达；问题更多是 critical-path synthesis | 继续 deferred |
| D — remote pointer bundle / run templates | 有最强需求：remote immutable evidence 造成重复 provenance 搬运 | 候选中优先级最高，但仍需第二个自然 session 与独立 spec/gate |
| E — quick record | 写入摩擦真实，但只有一个长 session，且 coarse local report + one Entry workaround 可用 | 继续 deferred，不足四个自然 session |
| F — collaborator Skill | 本次问题是现有 Skill 纪律未持续执行，不是缺少新 agent framework | 保持 moved to M4 |
| G — literature/source Skills | 本轮主要是代码和数值取证，没有形成新的独立需求 | 保持 independent/deferred |
| H — next-action relation | stale handoff 的直接原因是没写新 closeout；现有 closeout-first 机制本身可用 | 不恢复 runtime；先改进 closeout/working-Note 使用纪律 |

## 7. 建议的最小改进顺序

### 7.1 立即可做、无需 runtime 变化

1. 在 `using-aitp` Skill 中更明确写出 dense campaign 的推荐粒度：
   - 多个同一目的 job 先落一份 local immutable submission/result report；
   - AITP 用一条 `run`/`result` 索引 durable campaign moment；
   - transient queue snapshot 不单独记录。
2. 把“何时写 working Note”从软提示变成更具体的自然工作检查：
   - 同一因果链出现 4+ active Entries；或
   - `enter` 显示 `latest_working_note=None` 且近期存在多条互相依赖记录；或
   - 研究者问“最近结论到底是什么”。
3. 在 session closeout 中明确核对 `next_action` 是否已经落后于最新 active result；若落后，写一条真正的 closeout，而不是改旧记录。
4. 提供一个文档化的 remote evidence pointer manifest 示例，但暂不新增 schema/runtime。
5. 修复现有非法 `created_at: +now+` 记录时保留审计轨迹，不静默改写；该修复应独立于本反馈。

### 7.2 需要第二个自然 session 后再 adjudicate

优先复核：

1. D：最小 local remote-run pointer bundle；
2. B：可选 `based_on` + derived `used_by`；
3. A：只读 store health report。

仍不建议：数据库、向量搜索、daemon、自动语义结论、自动修改 relation、通用 quick-write shortcut。

## 8. 总结

AITP 在这个课题中最成功的部分是**防止过度宣称**：它迫使每个 binary-specific 数值结论带着 limitation 和 pin 生存，也保留了失败路线。最失败的部分不是读取命令，而是自然工作中的维护节奏：Entry 很多、closeout 和 working Note 不够及时，导致 `enter` 的结构投影正确但 handoff 语义过时。

当前证据支持继续使用 M1a，而不是立即扩张整个 M1b。若第二个普通 session 复现同样痛点，最值得进入正式 adjudication 的是窄 D、窄 B，随后才是 A；其余候选继续 defer/move/drop 是合理结果。
