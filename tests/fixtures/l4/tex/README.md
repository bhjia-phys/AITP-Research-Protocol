# L4 Test TeX Records

Compiled flow notebook TeX outputs from known-good L4 validation runs.
These serve as regression baselines for the TeX rendering pipeline.

## Files

- `l4_validation_test_record.tex` — Full L4 validation TeX with all six
  outcomes, physics checks, devil's advocate records, SymPy evidence,
  versioned review (v2), and trust classification. Generated from
  `tests/fixtures/l4/reviews/*.md`.

## Rebuilding

To regenerate the TeX records from current fixtures:

```bash
cd tests/fixtures/l4/tex
pdflatex l4_validation_test_record.tex
pdflatex l4_validation_test_record.tex  # second pass for TOC
```

Build artifacts (`.aux`, `.log`, `.out`, `.toc`, `.pdf`) should be
committed alongside the `.tex` source for fast regression diffing.

## Regression Test

The test in `test_l4_l2_memory.py` can be extended to verify that:
1. All six L4 outcome fixture files parse correctly
2. The physics check baseline JSON matches `PHYSICS_CHECK_FIELDS`
3. The validation contract has all mandatory fields
