---
name: skill-notebook-generate
description: |
  AI-Agent-driven research notebook generation from AITP L0-L4 artifacts.
  Replaces programmatic Markdown→LaTeX conversion. AI agents read structured
  research artifacts, understand the physics, and write LaTeX sections 
  directly using the JHEP+AITP template. Parallel agents for speed.
trigger: |
  User asks to generate/update/regenerate the research notebook,
  "写notebook", "生成notebook", "更新notebook", "compile notebook",
  or after major L3/L4 state changes.
---

# Agent-Driven Research Notebook Generation

## Architecture

Instead of regex-based Markdown→LaTeX conversion (which creates invalid LaTeX
from physics notation), AI agents READ the structured L0-L4 research artifacts,
UNDERSTAND the physics content, and WRITE LaTeX directly.

```
MASTER agent
  ├── Agent A → reads L1/question_contract.md, L0/sources/ → writes section_01_motivation.tex
  ├── Agent B → reads L1/convention_snapshot.md, domain-manifest.md → writes section_02_setup.tex
  ├── Agent C → reads L3/derive/, L3/trace-derivation/, L3/gap-audit/, L3/runs/ → writes section_03_derivation.tex
  ├── Agent D → reads L4/outputs/, L4/reviews/, runtime/log.md → writes section_04_results.tex
  ├── Agent E → reads L3/distill/, L3/candidates/, L1/contradiction_register.md → writes section_05_discussion.tex
  ├── Agent F → reads L0/source_registry.md, L0/sources/*/source.md → writes appendix_A1_sources.tex
  └── Agent G → reads runtime/log.md, runtime/sessions.md → writes appendix_A2_execution_log.tex
```

Each agent operates INDEPENDENTLY — they don't need to coordinate, just read
their assigned artifacts and write their section.

## Section → Artifact Map

| Section File | Agent | Source Artifacts | Key Content to Extract |
|-------------|-------|-----------------|----------------------|
| `section_01_motivation.tex` | A | L1/question_contract.md, L1/source_basis.md, L0/sources/*/source.md, MEMORY.md | Bounded question, competing hypotheses, scope, motivation, physical system |
| `section_02_setup.tex` | B | L1/convention_snapshot.md, contracts/domain-manifest.md, L1/derivation_anchor_map.md | Notation table, units, sign conventions, code↔theory symbol mapping, key formulas |
| `section_03_derivation.tex` | C | L3/derive/active_derivation.md, L3/trace-derivation/active_trace.md, L3/gap-audit/active_gaps.md, L3/runs/*/derivation_records.md, L3/integrate/active_integration.md | Derivation steps with equations, source anchors, gaps flagged, integration findings |
| `section_04_results.tex` | D | L4/outputs/*.md, L4/reviews/*.md, L4/validation_contract.md, runtime/log.md | Numerical results in valbox, validation tables, test matrix summary, failure analysis |
| `section_05_discussion.tex` | E | L3/distill/active_distillation.md, L3/candidates/*.md, L1/contradiction_register.md, L3/deferred.md | Distilled claims, candidate status, open questions, next steps, contradictions |
| `appendix_A1_sources.tex` | F | L0/source_registry.md, L0/sources/*/source.md | Source table: ID, title, type, role, fidelity, key files |
| `appendix_A2_execution_log.tex` | G | runtime/log.md, runtime/sessions.md | Session summary table, key events timeline |

## LaTeX Writing Guidelines for Agents

### Use the AITP environments from `aitp_paper.sty`:

```latex
% Research question
\begin{resultbox}[Bounded Question]
...question text...
\end{resultbox}

% Derivation step (numbered)
\setcounter{derivationstep}{N}
\derivationstep{Step Name}{
...derivation content with equations...
\sourceanchor{ID}{source_file:line}
}

% Gap flag
\gapflag[G1]{Description of the gap}

% Numerical result
\numericalresult{Observable}{System}{Method}{value}{uncertainty}{units}

% Validation table
\begin{validationtable}{Title}
Check description & Result details & \statuspass \\
\end{validationtable}

% Warning
\begin{warningbox}[Title]
...warning content...
\end{warningbox}
```

### Critical rules:
1. **ALL math in `$...$` or `\[...\]` or `\begin{equation}`** — never bare `_` or `^`
2. **Use `\sourceanchor{ID}{file:line}`** to link claims back to L0 sources
3. **Use `\gapflag[ID]{description}`** to mark unverified assumptions
4. **Every `\begin{...}` must have `\end{...}`**
5. **Tables use `\begin{tabular}` with `\toprule`/`\midrule`/`\bottomrule`**
6. **Code snippets use `\begin{lstlisting}[language=X]`**
7. **Don't copy raw markdown** — rewrite in proper LaTeX narrative

## Execution Protocol

### 1. Pre-flight check
- Read `state.md` from the topic root
- Check if `templates/aitp_notebook_master.tex` exists; if not, copy from protocol repo
- Check if `aitp_paper.sty` exists in the notebook directory; if not, copy from templates
- Determine which sections need regeneration (by artifact mtime vs `.notebook_build_ts`)

### 2. Parallel agent dispatch
Launch ALL 7 agents simultaneously using the Agent tool with `run_in_background: true`.
Each agent writes ONE section file. Agents must NOT read each other's output.

### 3. Assembly
After all agents complete:
- Run `pdflatex -interaction=nonstopmode master.tex` 
- If errors: read `.log`, identify the failing section, relaunch that section's agent with the error context
- Max 3 retry cycles
- Record build timestamp to `runtime/.notebook_build_ts`

### 4. Human review
- Open the compiled PDF
- Report: which sections were regenerated, any unresolved compilation warnings

## Incremental Rebuild

Check `runtime/.notebook_build_ts` against artifact mtimes:

```python
def needs_rebuild(section, topic_root, last_build):
    sources = SECTION_SOURCE_MAP[section]
    for src in sources:
        p = topic_root / src
        if p.exists() and p.stat().st_mtime > last_build:
            return True
    return False
```

Only dispatch agents for sections whose source artifacts changed.

## Agent Prompt Template

Each agent receives a prompt like:

```
You are writing a section of an AITP research notebook in JHEP format.

TOPIC: {topic_title}
SECTION: {section_name}
SOURCE FILES TO READ:
  - {path1}  ({description1})
  - {path2}  ({description2})
  ...

YOUR JOB:
1. Read all listed source files
2. Understand the physics content
3. Write {section_file} as a proper LaTeX file

The file must:
- Start with \section{{...}} or \appendix \section{{...}} (for appendix)
- Use AITP environments: resultbox, derivationbox, valbox, validationtable,
  warningbox, gapflag, sourceanchor, numericalresult
- Write proper LaTeX: all math in $...$ or equation environment
- Be self-contained (no \input inside section files)
- Include source anchors linking claims to L0 sources

Do NOT read other section files. Write ONLY your assigned section.
```

## Verification

After regeneration, verify:
- [ ] `pdflatex master.tex` exits with 0 errors
- [ ] PDF contains all 5 sections + 2 appendices
- [ ] Derivation has numbered steps with source anchors
- [ ] Validation section has numerical results with units
- [ ] Source appendix lists all L0 sources
- [ ] No raw markdown artifacts (no `**`, `#`, `|...|` in output)
