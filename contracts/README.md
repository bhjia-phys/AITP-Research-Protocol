# Contract Family

AITP uses durable contracts to keep research state inspectable and auditable.

The current public contract family is:

- `research-question`
- `candidate-claim`
- `derivation`
- `validation`
- `operation`
- `promotion-or-reject`
- `development-task`
- `computation-workflow`
- `compute-resource`
- `benchmark-report`
- `calculation-debug`

Each contract has:

- a human-readable description in this directory;
- a matching JSON Schema under `../schemas/` that describes the YAML frontmatter fields.
