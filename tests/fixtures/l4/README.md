# L4 Test Data Backups

Known-good fixture data for L4 validation layer regression tests.
These persist across test runs so L4 review format changes can be
checked against a stable baseline.

## Contents

- `reviews/` — one review per L4 outcome (pass, partial_pass, fail,
  contradiction, stuck, timeout), plus a versioned review (`_v2.md`)
- `validation_contract.md` — sample validation contract before review
- `physics_check_baseline.json` — expected physics check fields and
  representative pass/fail values
- `candidate_baseline.md` — sample candidate ready for L4 review
- `tex/` — compiled flow notebook TeX outputs from known-good L4 runs
