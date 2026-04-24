"""Demo script: run Phase 4 visualizations with real physics data."""

import tempfile, shutil
from pathlib import Path
from brain.mcp_server import (
    aitp_create_l2_node, aitp_create_l2_edge, aitp_create_l2_tower,
    aitp_visualize_eft_tower, aitp_visualize_derivation_chain,
    aitp_visualize_knowledge_graph, aitp_update_l2_node,
    _global_l2_path, _parse_md, _write_md,
)

td = tempfile.mkdtemp()
Path(td).joinpath("topics").mkdir()

# --- Create physics nodes ---
aitp_create_l2_node(td, "classical-em", "concept", "Classical Electrodynamics",
    physical_meaning="Maxwell equations governing EM fields in flat spacetime",
    mathematical_expression="dF = 0, d*F = J",
    regime_of_validity="v << c, hbar -> 0, no quantum effects",
    tower="em-tower", energy_scale="< eV")

aitp_create_l2_node(td, "qed", "concept", "Quantum Electrodynamics",
    physical_meaning="Quantum theory of EM interaction via photon exchange",
    mathematical_expression="L = psi_bar(iD - m)psi - 1/4 F^2",
    regime_of_validity="alpha << 1, E < 100 GeV",
    tower="em-tower", energy_scale="eV - GeV")

aitp_create_l2_node(td, "maxwell-eq", "theorem", "Maxwell's Equations",
    physical_meaning="Four coupled PDEs describing EM field evolution",
    mathematical_expression="div E = rho/eps0, curl B - dE/dt = mu0 J",
    regime_of_validity="classical, no quantum", energy_scale="< eV")

aitp_create_l2_node(td, "coulomb-law", "result", "Coulomb Law",
    physical_meaning="Electrostatic force between two point charges",
    mathematical_expression="F = q1*q2 / 4*pi*eps0*r^2",
    regime_of_validity="static, point charges, non-relativistic",
    energy_scale="< eV")

aitp_create_l2_node(td, "anomalous-moment", "result", "Electron Anomalous Magnetic Moment",
    physical_meaning="Deviation of g-factor from 2 due to QFT radiative corrections",
    mathematical_expression="a_e = alpha/2pi + O(alpha^2)",
    regime_of_validity="perturbative QED, alpha << 1",
    energy_scale="meV - GeV")

aitp_create_l2_node(td, "wkb", "approximation", "WKB Approximation",
    physical_meaning="Semiclassical approximation for slowly varying potentials",
    regime_of_validity="hbar -> 0 limit, smooth potentials",
    energy_scale="generic")

aitp_create_l2_node(td, "hierarchy-problem", "open_question", "Hierarchy Problem",
    physical_meaning="Why is the Higgs mass so much smaller than the Planck mass?",
    regime_of_validity="BSM scale M_Planck ~ 10^19 GeV",
    energy_scale="> TeV")

aitp_create_l2_node(td, "qft-to-classical", "regime_boundary", "QFT-Classical Boundary",
    physical_meaning="Boundary where quantum field effects become negligible",
    regime_of_validity="hbar -> 0, alpha -> 0, single-particle limit",
    energy_scale="< meV")

aitp_create_l2_node(td, "qed-derivation", "derivation_chain",
    "QED Coulomb from Photon Exchange",
    physical_meaning="Deriving classical Coulomb law from QED tree-level scattering",
    regime_of_validity="alpha << 1, static limit",
    energy_scale="eV - GeV")

# Trust levels
aitp_update_l2_node(td, "maxwell-eq", trust_level="independently_verified")
aitp_update_l2_node(td, "coulomb-law", trust_level="validated")
aitp_update_l2_node(td, "anomalous-moment", trust_level="multi_source_confirmed")

# --- Create edges ---
aitp_create_l2_edge(td, "qed-limits-classical", "qed", "classical-em", "limits_to",
    regime_condition="alpha -> 0, hbar -> 0, single-photon exchange")
aitp_create_l2_edge(td, "qed-uses-maxwell", "qed", "maxwell-eq", "uses",
    regime_condition="classical limit")
aitp_create_l2_edge(td, "maxwell-implies-coulomb", "maxwell-eq", "coulomb-law", "derives_from",
    regime_condition="static, point charge, Gauss law")
aitp_create_l2_edge(td, "qed-derives-coulomb", "qed-derivation", "coulomb-law", "derives_from")
aitp_create_l2_edge(td, "qed-der-uses-qed", "qed-derivation", "qed", "uses")
aitp_create_l2_edge(td, "anomalous-from-qed", "anomalous-moment", "qed", "derives_from",
    regime_condition="perturbative expansion")
aitp_create_l2_edge(td, "wkb-emerges", "wkb", "qft-to-classical", "emerges_from",
    regime_condition="hbar -> 0")
aitp_create_l2_edge(td, "hierarchy-motivates", "hierarchy-problem", "qed", "motivates")

# Mark one correspondence as verified
g2 = _global_l2_path(td)
edge_path = g2 / "graph" / "edges" / "qed-limits-classical.md"
fm, body = _parse_md(edge_path)
fm["correspondence_verified"] = True
_write_md(edge_path, fm, body)

# --- Create derivation chain with steps ---
chain_path = g2 / "graph" / "nodes" / "qed-derivation.md"
fm, _ = _parse_md(chain_path)
_write_md(chain_path, fm,
    "# QED Coulomb from Photon Exchange\n\n"
    "## Steps\n\n"
    "- Write QED Lagrangian with electron and photon fields\n"
    "- Compute tree-level e-e scattering amplitude\n"
    "- Take non-relativistic static limit: p -> 0\n"
    "- Fourier transform momentum-space amplitude to position space\n"
    "- Recover V(r) = e^2 / 4*pi*r, i.e. Coulomb potential\n"
)

# --- Create EFT tower ---
layers = [
    {"id": "classical-em", "energy_scale": "< meV", "theories": "classical-em, coulomb-law, maxwell-eq"},
    {"id": "nonrel-qm", "energy_scale": "meV - eV", "theories": "wkb"},
    {"id": "qed", "energy_scale": "eV - GeV", "theories": "qed, anomalous-moment, qed-derivation"},
    {"id": "bsm", "energy_scale": "> TeV", "theories": "hierarchy-problem"},
]
aitp_create_l2_tower(td, "em-tower", "Electromagnetic EFT Tower", "meV - TeV+", layers=layers)

# ================================================================
# PRINT VISUALIZATIONS
# ================================================================
SEP = "=" * 72

print(SEP)
print("  EFT TOWER VISUALIZATION")
print(SEP)
r = aitp_visualize_eft_tower(td, "em-tower")
print(r["ascii"])
print()
print("Metadata:", r["metadata"])

print()
print(SEP)
print("  DERIVATION CHAIN VISUALIZATION")
print(SEP)
r = aitp_visualize_derivation_chain(td, "qed-derivation")
print(r["ascii"])
print()
print("Metadata:", r["metadata"])

print()
print(SEP)
print("  KNOWLEDGE GRAPH VISUALIZATION")
print(SEP)
r = aitp_visualize_knowledge_graph(td)
print(r["ascii"])
print()
print("Metadata:", r["metadata"])

shutil.rmtree(td)
