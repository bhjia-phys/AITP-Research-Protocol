# Power-law Heisenberg / Yangian 课题中的 AITP 自然使用反馈

日期：2026-08-12
使用者：Kimi Code，配合研究者复核 SU(2) × D_L 分块下的能谱统计，并维护 Yangian 研究执行手册
Topic：`/home/bhjia/physics/quantum_chaos/Power_Law_Heisenberg_Chain`（`.aitp/topic/`）
协议版本：当前 M1a 命令面，`enter-0.2` / `list-0.1` / `show-0.1`

## 1. 反馈边界

这不是 AITP 与 plain files 的对照实验，不是 M1b gate review，也不是 freeze revision。它来自一次真实研究纠错：已有 spectral-spacing-v2 closeout 宣称产物链完成后，研究者继续追问每个 level-spacing 样本数是否与声明的 SU(2) × D_L 对称扇区一致。复核既确认了主 `P(s)` 样本，也发现并修正了一个 headline/all-S 报告口径错误。

本轮没有恢复暂停中的 full-alpha quotient-algebra goal，没有重启冻结的 Stage II.2 optimizer/formal grid，也没有读取 legacy corpus。所有当前仓库的计算、validator、测试、生成器和文档构建均由仓库内 Fish 3.3.1 `--no-config` 启动，使用 `.venv` Python，并固定 BLAS/OpenMP 线程为一。

## 2. 实际事件链

真实使用过程不是“记录一个成功结果”，而是对既有 closeout 的挑战与纠错：

1. 原 result/closeout 已记录 L=16 的 SU(2) × D_L spectral-spacing promotion，并声称 generic 点的主样本为 31 个 accepted headline blocks、2829 个 unfolded spacings；
2. 研究者质疑对称性约束下的 level-spacing 数量；
3. 独立 representation-theory/per-block 审计确认 `31/2829` 正确，但发现报告和 preview 将 all-S 的 raw zero/invalid 计数 `2768/1922` 放在了标为 `S=0,1,2` 的 headline 行；
4. AITP 写入 failure Entry `entry-bf042d6bafc94f41a0ba273179b75482`，明确把“主 `P(s)` 数量正确”与“诊断标签错误”拆开；
5. `aitp show` 用于精确恢复 failure 的 claim、limitations、refs 和 next action；
6. 报告代码改为强制显式选择 `primary` 或 `all`，并走 no-ED/no-unfolding-generation republication；
7. 双重 replay 和独立 scope audit 验证：headline alpha=2 为 `1998` zero gaps、`1448` invalid ratios、`1214` valid ratios；all-S 仍为 `2768/1922`；完整 results tree 和正式 `P(s)` SVG 不变；
8. 修复经测试、Witten 风格执行手册、live status、canonical PDF/source archive 同步后，用一条 resolving record 关闭 failure，再写新的 closeout；旧 result 和旧 closeout 均不改写。

这里最重要的科学边界是：这是 reporting-scope correction，不是新物理结果。它不改变 spectrum、block selection、raw ratio、unfolded spacing、bootstrap density 或任何 Poisson/GOE 距离，也不产生 integrability、chaos、ETH 或热力学分类。

## 3. 真正有帮助的地方

### 3.1 `enter` 在中断恢复时暴露了未关闭失败

`aitp enter --recent 5` 同时显示旧 closeout handoff 与 `unresolved_failures=1`。这阻止了 agent 仅凭“已有 closeout”把课题误判为完全收尾，也清楚表明当前修复尚未形成 resolving record。

`memory_status=available`、`omitted_active` 和 Note-age 信号仍只是 ledger 结构状态，不自动等于科学真理；真正的计数必须回到 HDF5、代码和独立审计。

### 3.2 `show` 适合打开被挑战的 exact failure

对 `entry-bf042d6bafc94f41a0ba273179b75482` 使用 `aitp show`，比从 `enter` 的摘要或直接猜测 Markdown 字段更可靠。它精确恢复了：

- failure 的局部范围；
- 原 HDF5、脚本、报告和 count-audit 的 hash pins；
- “不改变 eigenvalue / accepted block / unfolded spacing / 31/2829”的限制；
- 修复后应执行的具体 next action。

### 3.3 append-only failure 保留了纠错的时间顺序

原 result Entry 中的主 claim 大部分仍然成立，因此静默改写或整体 supersede 都不合适。先写 failure、修复后以新证据 resolve，保留了以下顺序：

```text
旧 result/closeout
  -> 研究者质疑
  -> 独立审计确认主样本但发现局部 scope bug
  -> failure Entry
  -> no-generation repair + replay + full validation
  -> resolving code-change/result
  -> new closeout
```

这种 append-only 结构比覆盖旧报告摘要更能防止“旧记录从未出错”的假象。

### 3.4 refs + SHA 固定了 metadata republication 的证据链

本轮 HDF5 hash 因 provenance metadata republication 而变化，但完整 `results` tree hash 前后相同，正式 `P(s)` SVG 也字节不变。AITP refs 适合 pin：

- 旧 HDF5 与旧审计；
- 修复后的脚本、HDF5、summary、figures 和 report；
- independent replay JSON；
- scope-fix audit JSON；
- full-suite machine record；
- execution-note TeX/PDF/source zip。

HDF5、PDF 和 zip 的内容不应该复制进 ledger；Entry 作为 coarse durable index 足够有效。

### 3.5 limitations 有效阻止把注释错误升级成物理结果

failure 与 resolving record 都可以明确写出：

- `31/2829` 从未被推翻；
- `2768/1922` 不是错误数值，而是错误地被标为 headline；
- alpha=2 的 headline `P(s)` 仍 unavailable；
- 没有任何物理分类变化。

这类局部纠错很容易在普通“修复完成”摘要中被夸大，而结构化 limitations 能持续约束后续会话。

### 3.6 closeout-first 在新 closeout 存在时有效

旧 closeout 仍提供过时 handoff，是因为 failure 之后尚未写新的 closeout，而不是 `enter-0.2` 排序失效。修复完成后追加新 closeout，就能让下一次 `enter` 恢复到“展示修正后的图；只在研究者明确要求后恢复 general quotient-algebra goal”的真实边界。

## 4. 最不顺手的地方

### 4.1 活跃 failure 不会覆盖旧 closeout 的 handoff

本轮 `enter` 的 `next_action` 仍来自旧 closeout，即使更新、更相关的 active failure 已存在。结构上这是既定的 closeout-first 规则；语义上，恢复者必须同时阅读 `unresolved_failures` 才能知道 handoff 已被挑战。

这不是足够强的 runtime 缺陷证据。更合适的 Skill 纪律是：挑战既有 closeout 时立刻写 failure；修复后 resolve，并写新的 closeout。不要等到后续会话从旧 handoff 猜测当前状态。

### 4.2 缺少窄的 `based_on` 关系

resolving record 实际同时依赖：

- 原 spectral result；
- 原 closeout；
- 后来的 failure；
- 新 scope audit 与 replay。

`resolves` 很适合关闭 failure，`supersedes` 不适合，因为主 result 仍成立；`refs` 适合 pin 文件，但不表达 Entry-to-Entry 的“本修复基于哪些记录”。这些依赖只能写进正文或把 Entry 文件本身作为 refs。

这给 roster B 的窄 `based_on` 提供了真实需求：只表达显式依赖，并允许 derived reverse view；不需要通用 graph database、自动推理或新索引。证据真实但范围很窄，仍应等待正式 natural-use adjudication。

### 4.3 局部更正难以表达为“主 claim 保留、局部说明被纠正”

旧 result Entry 中 `31/2829` 的核心结论仍成立，但其关联报告曾含 `2768/1922` 的 headline 误标。resolver 可以关闭 failure，却不能直接表达“旧 result 的一个局部说明被更正，而主 claim 继续 active”。整体 `supersedes` 又过重。

这可能支持更清晰的 correction discipline，或与窄 `based_on` 一起表达修复链；不应让 runtime 自动判断或重写旧 record 的语义。

### 4.4 prepare → edit → save 对本次高价值纠错可接受

本轮只有一条 failure、一条 resolving record 和一条 closeout，且都需要精确 refs、hash 和 limitations。完整 draft 流程的摩擦与事件价值相称，没有形成 `record quick` 的强需求。

### 4.5 working Note 的软提示需要语义判断

`enter` 显示 latest working Note 很旧，且其后有许多 active Entries。但本轮是一条短、证据清晰的修复链；执行手册和 second audit 已承担面向研究者的综合，不值得为 ledger 再复制一份 working Note。

因此 Note-age 信号有提醒价值，但不能机械地以 active Entry 数量触发 Note。是否写 Note仍应由 Skill 根据结论链复杂度和已有综合文档判断。

### 4.6 本轮没有支持其他 runtime 扩张

- AITP 当前没有 `check`，本轮 store 健康且 `warnings=[]`，没有为 roster A 增加新的强证据；
- 这是本地计算，没有 remote pointer bundle 需求，不支持 roster D；
- 没有 prediction/question typed-item 需求，不支持 roster C；
- 没有文献源工作流需求，不支持 roster G；
- stale handoff 的根因是新 closeout 尚未写入，不支持恢复 roster H。

## 5. 对 A–H roster 的自然使用判断

本表是自然使用反馈，不修改 freeze disposition。

| ID | 本次自然需求 | 暂定判断 |
|---|---|---|
| A — read-only `check` | 无新增强证据；`enter` 健康且无 warning | 继续 deferred |
| B — `based_on` / `used_by` | 有窄而真实的需求：repair 同时基于旧 result/closeout/failure，只能在正文/refs 表达 | 继续 deferred，优先级低于 GW/LibRPA 反馈中的 D；等待正式自然使用 review |
| C — typed open items | failure/result/closeout 已足够表达本轮链条 | 继续 deferred |
| D — remote pointer bundle / run templates | 本轮完全本地，无需求 | 本轮不支持；不改变既有候选判断 |
| E — quick record | 三条高价值记录适合完整 prepare/edit/save | 本轮不支持，继续 deferred |
| F — collaborator Skill | 问题属于现有 Skill 的 closeout/correction 纪律 | 保持 moved to M4 |
| G — literature/source Skills | 本轮未做文献检索或 source adjudication | 保持 independent/deferred |
| H — next-action relation | 旧 handoff 源于尚未写新 closeout，closeout-first 本身工作正常 | 继续 dropped，不恢复 runtime |

## 6. 建议的最小改进

无需 runtime 变化，建议在 `using-aitp` Skill 的纠错纪律中明确一句：

> 当研究者挑战既有 result/closeout 时，先写一条范围精确的 failure；修复后用直接证据 resolve，并写新的 closeout；不得为制造“干净历史”而修改旧 result。若主 claim 保留而只有局部说明更正，应在 failure/resolver 的 limitations 中明确这一区分。

这条建议足以覆盖本轮最关键的自然摩擦。是否选择 roster B 的窄 `based_on`，仍应等待正式 review；本反馈不授权任何 schema、CLI、runtime、roadmap 或 freeze 变更。

## 7. 总结

本轮 AITP 最有价值的作用，是把一个容易混成“谱统计做错了”的质疑拆成两个可审计事实：主 `P(s)` 样本 `31/2829` 正确，而 `2768/1922` 是数值正确但 scope 标签错误的 all-S 诊断。failure Entry 保留了挑战，refs/hash 固定了 no-generation republication 和结果树不变的证据，limitations 防止纠错被写成新物理结论，resolves + new closeout 则恢复了诚实 handoff。

这份证据支持继续使用当前 M1a 和改进 Skill 纪律，不支持立即扩张 runtime 或修改 M1b freeze。
