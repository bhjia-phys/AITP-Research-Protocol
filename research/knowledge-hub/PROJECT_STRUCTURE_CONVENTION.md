# Project Structure Convention

This document defines the mandatory project structure, documentation, and
workflow conventions for ABACUS+LibRPA feature development within the AITP
`code_method` lane.

These rules are **non-negotiable** for every new feature project. They exist to
ensure derivations drive code, not the other way around.

---

## 1. Project folder

Every new feature project begins with creating a **dedicated project folder**.
The location is chosen by the human collaborator. All project-related artifacts
— references, derivations, code, computation outputs, contracts — live inside
this folder and nowhere else.

```
<project-root>/                    # Human-chosen location
├── README.md                      # Project overview and status
├── L0_source/                     # Layer 0: Source acquisition
│   └── ref/                       #   Downloaded papers (PDF, TeX, BibTeX)
├── L1_intake/                     # Layer 1: Provisional understanding
├── L2_canonical/                  # Layer 2: Trusted memory
├── L3_exploratory/                # Layer 3: Exploratory outputs
├── L4_validation/                 # Layer 4: Validation and trust audit
├── docs/                          # LaTeX documentation (isolated)
│   ├── main.tex                   #   Master document
│   ├── preamble.sty               #   Shared preamble
│   ├── sections/                  #   One .tex per topic
│   │   ├── 01_introduction.tex
│   │   ├── 02_derivation.tex      #   Formula derivations
│   │   ├── 03_implementation.tex  #   Code-to-formula mapping
│   │   ├── 04_results.tex         #   Numerical results
│   │   └── 05_summary.tex
│   └── figures/                   #   Generated figures
├── code/                          # Source code changes
│   └── patches/                   #   Diffs and patches
├── computation/                   # Computation outputs
│   ├── smoke_test/                #   Phase 4 smoke test
│   └── benchmark/                 #   Phase 5 production runs
├── contracts/                     # AITP contract instances (Markdown + YAML frontmatter)
│   ├── development-task.*.md
│   ├── computation-workflow.*.md
│   ├── benchmark-report.*.md
│   └── calculation-debug.*.md
├── archive/                       # Reproducibility archive (append-only)
│   ├── conversations/             #   Unedited conversation transcripts
│   ├── specs/                     #   Externalized spec versions
│   └── hitl-log.md                #   HITL round tracking
└── build/                         # Build configurations
    └── cmake/                     #   CMake presets
```

### Rules

1. **One project, one folder.** No scattering files across multiple locations.
2. **Location is human-chosen.** The agent proposes a default path, the human
   confirms or overrides.
3. **All artifacts stay local.** References, derivations, code, outputs —
   everything goes into the project folder.
4. **No orphan files outside.** If a file relates to this project, it belongs
   inside the project folder.

---

## 2. Layer subdirectories

Each AITP layer (L0–L4) has its own subdirectory. Files are placed according
to their layer role, not their file type.

| Directory | Layer | What goes here |
|-----------|-------|---------------|
| `L0_source/` | L0 | Papers, references, upstream code snapshots, algorithm descriptions |
| `L0_source/ref/` | L0 | Downloaded PDFs, TeX sources, BibTeX files |
| `L1_intake/` | L1 | Reading notes, input consistency reports, implementation plans |
| `L3_exploratory/` | L3 | Feature branch code, intermediate test results, draft derivations |
| `L4_validation/` | L4 | Convergence data, benchmark comparisons, invariant check results |
| `L2_canonical/` | L2 | Approved derivations, validated benchmark data, experience cards |

### Promotion rules

Files move from lower layers to higher layers through the standard AITP
promotion gates. A file in `L3_exploratory/` does not become trusted just
because the agent is confident — it must pass L4 validation and receive
explicit human approval before moving to `L2_canonical/`.

---

## 3. LaTeX documentation

### Requirement

**All documentation must be written in LaTeX.** This includes:

- Formula derivations
- Algorithm descriptions
- Progress notes
- Physical correctness arguments
- Benchmark analysis
- Summary reports

Plain Markdown is acceptable only for `README.md` and AITP contract
descriptions. Everything else uses LaTeX.

### Why LaTeX

1. **Formula fidelity.** Physics derivations require precise mathematical
   notation. LaTeX is the standard.
2. **Compilability.** A LaTeX document compiles into a PDF that can be
   reviewed, shared, and archived.
3. **Version control.** LaTeX source is plain text — diff-friendly.
4. **Isolation.** Documentation lives in `docs/`, separate from code and
   computation. This prevents entanglement.

### Structure

```
docs/
├── main.tex               # \input{sections/...} — master document
├── preamble.sty            # Shared packages and macros
├── sections/
│   ├── 01_introduction.tex
│   ├── 02_derivation.tex   # THE key file — all formulas here
│   ├── 03_implementation.tex  # Maps formulas to code
│   ├── 04_results.tex
│   └── 05_summary.tex
└── figures/
    └── *.pdf               # Generated from computation or tikz
```

### Compilation

```bash
cd <project-root>/docs
latexmk -pdf main.tex
```

The compiled `main.pdf` is the single authoritative document for the project.

---

## 4. Derive-first workflow

This is the core discipline: **formulas before code, always**.

### The rule

```
Derive → Human Approve → Code → Validate
  ↑                                      |
  └─────── (if validation fails) ────────┘
```

**Code must strictly follow the approved derivation. The agent must not modify
the physics without updating the derivation first and getting human approval.**

### Step-by-step

1. **Derive** (L0→L1→L3):
   - Read references in `L0_source/ref/`
   - Write derivations in `docs/sections/02_derivation.tex`
   - Include: starting equations, assumptions, step-by-step algebra, final
     formula that will be implemented
   - Compile LaTeX to verify notation is correct

2. **Human review gate** (G0: Derivation approved):
   - Present the compiled `main.pdf` to the human
   - Human reviews the derivation for correctness
   - Human may request modifications
   - **The derivation is not approved until the human explicitly says so**

3. **Implement** (L3):
   - Write code in `code/` that implements the approved derivation
   - Code must include comments referencing the specific equation numbers
     from `02_derivation.tex`
   - Example: `// Implements Eq. (12) from docs/sections/02_derivation.tex`

4. **Validate** (L4):
   - Run computations, compare with derivation predictions
   - If validation fails, **go back to step 1** — re-derive, get approval,
     then fix code
   - The agent must never silently change the physics in code to make tests
     pass

### What counts as a derivation

A derivation must contain:

| Element | Description |
|---------|-------------|
| Starting point | What known equation or algorithm are we building on? |
| Assumptions | What approximations are being made? |
| Steps | Algebraic or logical steps from start to finish |
| Final formula | The equation that will be implemented in code |
| Domain of validity | Under what conditions is this formula valid? |
| Reference to literature | Which paper(s) does this come from? |

### What is forbidden

- Writing code before the derivation is approved
- Modifying the physics in code without updating the derivation
- Implementing "a slightly different formula" because it seems to work better
- Skipping the human review gate
- Using comments like "this is equivalent to Eq. X but rearranged" without
  showing the rearrangement in the derivation

---

## 5. Directory creation checklist

When starting a new project, the agent must:

- [ ] Ask the human for the project folder location
- [ ] Create the full directory structure (L0–L4, docs/, code/, computation/, contracts/, build/)
- [ ] Create `docs/main.tex` with the standard template
- [ ] Create `docs/preamble.sty` with physics macros
- [ ] Create `docs/sections/` with stub .tex files
- [ ] Create `README.md` with project name, topic, and status
- [ ] Bootstrap the AITP topic and record the topic slug in README

### Minimal LaTeX template (`docs/main.tex`)

```latex
\documentclass[11pt,a4paper]{article}
\usepackage{preamble}

\title{<PROJECT TITLE>}
\author{<AUTHOR>}
\date{\today}

\begin{document}
\maketitle
\tableofcontents

\input{sections/01_introduction}
\input{sections/02_derivation}
\input{sections/03_implementation}
\input{sections/04_results}
\input{sections/05_summary}

\bibliographystyle{unsrt}
\bibliography{../L0_source/ref/references}
\end{document}
```

### Minimal preamble (`docs/preamble.sty`)

```latex
\NeedsTeXFormat{LaTeX2e}
\ProvidesPackage{preamble}

% Mathematics
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{bm}
\usepackage{physics}

% Graphics
\usepackage{graphicx}
\usepackage{tikz}

% Tables
\usepackage{booktabs}
\usepackage{longtable}

% Cross-referencing
\usepackage{hyperref}
\usepackage{cleveref}

% Custom commands
\newcommand{\ket}[1]{\left|#1\right\rangle}
\newcommand{\bra}[1]{\left\langle#1\right|}
\newcommand{\braket}[2]{\left\langle#1|#2\right\rangle}
\newcommand{\expect}[1]{\left\langle#1\right\rangle}
\newcommand{\Hhat}{\hat{H}}
\newcommand{\Ghat}{\hat{G}}
\newcommand{\Sigmahat}{\hat{\Sigma}}
\newcommand{\chiO}{\chi^0}
\newcommand{\W}{\mathcal{W}}
```

---

## 6. Relationship to other protocol documents

| Document | Relationship |
|----------|-------------|
| `FIRST_PRINCIPLES_LANE_PROTOCOL.md` | Defines the domain protocol; this document adds structural and workflow conventions |
| `FEATURE_DEVELOPMENT_PLAYBOOK.md` | Defines the phase-by-phase process; this document adds the folder structure and derive-first gate |
| AITP core `L0–L4` layer model | This document maps layers to concrete filesystem directories |

When this document conflicts with a general AITP convention, **this document
takes precedence** for ABACUS+LibRPA feature development projects within the
`code_method` lane.

---

## 7. Reproducibility archive

Every project must include an `archive/` directory for reproducibility. This
directory is **append-only**: never modify or delete past entries.

### Directory structure

```
archive/
├── conversations/                # Unedited conversation transcripts
│   ├── {phase}-{model}#{round}.md
│   └── ...
├── specs/                        # Externalized spec versions
│   ├── spec-v1.md                # First version (LLM output)
│   ├── spec-v2.md                # After human review
│   └── spec-final.md             # Approved version
├── code/                         # Code versions with pass/fail status
│   ├── {artifact}-{model1}-{model2}#{round}-{Pass|Fail}.{ext}
│   └── ...
└── hitl-log.md                    # HITL round tracking
```

### Naming convention

All archived materials follow the pattern:

```
{artifact}-{model1}-{model2}#{round}-{status}.{ext}
```

Where:

- `artifact`: what was produced (`spec`, `code`, `conversation`)
- `model1`: model that produced the spec (omitted for zero-shot)
- `model2`: model that produced the code
- `round`: iteration number (1, 2, 3, ...)
- `status`: `Pass` or `Fail`

### HITL log schema

```json
{
  "project": "project-name",
  "entries": [
    {
      "round": 1,
      "phase": "3",
      "spec_model": "claude",
      "code_model": "claude",
      "status": "Fail",
      "human_feedback_summary": "Brief description of the feedback",
      "timestamp": "2026-04-15T10:30:00Z",
      "artifact_path": "archive/code/code-claude-claude#1-Fail.py"
    }
  ]
}
```

### Rules

1. **Append-only**: past entries are never modified or deleted
2. **Complete**: every round must have an entry, including failures
3. **Unedited**: conversation transcripts are preserved exactly as they occurred
4. **Traceable**: each entry links to the corresponding artifact file
