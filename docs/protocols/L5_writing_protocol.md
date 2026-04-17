# L5 Writing Protocol

Domain: Point (L5)
Authority: subordinate to AITP SPEC S3.

---

## 5.1. Role

L5 is the output layer where topic results are compiled into publication-grade
artifacts: papers, slides, reports, and other writing products. It draws from
L2 (validated canonical knowledge) and L3 (novel results pending review).

L5 is NOT a validation layer. It does not judge whether results are correct —
that is L4's role. L5's role is to present results clearly and completely.

## 5.2. Artifacts

L5 may produce:

- **Paper drafts** — LaTeX manuscripts, journal submissions
- **Slides** — presentation materials for talks or defenses
- **Reports** — technical reports, thesis chapters
- **Supplementary materials** — appendices, code documentation, data tables

## 5.3. Source Layers

| Source | What L5 draws | Trust level |
|--------|---------------|-------------|
| L2 | Validated knowledge, definitions, theorems, methods | Trusted |
| L3-A | Novel candidates not yet promoted | Untrusted (mark as preliminary) |
| L3-R | Validation results supporting claims | Audit surface |
| L4 | Numerical data, plots, benchmarks | Audit surface |

L5 must distinguish between content drawn from L2 (presented as established)
and content drawn from L3 (presented as preliminary or subject to review).

## 5.4. Writing Workflow

1. **Gather** — collect relevant L2 knowledge and L3 results for the topic.
2. **Outline** — create structure, identify which claims go where.
3. **Draft** — write sections, clearly separating established from preliminary.
4. **Cite** — trace every claim to its source layer (L0 source, L2 knowledge,
   or L3 candidate).
5. **Review** — human reviews the draft. L5 does not auto-publish.
6. **Revise** — iterate based on human feedback.

## 5.5. Constraints

- L5 may NOT introduce new claims not present in L2 or L3.
- L5 must NOT promote L3 content as if it were L2-validated.
- Every figure/table must trace to an L4 validation result or L2 canonical data.
- L5 outputs require human review before any external submission.
- L5 does not modify L0-L4 artifacts.

## 5.6. File Convention

```
topics/<topic_slug>/
  L5_writing/
    outline.md              # paper outline
    draft.tex               # main LaTeX draft
    figures/                # plots from L4
    tables/                 # data tables
    references.bib          # bibliography from L0
```

## 5.7. What L5 Should Not Do

- Invent results not backed by L2 or L3.
- Present unvalidated L3 candidates as established facts.
- Skip human review before submission.
- Modify L2 or L3 artifacts during the writing process.
