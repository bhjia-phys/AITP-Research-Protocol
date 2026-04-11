# Requirements: v1.64 L1 Method Specificity Surface

## Milestone Goal

Close the first still-missing production slice of backlog `999.27` by giving
AITP a real L1 method-specificity surface on top of the already-implemented
assumption, regime, reading-depth, notation, and contradiction paths.

## Active Requirements

### Method Specificity Extraction

- [x] `REQ-MSPEC-01`: AITP records source-backed `method_specificity_rows`
  inside `l1_source_intake` during real topic-shell distillation.
- [x] `REQ-MSPEC-02`: each method-specificity row captures a bounded method
  family, a specificity tier, and evidence excerpt tied to source-backed text
  rather than free-floating heuristics.

### Runtime And Acceptance Surface

- [x] `REQ-MSPEC-03`: topic-shell markdown, runtime bundle, and `status --json`
  expose the method-specificity surface through real production paths.
- [x] `REQ-MSPEC-04`: an isolated acceptance path proves the surface through a
  real CLI/runtime entrypoint and durable artifacts.

### Documentation And Acceptance

- [x] `REQ-MSPEC-05`: public docs, contract tests, and the new acceptance path
  document the method-specificity surface honestly as a first production slice
  of `999.27`.

### Verification

- [x] `REQ-VERIFY-01`: the milestone closes with targeted regressions,
  maintainability-budget verification, and a green full knowledge-hub suite.
