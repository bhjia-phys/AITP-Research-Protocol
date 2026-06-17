"""Create AITP v2 topics from scattered research directories.

1. gw-topology-greens-function  <- gw-topology-theory/ + librpa/
2. quantum-gravity-von-neumann  <- Quantum-Gravity-Algebra-Study/ (replaces bare jones-von-neumann-algebras)
3. mipt-vonneumann-unification  <- mipt-algebra-gravity-unification/
4. Merge hs-like-chaos-window/ local content into existing quantum-chaos-long-range-spin-chains
"""

import shutil
import os
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_WORKSPACE = Path(os.environ.get("AITP_WORKSPACE_ROOT", str(Path.cwd())))
TOPICS_ROOT = Path(os.environ.get("AITP_TOPICS_ROOT", str(DEFAULT_WORKSPACE / "research" / "aitp-topics")))
RESEARCH_ROOT = Path(os.environ.get("AITP_RESEARCH_ROOT", str(DEFAULT_WORKSPACE / "research")))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_md(path: Path, frontmatter: dict, body: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---\n"]
    for k, v in frontmatter.items():
        if isinstance(v, bool):
            lines.append(f"{k}: {str(v).lower()}\n")
        elif isinstance(v, (int, float)):
            lines.append(f"{k}: {v}\n")
        elif isinstance(v, str):
            escaped = v.replace('"', '\\"')
            lines.append(f'{k}: "{escaped}"\n')
        else:
            lines.append(f"{k}: {v}\n")
    lines.append("---\n")
    lines.append(body if body.startswith("\n") else "\n" + body)
    path.write_text("".join(lines), encoding="utf-8")


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ─── Helpers for topic creation ───────────────────────────────────────────

def create_state(slug: str, title: str, question: str, lane: str, stage: str = "L1",
                 posture: str = "read", l3_subplane: str = ""):
    fm = {
        "topic_slug": slug,
        "title": title,
        "stage": stage,
        "posture": posture,
        "lane": lane,
        "status": "new",
        "gate_status": "ready",
        "mode": "explore",
        "sources_count": 0,
        "candidates_count": 0,
        "created_at": _now(),
        "updated_at": _now(),
    }
    if l3_subplane:
        fm["l3_subplane"] = l3_subplane
    body = f"\n# {title}\n\n## Research Question\n{question}\n\n"
    _write_md(TOPICS_ROOT / slug / "state.md", fm, body)


def register_source(slug: str, source_id: str, title: str, stype: str = "paper",
                    arxiv_id: str = "", notes: str = ""):
    src_dir = TOPICS_ROOT / slug / "L0" / "sources"
    fm = {
        "source_id": source_id,
        "type": stype,
        "title": title,
        "arxiv_id": arxiv_id,
        "fidelity": "arxiv_preprint" if arxiv_id else "published",
        "registered": _now(),
    }
    body = f"\n# {title}\n\n{notes}\n\n" if notes else f"\n# {title}\n\n"
    _write_md(src_dir / f"{source_id}.md", fm, body)
    # Update source count in state
    state_path = TOPICS_ROOT / slug / "state.md"
    state_text = _read_file(state_path)
    src_dir_path = TOPICS_ROOT / slug / "L0" / "sources"
    count = len(list(src_dir_path.glob("*.md")))
    import re
    state_text = re.sub(r"sources_count: \d+", f"sources_count: {count}", state_text)
    state_path.write_text(state_text, encoding="utf-8")


def fill_l1(slug: str, question: str, scope: list[str], observables: list[str],
            notation: list[str] = None, anchors: list[str] = None):
    l1 = TOPICS_ROOT / slug / "L1"
    l1.mkdir(parents=True, exist_ok=True)
    ts = _now()

    _write_md(l1 / "question_contract.md", {
        "bounded_question": question,
        "scope_boundaries": "; ".join(scope),
        "target_quantities": "; ".join(observables),
        "created_at": ts,
    }, (
        "# Question Contract\n\n"
        "## Bounded Question\n\n"
        f"{question}\n\n"
        "## Scope Boundaries\n\n" +
        "\n".join(f"- {s}" for s in scope) + "\n\n"
        "## Target Quantities Or Claims\n\n" +
        "\n".join(f"- {o}" for o in observables) + "\n"
    ))

    _write_md(l1 / "source_basis.md", {
        "core_sources": "see L0/sources/",
        "peripheral_sources": "see research directory literature/",
        "created_at": ts,
    }, (
        "# Source Basis\n\n"
        "## Core Sources\n\n"
        "Registered via L0/sources/.\n\n"
        "## Peripheral Sources\n\n"
        "See research directory for literature files.\n\n"
        "## Why Each Source Matters\n\n"
        "Source relevance established during initial research.\n"
    ))

    notation = notation or ["natural units (hbar=1)", "standard condensed matter notation"]
    _write_md(l1 / "convention_snapshot.md", {
        "notation_choices": "; ".join(notation),
        "unit_conventions": "natural units",
        "created_at": ts,
    }, (
        "# Convention Snapshot\n\n"
        "## Notation Choices\n\n" +
        "\n".join(f"- {n}" for n in notation) + "\n\n"
        "## Unit Conventions\n\n"
        "Natural units where applicable.\n\n"
        "## Unresolved Tensions\n\n"
        "None recorded.\n"
    ))

    anchors = anchors or ["see target_quantities above"]
    _write_md(l1 / "derivation_anchor_map.md", {
        "starting_anchors": "; ".join(anchors),
        "created_at": ts,
    }, (
        "# Derivation Anchor Map\n\n"
        "## Source Anchors\n\n" +
        "\n".join(f"- {a}" for a in anchors) + "\n\n"
        "## Candidate Starting Points\n\n"
        "To be determined during L3.\n"
    ))

    _write_md(l1 / "contradiction_register.md", {
        "blocking_contradictions": "none",
        "created_at": ts,
    }, (
        "# Contradiction Register\n\n"
        "## Unresolved Source Conflicts\n\n"
        "None recorded.\n\n"
        "## Blocking Status\n\n"
        "No blocking contradictions.\n"
    ))


def create_l3_skeleton(slug: str, subplane: str = "analysis"):
    l3 = TOPICS_ROOT / slug / "L3"
    subplanes = ["ideation", "planning", "analysis", "result_integration", "distillation"]
    for sp in subplanes:
        sp_dir = l3 / sp
        sp_dir.mkdir(parents=True, exist_ok=True)
        active_names = {
            "ideation": "active_idea.md",
            "planning": "active_plan.md",
            "analysis": "active_analysis.md",
            "result_integration": "active_integration.md",
            "distillation": "active_distillation.md",
        }
        _write_md(sp_dir / active_names[sp], {
            "status": "draft",
            "created_at": _now(),
        }, f"\n# {sp.title()} Artifact\n\nPlaceholder.\n\n")
    (l3 / "candidates").mkdir(parents=True, exist_ok=True)
    (l3 / "tex").mkdir(parents=True, exist_ok=True)


def copy_to_runtime(slug: str, src_dir: Path, prefix: str = ""):
    runtime = TOPICS_ROOT / slug / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    prefix = prefix or "orig_"
    count = 0
    for f in src_dir.rglob("*.md"):
        if f.is_file():
            rel = f.relative_to(src_dir)
            dest = runtime / f"{prefix}{rel.stem}.md"
            if not dest.exists():
                content = _read_file(f)
                _write_md(dest, {"imported_from": str(src_dir.name)}, f"\n{content}\n")
                count += 1
    for f in src_dir.rglob("*.bib"):
        if f.is_file():
            rel = f.relative_to(src_dir)
            dest = runtime / f"{prefix}{rel.stem}.bib"
            if not dest.exists():
                shutil.copy2(f, dest)
                count += 1
    for f in src_dir.rglob("*.tex"):
        if f.is_file():
            rel = f.relative_to(src_dir)
            dest = runtime / f"{prefix}{rel.stem}.tex"
            if not dest.exists():
                shutil.copy2(f, dest)
                count += 1
    return count


# ─── Topic 1: GW Topology & Green Function ────────────────────────────────

def create_gw_topology():
    slug = "gw-topology-greens-function"
    print(f"\n=== Creating {slug} ===")
    topic_root = TOPICS_ROOT / slug
    if topic_root.exists():
        shutil.rmtree(topic_root)

    question = (
        "How do QSGW self-energy corrections affect topological invariants (Chern number, Z2), "
        "and can these invariants be computed directly from the Matsubara-axis Green function "
        "via the Ishikawa-Matsuyama formula?"
    )
    scope = [
        "Route 1: quasiparticle wavefunction + Berry curvature post-processing",
        "Route 2: Green function + Ishikawa-Matsuyama / Wang-Zhang formalism",
        "Test materials: Haldane model -> Bi2Se3",
        "Implementation target: LibRPA Matsubara data -> topological Hamiltonian",
    ]
    observables = [
        "Chern number: Green-function formula vs wavefunction-based comparison",
        "Z2 invariant: Wang-Zhang formula applied to QSGW output",
        "Topological Hamiltonian H_top(k) = H_0(k) + Sigma(i0, k) - mu",
        "Band gap correction: QSGW vs KS-DFT for topological materials",
    ]

    create_state(slug, "GW Self-Energy Corrections to Topological Invariants",
                 question, "formal_theory", stage="L1", posture="frame")

    # Register sources
    sources = [
        ("ishikawa-matsuyama-1987", "Topological invariant from Green function (Ishikawa-Matsuyama)",
         "paper", "", "N3[G] formula for Chern number from full Green function"),
        ("gurarie-2011", "Single-particle Green's functions and interacting topological insulators",
         "paper", "", "Extension of topological invariants to interacting systems via Green function"),
        ("wang-zhang-2012", "Simplified topological invariants for interacting insulators",
         "paper", "", "Z2 invariant from Green function; key for route 2"),
        ("van-schilfgaarde-2006", "Quasiparticle self-consistent GW theory",
         "paper", "", "QSGW method foundation"),
        ("aryasetiawan-1998", "The GW method (review)",
         "paper", "", "Comprehensive GW method reference"),
        ("zhou-liu-2020", "Green's function formalism and topological invariants",
         "paper", "", "Geometric derivation connecting Green function to topology"),
        ("li-kee-kim-2022", "Green's function approach to interacting higher-order topological insulators",
         "paper", "", "Extension to higher-order topology"),
    ]
    for sid, title, stype, arxiv, notes in sources:
        register_source(slug, sid, title, stype, arxiv, notes)

    fill_l1(slug, question, scope, observables,
            notation=["standard condensed matter notation (k-space, BZ)",
                       "Matsubara frequency iomega_n convention",
                       "Green function G(k, iomega) formalism"],
            anchors=["Berry curvature -> Chern number (TKNN)",
                      "Ishikawa-Matsuyama N3[G] formula",
                      "Wang-Zhang Z2 formula",
                      "Topological Hamiltonian H_top(k) = H_0(k) + Sigma(i0,k) - mu"])

    # Copy original research files
    n1 = copy_to_runtime(slug, RESEARCH_ROOT / "gw-topology-theory", prefix="gw_topo_")
    n2 = copy_to_runtime(slug, RESEARCH_ROOT / "librpa", prefix="librpa_")
    print(f"  Sources: {len(sources)}, Runtime files: {n1 + n2}")
    print(f"  Done: {slug} at L1")


# ─── Topic 2: Quantum Gravity & Von Neumann Algebras ──────────────────────

def create_quantum_gravity_vna():
    slug = "quantum-gravity-von-neumann"
    print(f"\n=== Creating {slug} ===")
    topic_root = TOPICS_ROOT / slug
    if topic_root.exists():
        shutil.rmtree(topic_root)

    # Also remove old bare jones topic if it exists
    old_slug = "jones-von-neumann-algebras"
    old_topic = TOPICS_ROOT / old_slug
    if old_topic.exists():
        print(f"  Removing superseded topic: {old_slug}")
        shutil.rmtree(old_topic)

    question = (
        "How do von Neumann algebra type transitions (Type III -> Type II) arise in quantum gravity, "
        "and what is the precise relationship between algebra type, entanglement entropy finiteness, "
        "and background independence?"
    )
    scope = [
        "Von Neumann algebra classification (Type I, II_1, II_inf, III) in QFT",
        "Witten 2023 background-independent algebra framework",
        "Hong Liu group: large N algebras and type transitions",
        "Chandrasekaran et al. 2022: gravity-induced algebra type change",
        "Jones index and subfactor theory connections",
    ]
    observables = [
        "Algebra type transition mechanism: continuous or abrupt?",
        "Entanglement entropy behavior per algebra type",
        "Background independence <-> Type II emergence",
        "Critical conditions for Type III -> Type II transition",
    ]

    create_state(slug, "Von Neumann Algebra Type Transitions in Quantum Gravity",
                 question, "formal_theory", stage="L1", posture="read")

    sources = [
        ("witten-2023-bg-indep", "Witten 2023: Background Independent Algebra in Quantum Gravity",
         "paper", "", "Core framework for algebra types in gravitational QFT"),
        ("chandrasekaran-2022-large-N", "Chandrasekaran et al. 2022: Large N algebras and quantum gravity",
         "paper", "", "Gravity-induced algebra type change from Type III to Type II"),
        ("gesteau-liu-2024-stringy", "Gesteau-Liu 2024: Toward Stringy Horizons",
         "paper", "", "String-theoretic approach to gravitational algebras"),
        ("jones-vna-index", "Jones index and subfactor theory for von Neumann algebras",
         "paper", "", "Mathematical foundation for algebra classification"),
        ("hong-liu-timeline-2012-2025", "Hong Liu research group: large N algebras body of work",
         "paper", "", "Extended research program on algebra-gravity connections"),
    ]
    for sid, title, stype, arxiv, notes in sources:
        register_source(slug, sid, title, stype, arxiv, notes)

    fill_l1(slug, question, scope, observables,
            notation=["von Neumann algebra standard notation (M, N, type classification)",
                       "Algebraic QFT notation (local algebras A(O))",
                       "Jones index [M:N] notation"],
            anchors=["Type III_1 algebras in QFT (standard result)",
                      "Type II_1 emergence in gravitational context (Chandrasekaran et al.)",
                      "Background independence constraint (Witten 2023)",
                      "30+ research questions from study guide"])

    n = copy_to_runtime(slug, RESEARCH_ROOT / "Quantum-Gravity-Algebra-Study", prefix="qg_vna_")
    print(f"  Sources: {len(sources)}, Runtime files: {n}")
    print(f"  Done: {slug} at L1 (superseded old jones-von-neumann-algebras)")


# ─── Topic 3: MIPT + Von Neumann + Background Independence Unification ───

def create_mipt_unification():
    slug = "mipt-vonneumann-unification"
    print(f"\n=== Creating {slug} ===")
    topic_root = TOPICS_ROOT / slug
    if topic_root.exists():
        shutil.rmtree(topic_root)

    question = (
        "Can measurement-induced phase transitions (MIPT), von Neumann algebra type transitions, "
        "and background independence be unified in a single framework via the measured SYK model, "
        "and what does the resulting phase diagram reveal about the deep connection between "
        "quantum measurement, entanglement, and spacetime?"
    )
    scope = [
        "Measured SYK model as the concrete unifying platform",
        "Replica trick for phase structure analysis",
        "Von Neumann algebra type analysis in MIPT context",
        "Background independence constraint from gravitational dual",
        "Tensor network realization of the unified framework",
    ]
    observables = [
        "Unified phase diagram: MIPT x algebra type x background independence",
        "Critical measurement rate for MIPT transition",
        "Algebra type at each phase of the measured SYK model",
        "Background independence constraint on the phase boundary",
    ]

    create_state(slug,
                 "MIPT, Von Neumann Algebra Type Transitions, and Background Independence: "
                 "A Unified Framework via the Measured SYK Model",
                 question, "formal_theory", stage="L3", posture="derive", l3_subplane="distillation")

    sources = [
        ("measured-syk-model", "Measured SYK model: MIPT platform",
         "paper", "", "Concrete model for MIPT with algebraic analysis"),
        ("mipt-review", "Measurement-induced phase transition literature",
         "paper", "", "MIPT phenomenology and criticality"),
        ("vna-type-transition", "Von Neumann algebra type transitions in quantum systems",
         "paper", "", "Algebra type classification and transitions"),
        ("background-independence-witten", "Background independence in algebraic QFT",
         "paper", "", "Witten's constraint on gravitational algebras"),
        ("tensor-network-mipt", "Tensor network realization of MIPT",
         "paper", "", "Tensor network perspective on measurement transitions"),
    ]
    for sid, title, stype, arxiv, notes in sources:
        register_source(slug, sid, title, stype, arxiv, notes)

    fill_l1(slug, question, scope, observables,
            notation=["SYK model notation (q_ij random couplings)",
                       "Replica trick notation (n -> 1 limit)",
                       "von Neumann algebra type classification",
                       "Measurement operator notation"],
            anchors=["MIPT known phenomenology",
                      "SYK solvable large-N limit",
                      "Replica trick for entanglement entropy",
                      "Tensor network-MIPT correspondence"])

    create_l3_skeleton(slug, "distillation")

    # Fill L3 analysis with paper structure
    l3_analysis = topic_root / "L3" / "analysis" / "derivation_log.md"
    _write_md(l3_analysis, {
        "status": "draft_paper_exists",
        "evidence_count": 8,
        "created_at": _now(),
    }, (
        "# Derivation Log\n\n"
        "## Paper Structure (Complete LaTeX Draft)\n\n"
        "1. Introduction\n"
        "2. Mathematical Preliminaries\n"
        "3. The Measured SYK Model\n"
        "4. Replica Trick and Phase Structure\n"
        "5. Von Neumann Algebra Type Analysis\n"
        "6. Background-Independence Constraint\n"
        "7. The Unified Phase Diagram\n"
        "8. Tensor Network Realization\n"
        "9. Open Problems and Conjectures\n"
        "10. Discussion and Outlook\n\n"
        "## Key Results\n\n"
        "- Unified phase diagram connecting MIPT, algebra type, and background independence\n"
        "- Measured SYK model as concrete realization\n"
        "- Tensor network interpretation\n\n"
        "## Open Gaps\n\n"
        "- Numerical validation of critical exponents\n"
        "- Extension beyond large-N limit\n"
        "- Connection to holographic duality\n"
    ))

    n = copy_to_runtime(slug, RESEARCH_ROOT / "mipt-algebra-gravity-unification", prefix="mipt_")
    print(f"  Sources: {len(sources)}, Runtime files: {n}")
    print(f"  Done: {slug} at L3 (draft paper)")


# ─── Topic 4: Merge hs-like-chaos-window into existing quantum-chaos topic ─

def merge_hs_like_chaos_window():
    slug = "quantum-chaos-long-range-spin-chains"
    print(f"\n=== Merging hs-like-chaos-window into {slug} ===")

    src_dir = RESEARCH_ROOT / "hs-like-chaos-window"
    if not src_dir.exists():
        print(f"  Source directory not found: {src_dir}")
        return

    n = copy_to_runtime(slug, src_dir, prefix="local_")
    print(f"  Copied {n} files to runtime/")

    # Also copy code configs and result JSONs as reference
    runtime = TOPICS_ROOT / slug / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)

    count_extra = 0
    for pattern in ["code/configs/*.json", "results/**/*.json", "benchmarks/**/*.json"]:
        for f in src_dir.glob(pattern):
            if f.is_file():
                dest = runtime / f"local_{f.stem}.json"
                if not dest.exists():
                    shutil.copy2(f, dest)
                    count_extra += 1
    print(f"  Copied {count_extra} extra data files")
    print(f"  Done: merged hs-like-chaos-window content into {slug}")


# ─── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    create_gw_topology()
    create_quantum_gravity_vna()
    create_mipt_unification()
    merge_hs_like_chaos_window()

    # Summary
    print("\n=== Summary ===")
    for d in sorted(TOPICS_ROOT.iterdir()):
        if d.is_dir():
            state = d / "state.md"
            if state.exists():
                text = _read_file(state)
                import re
                stage = re.search(r"stage: (\S+)", text)
                title = re.search(r"title: (.+)", text)
                sources = len(list((d / "L0" / "sources").glob("*.md"))) if (d / "L0" / "sources").exists() else 0
                runtime_files = len(list((d / "runtime").glob("*"))) if (d / "runtime").exists() else 0
                print(f"  {d.name}: stage={stage.group(1) if stage else '?'}, "
                      f"sources={sources}, runtime={runtime_files}")

    print("\n=== Creation complete ===")
