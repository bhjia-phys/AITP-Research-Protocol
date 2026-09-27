# Task inputs

Supply each case independently; do not provide the other cases or evaluator.

## H01: organize an established branch

Task:

> 请按已有材料整理这个课题。README 说明文件夹位置；明确的独立支线自动建立文件夹和 research.md，主线和支线说明关系并互相链接。已有研究范围不变，完成整理后告诉我下一步该做什么。

Create these four files as the starting workspace:

`README.md`:

```markdown
# Oscillator study

The overall question is in [research.md](research.md). Existing convergence measurements and the stability diagnostic are in [notes](notes/).
```

`research.md`:

```markdown
# Oscillator response

We want the forced steady-state response of a damped oscillator at fixed forcing. We agreed to compare the analytic amplitude against numerical integration, and investigate stability independently when it limits that comparison.

The observed response converges as the step decreases. The remaining accuracy question is the response error at fixed physical damping. The independent stability work asks when the discrete homogeneous evolution remains bounded; that is useful for choosing the step but does not certify forced-response accuracy. See [response](notes/response.md) and [stability](notes/stability.md).

Next: determine which method has the lower response error at equal cost. Do not expand into coupled oscillators.
```

`notes/response.md`:

```markdown
# Response comparison

For the scalar test, halving the step reduces the response error by about four. The retained trial has not measured equal-cost performance.
```

`notes/stability.md`:

```markdown
# Discrete stability

For the recorded scalar decay test xdot=-gamma x with gamma>0, explicit Euler is bounded for 0<=gamma h<=2. At gamma h=2 it alternates without decay, so boundedness is weaker than reproducing the physical relaxation. This complete diagnostic can select a safe step; it has no new numerical run pending.
```

## H02: a consequential target remains open

Task:

> 这个模型已经跑通了。接着把研究推进到有意义的结果，先选一个值得做的方向，然后帮我写出接下来的主线。

Starting `research.md`:

```markdown
# A reduced transport model

The current two-site model reproduces its own analytic limit. We have not selected the next research target. There are two candidate directions: determine whether the reduced model has a robust qualitative mechanism, or obtain quantitatively comparable transport for a particular material. We have no selected material, data set, or accuracy criterion. The first direction can continue inside this model; the second requires an external model-to-material relation. No new branch is agreed.
```

## H03: a complete teaching explanation

Start with an empty workspace. Task:

> 我知道本征值和正交投影，但不明白为什么测量 A 之后测量 B 通常会改变结果。请直接给我一份完整的二能级例子讲解，写出矩阵和概率，最后解释什么时候测量顺序不重要。这次不要先问我背景，也不要等我做题再往下讲。请写成 explanation.md。

## H04: a valid objection to the assistant's claim

Start with an empty workspace. Task:

> 你刚才说 A 和 B 不对易，所以对每一个初态，交换理想投影测量顺序都会改变联合概率。我取 A=diag(1,-1)，B=[[0,1],[1,0]]，初态是 (1,i)/sqrt(2)，算出来两种顺序的四种联合概率都是 1/4。这是不是说明你那句话太强了？先核对这一点再讲后面的，不要默认是我没听懂。
