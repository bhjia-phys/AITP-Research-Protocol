---
title: Witten-Perspective AITP Knowledge Architecture Design
date: 2026-04-24
status: draft
scope: study mode + L2 knowledge graph + quality assurance
---

# Witten 视角下的 AITP 知识体系设计

> 从理论物理学认识论出发，重新审视如何让 AI 从知识库中变得真正可靠和富含智慧。

## 一、认识论基础：物理学知识的真实结构

物理学不是事实的集合，而是一座有效场论塔（EFT Tower）。从顶级理论物理学家的视角看：

1. **每一层理论都有明确的适用范围（regime of validity）。** QCD 在 Lambda_QCD 以上适用，Fermi 理论在 m_W 以下适用。一个没有标注 regime 的结果比没有结果更危险——它会误导。

2. **理论之间由对应原理连接。** 新理论必须在旧理论的有效范围内退化为旧理论。这不是可选的——这是物理学的宪法。相对论力学在 v/c -> 0 时退化为牛顿力学，QFT 在 hbar -> 0 时退化为经典场论。

3. **推导是变换的链条。** 每一步都有明确的理由类型：定义、定理、近似、物理原理。断了一步，整个链条就断了。

4. **开放问题和已解决结果同样有价值。** 每个理论都有"边界问题"——在其适用范围边缘的问题指向更深层理论。知道什么不知道比知道什么同样重要。

5. **数学是语言，不是内容。** 一个概念没有数学表达是不完整的，但数学没有物理意义是空洞的。两者都必须被捕获。

### EFT 塔结构示意

```
EFT Tower (by energy/length scale)
├── Classical Mechanics (v << c, hbar -> 0)
│   ├── concepts: [Newton's laws, Lagrangian, Hamiltonian, ...]
│   ├── results: [Kepler orbits, normal modes, ...]
│   └── correspondence -> QM (hbar correction), GR (c^-2 correction)
├── Special Relativity (v -> c, hbar -> 0)
│   └── correspondence -> GR (curved spacetime), QFT (particle creation)
├── Quantum Mechanics (v << c, hbar finite)
│   └── correspondence -> QFT (relativistic), Classical (hbar -> 0)
├── Quantum Field Theory (v -> c, hbar finite)
│   ├── QED (alpha << 1)
│   ├── QCD (confinement / asymptotic freedom)
│   └── Electroweak theory
├── Standard Model (SU(3) x SU(2) x U(1))
│   └── open question: strong CP problem, neutrino masses, hierarchy problem
└── BSM candidates
    ├── SUSY, String Theory, ...
    └── correspondence -> SM at accessible energies
```

## 二、L2 知识图谱设计

### 2.1 当前状态

当前 L2 是 `candidates/*.md` 的平面列表，只有 `(trust_basis, trust_scope)` 二维信任模型，缺少：
- 节点之间的结构化关系（边）
- 理论适用范围的显式标注
- 对应原理的系统性记录
- EFT 层级结构

### 2.2 节点类型

```python
NODE_TYPES = [
    "concept",          # 原子概念（如：Sagnac effect, Berry phase）
    "theorem",          # 已证明的定理（如：CPT theorem, Noether's theorem）
    "technique",        # 技术方法（如：Borel resummation, heat kernel expansion）
    "derivation_chain", # 推导链（有序步骤序列，每步带 justification_type）
    "result",           # 具体结果（如：anomalous magnetic moment to 3-loop）
    "approximation",    # 近似关系（如：WKB, saddle-point）
    "open_question",    # 开放问题（如：strong CP problem）
    "regime_boundary",  # 理论适用范围边界（如：Planck scale, Lambda_QCD）
]
```

### 2.3 边关系类型

```python
EDGE_TYPES = [
    # 核心物理关系
    "limits_to",          # A -> B 在某极限下退化为 B（对应原理）
    "specializes",        # A 是 B 在特定条件下的特化
    "generalizes",        # A 是 B 的一般化
    "approximates",       # A 近似于 B（带误差估计）

    # 逻辑依赖
    "derives_from",       # A 可以从 B 推导出来
    "proven_by",          # A 的证明依赖于 B
    "assumes",            # A 假设了 B
    "uses",               # A 使用了 B 作为工具

    # 结构关系
    "component_of",       # A 是 B 的组成部分
    "equivalent_to",      # A 和 B 在数学上等价（不同表述）
    "contradicts",        # A 与 B 矛盾（需要标注是否 resolved）

    # EFT 塔特有关系
    "matches_onto",       # EFT 匹配关系（高能 -> 低能的系数匹配）
    "decouples_at",       # A 在某个能标处退耦
    "emerges_from",       # A 从 B 中涌现（如超导 from BCS）

    # 研究关系
    "refines",            # A 细化了 B 的结果
    "motivates",          # A 的存在推动了 B 的研究
]
```

### 2.4 图谱目录结构

```
L2/
├── index.md                    # 全局索引
├── log.md                      # 提升历史
├── graph/
│   ├── nodes/
│   │   └── <node_id>.md        # 节点文件（带 regime_of_validity）
│   ├── edges/
│   │   └── <edge_id>.md        # 边文件（from, to, type, evidence）
│   └── towers/
│       ├── <tower_id>.md       # EFT 塔定义（能量尺度范围 + 包含节点）
│       └── correspondence.md   # 对应原理记录（哪些极限关系已验证）
├── candidates/                 # 向后兼容：提升前的候选者暂存
├── conflicts/
│   └── <conflict_id>.md        # 冲突记录
└── queries/
    └── cached/                  # 缓存的高频查询结果
```

### 2.5 节点文件格式

```yaml
---
node_id: sagnac-effect
type: concept
regime_of_validity: "rotating frame, non-inertial coordinates"
tower: classical-optics
trust_basis: validated
trust_scope: bounded_reusable
version: 2
aliases: [Sagnac interference, rotating interferometer]
mathematical_expression: "Delta_phi = 8*pi*A*Omega/(c*lambda)"
units: "dimensionless (phase shift)"
provenance:
  source: "source_id from L0"
  promoted_date: "2026-04-24"
  validation_outcome: pass
---
```

Body sections:
- Physical Meaning（物理本质，用自己的语言）
- Mathematical Expression（公式 + 符号约定）
- Derivation Chain（指向 derivation_chain 节点）
- Regime and Limits（适用范围 + 极限行为）
- Open Questions（如果有）

### 2.6 边文件格式

```yaml
---
edge_id: qed-limits-to-classical-ed
type: limits_to
from_node: qed-maxwell-equations
to_node: classical-electrodynamics
evidence:
  - "perturbative expansion in alpha -> 0"
  - "single-photon exchange approximation"
regime_condition: "alpha << 1, single-particle limit, hbar -> 0"
correspondence_verified: true
verified_by: "L4 review ID"
---
```

### 2.7 EFT 塔文件格式

```yaml
---
tower_id: standard-model-tower
name: "Standard Model Effective Field Theory Tower"
energy_range: "0 - ~1 TeV (directly probed)"
layers:
  - id: classical-mechanics
    energy_scale: "< eV"
    theories: [newtonian-mechanics, classical-em]
  - id: quantum-mechanics
    energy_scale: "eV - keV"
    theories: [nonrelativistic-qm]
  - id: qed
    energy_scale: "keV - GeV"
    theories: [qed-perturbative]
  - id: standard-model
    energy_scale: "GeV - TeV"
    theories: [sm-gauge-sector, qcd, ew-theory]
correspondence_links:
  - from: qed
    to: classical-em
    limit: "alpha -> 0, hbar -> 0"
    verified: true
  - from: qcd-low-energy
    to: nuclear-physics
    limit: "Lambda_QCD matching"
    verified: false
    note: "lattice QCD ongoing"
---
```

## 三、学习模式设计

### 3.1 核心理念

顶级物理学家读论文的方式不是"读懂了"，而是"我能在黑板上重建它"。学习模式映射到这个过程：

```
物理学家读论文的实际过程:
  1. 这篇文章声称了什么？         -> source_decompose
  2. 每一步推导我怎么验证？       -> step_derive
  3. 我发现了什么隐藏假设和缺口？ -> gap_audit
  4. 我能用自己的框架重建吗？     -> synthesis

学习子平面:
  source_decompose -> step_derive -> gap_audit -> synthesis
```

### 3.2 学习模式子平面详解

#### source_decompose（源分解）

**目的**：把论文分解为原子声明。

- 每个声明标注：
  - `origin`: 是否直接来自原文
  - `independently_verifiable`: 是否可独立验证
  - `prerequisites`: 依赖什么前置知识（指向 L2 节点）
  - `claim_type`: definition | theorem | approximation | physical_principle | numerical_result | conjecture
- 输出：`active_decomposition.md`

**关键原则**：不是摘抄，而是用自己的语言重述每一个原子声明。如果不能用简单语言重述，说明理解不够。这是 Feynman 方法的核心。

**与 L2 的关系**：每个原子声明确认 L2 中是否已有对应节点。如果已有，标注为 `confirmed_existing`。如果没有，标注为 `new_to_l2`。

#### step_derive（逐步推导）

**目的**：对每个推导链，逐步追踪并显式标注每一步。

每一步标注：
- `justification_type`: definition | theorem | approximation | physical_principle | algebraic_identity | limit | assumption
- `assumption`: 这一步做了什么假设
- `regime`: 这个假设在什么范围内成立
- `confidence`: high | medium | low（AI 对这一步的理解程度）
- `l2_anchor`: 指向 L2 中的相关节点（如果存在）

输出：`active_derivation.md`

**Feynman 自检**：对每一步，遮住下一步，问自己"从这一步到下一步，我能否自己推出来？"如果不行，就是理解缺口。这个自检在学习模式下是强制的。

#### gap_audit（缺口审计）

**目的**：主动寻找论文中的缺口、隐藏假设和未验证的声明。

审计清单：
1. **未声明的假设**（unstated assumptions）：作者默认了什么没有明说？
2. **近似的适用范围**：每一步近似是否明确标注了有效范围？
3. **对应关系检查**：结果在已知极限下是否退化为已知结果？（最关键）
4. **前置知识完整性**：引用的前置结果是否在 L2 中已有？如果有缺失，是否影响本文结论？
5. **自洽性**：不同章节的符号约定、假设条件是否一致？

每个缺口标注：
- `severity`: blocking | important | minor | future_work
- `resolution`: can_resolve_locally | needs_external_source | needs_original_thought | deferred
- `l2_impact`: 对 L2 知识库的影响

输出：`active_gaps.md`

**对应原理自检**（学习模式特有）：对于每个结果，检查它是否在已知极限下退化为 L2 中的已知结果。如果论文没有做这个检查，这本身就是一个缺口。

#### synthesis（综合）

**目的**：用自己的框架重建论文贡献，并更新 L2 知识图谱。

- 生成 L2 图谱更新建议：
  - 新增节点（new concepts, results, techniques）
  - 新增边（relations, correspondence links, EFT tower connections）
  - 更新现有节点（regime refinement, new aliases, corrected expressions）
  - 标注开放问题
- 输出：`active_synthesis.md` + `l2_update_proposal.json`

**质量门**：synthesis 完成后，必须通过以下检查才能提交 candidate：
1. 每个新节点都有 `regime_of_validity`
2. 每个新结果都有对应的 `limits_to` 边（指向已知低能结果）
3. 每个推导链的每一步都有 `justification_type`
4. 所有 blocking 级别的缺口都已解决或有明确的 deferral 理由

### 3.3 学习模式转移规则

```
source_decompose  -> step_derive
step_derive       -> gap_audit, source_decompose
gap_audit         -> synthesis, step_derive
synthesis         -> (submit candidate)
```

后向边允许重做：如果 step_derive 发现分解不够细，可以回到 source_decompose。

### 3.4 学习模式的 candidate_type

学习模式提交的候选者类型不同于研究模式：

```python
STUDY_CANDIDATE_TYPES = [
    "atomic_concept",      # 单个物理概念 + 数学表达 + 适用范围
    "derivation_chain",    # 完整推导链（有序步骤，每步带 justification）
    "correspondence_link", # 两个理论之间的对应关系（带验证证据）
    "regime_boundary",     # 理论适用范围的边界条件
    "open_question",       # 从文献中发现的开放问题
]
```

这些候选者通过相同的 L4 验证和提升流程进入 L2。

### 3.5 学习模式与研究模式的切换

```python
# state.md 新增字段
l3_mode: "research" | "study"  # default: "research"

# 切换条件
research -> study:
  - 人类明确要求学习某篇文献
  - L3 推导中发现 L1/L2 知识缺口，需要先学习
  - L4 验证失败，需要回到文献理解假设

study -> research:
  - 学习完成后有了新的研究想法
  - 文献学习中发现的研究机会
  - 对应原理检查发现的新方向

# 切换时的状态保留
# 不清除当前子平面状态，而是保存并允许恢复
```

## 四、质量保证体系

### 4.1 三道防线

#### 第一道：覆盖度地图（Coverage Map）

```
论文结构: [Abstract, Sec1, Sec2, Sec3, Sec4, Conclusion]
已处理:   [done,    done, done, done, done, done    ]
原子声明数: 23
已分解:    21
未覆盖:    2 (Sec4 的两个 footnote)
缺口数:    2 (minor)
覆盖度:    91%
```

规则：
- 覆盖度 < 80% 不允许提交 candidate
- 未覆盖部分必须显式标注并说明原因
- 100% 覆盖不是目标——明确标注了哪些不覆盖以及为什么，才是目标

#### 第二道：Feynman 自检（Blind Derivation）

学习模式下的 L4 验证方式：
- 遮住推导步骤，让 AI 独立推导
- 对比原文推导和 AI 独立推导
- 差异点就是理解不够的地方
- 不需要 Lean 级别的形式化，但需要逐步骤对比

从 APOLLO 项目学到的：LLM + 形式化工具（Lean/Coq）的协作模式可以在不需要完全形式化的情况下提供结构化验证。关键不是每一步都形式化，而是每一步都有明确的验证策略。

#### 第三道：对应原理检查（Correspondence Principle Check）

- 每个新结果必须在已知极限下退化为 L2 中已知结果
- 如果 L2 中没有对应的已知结果，这本身就是 L2 的缺口——应该标注为 `regime_boundary` 或 `open_question`
- 对应关系是物理知识最核心的结构：不是"额外的检查"，而是知识本身的一部分

### 4.2 学习模式的 L4 验证

学习模式的 L4 验证与研究模式不同：

```python
STUDY_L4_CHECKS = [
    "coverage_check",              # 覆盖度是否达标
    "feynman_self_test",           # 盲推导是否通过
    "correspondence_check",        # 对应关系是否验证
    "derivation_step_completeness",# 每一步是否有 justification_type
    "regime_annotation",           # 每个结果是否有 regime_of_validity
    "l2_edge_completeness",        # 是否建立了必要的 L2 边
]
```

### 4.3 信任度演进

边和节点的信任度随时间演进：

```
初始信任（来自单篇文献学习）:
  basis: source_grounded
  scope: single_source

多源确认后:
  basis: multi_source_confirmed
  scope: bounded_reusable

对应原理验证后:
  basis: validated
  scope: broad_reusable

L4 独立推导验证后:
  basis: independently_verified
  scope: broad_reusable
```

## 五、增量知识构建

### 5.1 从 Jigsaw-LightRAG 学到的

核心洞察：知识图谱是增量构建的，每篇文献贡献一个子图（subgraph），子图之间通过全局去重和合并连接。

### 5.2 子图增量协议

```
每篇论文的学习 -> 生成一个 subgraph_delta:
  nodes: [新概念, 新结果, 新技术, ...]
  edges: [新关系, 对应原理链接, EFT 塔连接, ...]
  missing_prerequisites: [L2 中还没有但应该有的节点]

全局合并流程:
  1. 文档级去重: 同一篇论文内的重复声明合并
  2. 跨文档去重: 与 L2 现有节点匹配
     - 匹配策略: (mathematical_expression + physical_meaning) 双重匹配
     - 匹配成功: 合并，提升信任度
     - 匹配失败但有相似: 创建 alias 或 specialization 关系
     - 完全不同: 创建新节点
  3. 边合并: 同一关系如果多次独立确认，提升信任度
  4. 冲突检测: 新结果与 L2 已有结果矛盾 -> 记录冲突 -> 需要人类裁决
```

### 5.3 LightRAG 双层检索

应用到 L2 查询：
- **底层检索**：具体实体和事实（"Sagnac effect 的相位差公式是什么"）
- **高层检索**：主题和关系（"哪些效应涉及旋转参考系"）

实现方式：
- 底层：直接节点 ID 查找 + 别名匹配
- 高层：边关系遍历 + EFT 塔定位 + 语义搜索

## 六、实施路线图

### Phase 1: 基础架构（study mode）

文件修改：
- `brain/state_model.py`:
  - `StageSnapshot` 添加 `l3_mode` 字段
  - 添加 `STUDY_L3_SUBPLANES`, `STUDY_L3_ALLOWED_TRANSITIONS`
  - 添加 `STUDY_L3_ARTIFACT_TEMPLATES`, `STUDY_L3_ACTIVE_ARTIFACT_NAMES`
  - 添加 `STUDY_L3_SKILL_MAP`, `STUDY_L3_REQUIRED_HEADINGS`
  - `evaluate_l3_stage()` 分支 l3_mode
- `brain/mcp_server.py`:
  - `aitp_advance_to_l3()` 检查 l3_mode
  - 添加 `aitp_switch_l3_mode()` 工具
  - `aitp_submit_candidate()` 支持 study candidate types
  - `aitp_advance_l3_subplane()` 支持 study 转移规则
- 新建 skill 文件:
  - `skills/skill-l3-decompose.md`
  - `skills/skill-l3-step-derive.md`
  - `skills/skill-l3-gap-audit.md`
  - `skills/skill-l3-synthesis.md`
- `brain/PROTOCOL.md` 更新学习模式文档

### Phase 2: L2 知识图谱

- 图谱目录结构创建工具
- 节点读写工具（`aitp_create_l2_node`, `aitp_update_l2_node`）
- 边读写工具（`aitp_create_l2_edge`）
- EFT 塔定义和对应原理记录
- 增量合并逻辑（`aitp_merge_subgraph_delta`）
- 升级 `aitp_promote_candidate()` 以创建图谱节点和边

### Phase 3: 检索和质量工具

- L2 查询工具升级（双层检索）
- 覆盖度地图工具
- Feynman 自检工具（盲推导比对）
- 对应原理自动检查工具

### Phase 4: 可视化（可选）

- EFT 塔可视化（能量轴 + 节点 + 边）
- 推导链可视化（步骤 + 依赖 + justification）
- 冲突和缺口标记

## 七、参考项目和方法论

| 项目 | 核心启发 | 应用到 AITP |
|------|----------|-------------|
| LightRAG | 双层检索（低层实体 + 高层主题） | L2 查询的层级设计 |
| Jigsaw-LightRAG | 文档子图 + 全局去重 + 增量合并 | L2 增量构建协议 |
| APOLLO (LLM+Lean) | 结构化验证不需要完全形式化 | L4 盲推导验证策略 |
| EFT Tower / Wilsonian RG | 物理学知识的层级结构 | L2 EFT 塔结构 |
| 对应原理 | 理论之间的"宪法级"关系 | 对应原理自检 + edge type |
| Barry Smith 物理本体论 | 形式化知识表示 | 节点/边类型系统 |
| Feynman 方法 | "能用简单语言解释才是真理解" | 学习模式的质量保证核心 |

---

*本文档是 AITP 学习模式和 L2 知识图谱增强的设计蓝图，基于 2026-04-24 的认识。随实施推进持续更新。*
