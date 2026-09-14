# Journal sources and the Markdown adaptation

The sources below were inspected on 2026-09-14. These AITP Markdown templates
are original editorial starting points. They are not official journal templates
or a claim of compliance with submission requirements.

## What the official TeX sources provide

PRL, PRX and PRB share [APS REVTeX 4.2](https://journals.aps.org/revtex).
The distribution contains `apstemplate.tex` and the fuller `apssamp.tex` in
`doc/latex/revtex/sample/aps/`. The APS page links the
[CTAN distribution](https://ctan.org/pkg/revtex), including its
[downloadable archive](https://mirrors.ctan.org/macros/latex/contrib/revtex.zip).
The template defines title and author material, an abstract, sectioning,
equations, figures and tables, optional appendices, and a bibliography.
The journal options select formatting within the same class:

```tex
\documentclass[aps,prl,reprint]{revtex4-2} % PRL
% Use prx for PRX or prb for PRB in place of prl.
```

The [official JHEP package page](https://jhep.sissa.it/jhep/help/JHEP_TeXclass.jsp)
provides `jheppub.sty`, `JHEP.bst`, an
[example archive](https://jhep.sissa.it/jhep/help/JHEP/TeXclass/DOCS/example.tar.gz)
and the [author manual](https://jhep.sissa.it/jhep/help/JHEP/TeXclass/DOCS/JHEP-author-manual.pdf).
Its `jhepexample.tex` uses:

```tex
\documentclass[a4paper,11pt]{article}
\usepackage{jheppub}
```

The example demonstrates an abstract, nested sections, labelled equations,
cross-references, captioned figures and tables, an appendix and a bibliography.
It demonstrates typesetting conventions rather than prescribing an argument
for every theoretical-physics topic.

## What AITP takes from each venue

| Source | Relevant guidance | AITP adaptation |
| --- | --- | --- |
| [PRL author guidance](https://journals.aps.org/prl/authors) | An introduction, central argument establishing results, and conclusion; the main article must remain understandable with details elsewhere. | A compact note keeps its decisive implication visible and links extended derivations. Use the Letter template when the whole question fits this form. |
| [PRX author guidance](https://journals.aps.org/prx/authors) | Research articles have no fixed length limit; framing and interpretation address a broad physics readership. | Give the motivation and physical meaning room to develop. Either full template can expand when the argument requires it. |
| [JHEP TeX example](https://jhep.sissa.it/jhep/help/JHEP/TeXclass/DOCS/example.tar.gz) | Structured sections, displayed equations, cross-references and titled appendices. | A theory note can develop setup, construction and consequences, with detailed proofs in linked notes. |
| [PRB author guidance](https://journals.aps.org/prb/authors) | Regular articles allow extended treatment; explain terminology and connections to the literature for the journal's readership. | A computational or mixed note connects model, methods, controlled comparisons and interpretation. |

These are editorial choices by AITP. PRB is not restricted to numerical work,
JHEP is not restricted to proofs, and the journals do not mandate our proposed
section headings. Do not create four almost identical `research.md` files or
choose a publication venue merely to start a topic.

## Use the templates

- [Compact argument](../assets/research-letter.md): a short, self-contained
  question with one central construction, comparison or obstruction.
- [Formal theory or conceptual learning](../assets/research-theory.md): precise
  setting, construction, consequences and physical interpretation.
- [Computation or theory with numerical tests](../assets/research-computational.md):
  model, theoretical basis, method, evidence and controlled interpretation.

Choose the form that carries the whole agreed research question. Section titles
can describe the actual scientific content. Merge or omit sections that have no
work to do, and remove drafting comments before presenting a finished revision.
A new topic may contain only an honest abstract, introduction and proposed route.
No journal word count, page count or fixed number of sections applies.

Use ordinary Markdown headings, paragraphs, links and tables. Use `$...$` and
`$$...$$` for mathematics where the reader supports them. An image can have a
caption immediately below it and a nearby link to its generating analysis;
a PDF can be linked directly. Standard Markdown does not reproduce TeX columns,
float placement or automatic equation numbering. No CSS, conversion pipeline,
Obsidian plugin or bibliography processor is required.

Research memory adds the live uncertainty, useful failed routes and evidence
links that a submitted article might compress. Keep these attached to the
argument; a short optional open-questions ending is enough when needed. Follow
[main-note guidance](research-note.md) for revisions and asset preservation.
TeX manuscript production remains a separate, explicitly requested task.
