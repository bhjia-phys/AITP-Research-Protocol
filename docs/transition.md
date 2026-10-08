# Replacing the legacy implementation

AITP now consists of article-centred memory, research Skills and learning through
direct Skill distillation. The active bundle is `plugins/aitp`, with seven core
Skills: memory (the entry and research cycle), research, verify, writing and
distillation, plus the two conditional interaction Skills, human-brainstorming and
human-learning. Taste remains future work.

The earlier ledger runtime, stage machinery, schemas and adapter contracts are
retired from the active tree. Published Git history remains intact. This is a
replacement implementation, not compatibility with the old command or adapter.
Retire an installed legacy integration explicitly when adopting the new bundle;
a host's separate legacy research mode is not implemented by this plugin.

Writing incorporates the former Witten-style and computational writing guidance.
Asset placement follows the existing README and working locations. The main
note develops the argument through detailed notes and their supporting assets;
optional layouts help new topics start without requiring a directory tree or
automatic migration. First entry includes resolving consequential scope questions
with the researcher before drafting or consolidating the main note.

The 1.1.0 release included one small generic teaching example, now retired from
the development tree. Proposed LibRPA and topological-phase/anomaly examples
remain outside the public tree until author review. General methods can be
included under `aitp-research/methods/` independently of those examples. Private
research examples and their evaluation records are retained outside the published tree.
Unpublished commits containing them were excluded from the release ancestry.
This does not erase any material already present in older published history.

Codex and Hakimi expose the same seven core Skills; how a nested method Skill is exposed
differs by host, as the README explains. Start a new host thread after
replacing an installed version. See [validation](validation.md) for the bounded
checks and their limits.
