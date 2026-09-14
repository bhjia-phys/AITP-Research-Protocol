# Cite equations, notes and evidence

Use ordinary Markdown links and enough scientific context to identify what is
being cited. A link should explain its role: definition, proof, counterexample,
source passage, implementation or measured comparison. Keep a short note readable
without requiring a click for each sentence.

## Equations and local numbering

Use `$...$` inline and `$$...$$` for displayed mathematics in a compatible reader.
Number equations that are referred to or need a precise discussion; routine
intermediate displays may remain unnumbered. Number independently within each
file. A long note may use section-based numbers if that is its existing convention.
No project-wide sequence or equation registry is required.

Where MathJax-compatible tagging has been checked, a display can use:

```md
$$
H_\beta=(1-\beta)H_0+\beta H_t.
\tag{1}
$$
```

When rendering support is unknown, a visible prose label such as
`**Equation (1): linear mixing.**` beside the display retains the locator.
Do not show two conflicting numbers or add both labels unnecessarily.

Cross-file references give the meaning, linked file and that file's local number:

```md
The update follows the
[linear-mixing rule, Eq. (1)](notes/hamiltonian-mixing.md).
```

For a long file, link the relevant named section as well. Prefer informative,
stable headings; test the fragment in the intended reader before promising a
precise jump. A number displayed by `\tag` is not itself a portable link target.
Markdown has no universal cross-file `\label`/`\eqref` resolver. Use those commands
only where the actual renderer has demonstrated the required behavior.

When changing a cited number, heading, filename or equation meaning, inspect and
repair its affected references. A narrow text search around that file and formula
is normally sufficient; no automatic whole-library audit is required. Main text
may restate a decisive equation with its own local number and link its derivation.

## Papers, figures and numerical evidence

Distinguish local equation numbers from source-paper numbers: write "Witten,
Section 2.6, Eq. (2.28)" when citing that source, rather than an ambiguous "Eq. (2)".
Give an identifiable title/author and DOI, arXiv or local PDF link. Preserve the
version or page convention when it affects the locator. A reading note says
which passages were inspected and separates source claims from the researcher's
derivation. Do not claim full-paper understanding from abstract inspection.

Number figures and tables locally when they need references. Define quantities,
conditions, units and uncertainties in the caption or adjacent text. Link the
generating analysis and data; a screenshot without its underlying comparison
does not establish a numerical claim. File existence checks verify navigation,
not mathematical content, numerical validity or rendered anchors.

Ordinary file links are the baseline. Obsidian backlinks, block identifiers and
embeds can improve a chosen local reading workflow, but must not be the only
locator needed by another reader. Keep a meaningful file/section description.
These distinctions follow the documented capabilities of
[MathJax](https://docs.mathjax.org/en/latest/input/tex/eqnumbers.html),
[Obsidian links](https://obsidian.md/help/links) and
[GitHub mathematics](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions).
They do not certify a particular host's rendering configuration.
