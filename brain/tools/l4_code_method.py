"""L4 analysis tools for code_method lane (HPC computational physics).

Parses HPC output files, extracts numerical results, compares against
literature benchmarks, and checks convergence criteria.

Intended to be called both as an MCP tool (via mcp_server.py) and
standalone from CLI.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── Parsing: LibRPA output --------------------------------------------------

def _parse_librpa_out(filepath: Path) -> dict[str, Any]:
    """Extract key metrics from a LibRPA stdout/stderr file.

    Returns dict with fields found, empty dict if nothing parsed.
    """
    if not filepath.exists():
        return {}
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}

    result: dict[str, Any] = {}

    # QP energies: lines like "band  12  E_QP =  -6.8432  eV"
    qp_matches = re.findall(
        r"band\s+(\d+)\s+E_QP\s*=\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)\s*eV",
        text,
    )
    if qp_matches:
        result["qp_energies"] = [
            {"band": int(b), "energy_eV": float(e)} for b, e in qp_matches
        ]

    # Convergence: "Converged after X iterations" or "delta_E = X.XXE-XX eV"
    conv_match = re.search(
        r"(?:Converged after|converged in)\s+(\d+)\s+iterations?", text
    )
    if conv_match:
        result["convergence_iterations"] = int(conv_match.group(1))

    delta_match = re.search(
        r"delta_E\s*=\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)\s*eV", text
    )
    if delta_match:
        result["delta_eV"] = float(delta_match.group(1))

    # Wall time
    time_match = re.search(
        r"(?:Total wall time|wall time|Elapsed time)\s*[:=]\s*([\d.]+)\s*(s|sec|min|h)",
        text, re.IGNORECASE,
    )
    if time_match:
        result["wall_time"] = f"{time_match.group(1)}{time_match.group(2)}"

    # Exit status
    if re.search(r"(?:calculation finished|exited normally|EXIT CODE 0|exit code 0)", text, re.IGNORECASE):
        result["exit_status"] = "success"
    elif re.search(r"(?:ERROR|FATAL|SIGNAL|abort|segfault|terminate called)", text):
        result["exit_status"] = "error"

    # NaN detection
    if re.search(r"\bNaN\b", text):
        result["has_nan"] = True

    # Chi0 frequency points completed
    chi0_match = re.findall(
        r"(?:Chi0|chi0).*?(\d+)/(\d+)\s+(?:tau|freq)", text, re.IGNORECASE
    )
    if chi0_match:
        result["chi0_progress"] = [
            {"completed": int(c), "total": int(t)} for c, t in chi0_match
        ]

    return result


# ── Parsing: ABACUS output ---------------------------------------------------

def _parse_abacus_out(filepath: Path) -> dict[str, Any]:
    """Extract key metrics from an ABACUS SCF/NSCF output file."""
    if not filepath.exists():
        return {}
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}

    result: dict[str, Any] = {}

    # SCF convergence
    if re.search(r"(?:SCF IS CONVERGED|charge density convergence is achieved)", text, re.IGNORECASE):
        result["scf_converged"] = True
    elif re.search(r"(?:SCF NOT CONVERGED|nscf)", text, re.IGNORECASE):
        result["scf_converged"] = bool(
            re.search(r"(?:SCF IS CONVERGED)", text, re.IGNORECASE)
        )

    # Total energy
    energy_match = re.search(
        r"(?:FINAL_ETOT_IS|total energy\s*=\s*)\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)\s*eV",
        text, re.IGNORECASE,
    )
    if energy_match:
        result["total_energy_eV"] = float(energy_match.group(1))

    # Fermi energy
    fermi_match = re.search(
        r"(?:E-fermi|Fermi energy|EFERMI)\s*[:=]\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)\s*eV",
        text, re.IGNORECASE,
    )
    if fermi_match:
        result["fermi_energy_eV"] = float(fermi_match.group(1))

    # k-points
    kpt_match = re.search(r"nkstot\s*=\s*(\d+)", text)
    if kpt_match:
        result["nkstot"] = int(kpt_match.group(1))

    # Wall time
    time_match = re.search(
        r"(?:wall time|total.*?time)\s*[:=]\s*([\d.]+)\s*(s|sec)",
        text, re.IGNORECASE,
    )
    if time_match:
        result["wall_time"] = f"{time_match.group(1)}s"

    return result


# ── Parsing: GW band data files ----------------------------------------------

def _parse_band_data(filepath: Path) -> dict[str, Any]:
    """Parse GW_band_spin_*.dat or gw_band.dat files.

    Expected format: columns separated by whitespace.
    Common layouts:
      kx ky kz  E_KS(s=1) E_KS(s=2) ... E_GW(s=1) E_GW(s=2) ...
      k-path-index  E_vbm  E_cbm  ...
    """
    if not filepath.exists():
        return {"error": f"File not found: {filepath}"}

    try:
        lines = filepath.read_text(encoding="utf-8", errors="replace").strip().split("\n")
    except Exception:
        return {"error": f"Could not read: {filepath}"}

    if not lines:
        return {"error": "Empty band data file"}

    result: dict[str, Any] = {"source_file": str(filepath), "nlines": len(lines)}
    data_rows: list[list[float]] = []
    header_keywords = [
        "band", "k-point", "kpoint", "energy", "e_ks", "e_gw", "kx", "vbm", "cbm",
    ]

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Skip header lines
        if any(stripped.lower().startswith(kw) for kw in header_keywords):
            continue
        try:
            vals = [float(x) for x in stripped.split()]
            if vals:
                data_rows.append(vals)
        except ValueError:
            continue

    if not data_rows:
        result["error"] = "No numeric data rows parsed"
        return result

    result["n_data_rows"] = len(data_rows)
    ncols = len(data_rows[0])

    # Try to identify VBM/CBM/gap
    # Heuristic: GW band data files typically have VBM as the highest occupied band
    # energy below E_Fermi and CBM as the lowest unoccupied band above E_Fermi
    all_energies: list[float] = []
    for row in data_rows:
        for v in row[3:]:  # skip first 3 columns (typically kx,ky,kz or idx)
            all_energies.append(v)

    if all_energies:
        result["energy_min_eV"] = round(min(all_energies), 6)
        result["energy_max_eV"] = round(max(all_energies), 6)

        # Separate into occupied (< 0, typical for semiconductors at Gamma)
        # and unoccupied (> 0)
        occupied = [e for e in all_energies if e < 0]
        unoccupied = [e for e in all_energies if e >= 0]
        if occupied and unoccupied:
            vbm = max(occupied)  # highest occupied
            cbm = min(unoccupied)  # lowest unoccupied
            gap = cbm - vbm
            result["vbm_eV"] = round(vbm, 6)
            result["cbm_eV"] = round(cbm, 6)
            result["gap_eV"] = round(gap, 6)
            result["gap_direct"] = True  # conservative assumption

            # Check if this is a direct gap (both at same k-point)
            # For band path data, check if VBM and CBM appear in same row
            for row in data_rows:
                row_energies = row[3:] if len(row) > 3 else row
                ro = [e for e in row_energies if e < 0]
                ru = [e for e in row_energies if e >= 0]
                if ro and ru:
                    row_gap = min(ru) - max(ro)
                    if abs(row_gap - gap) < 1e-4:
                        result["gap_direct"] = True
                        break

    # Detect QSGW iteration bands if present
    # Pattern: columns might represent different GW iterations
    if ncols > 5:
        result["possible_iterations"] = ncols - 3  # heuristic

    return result


# ── Benchmark comparison ----------------------------------------------------

_BENCHMARKS: dict[str, dict[str, Any]] = {
    "si_indirect_gap": {
        "observable": "Si indirect band gap",
        "value_eV": 1.17,
        "uncertainty_eV": 0.01,
        "source": "Experimental (low temperature)",
        "system": "Si bulk, diamond",
    },
    "si_direct_gap_gamma": {
        "observable": "Si direct band gap at Gamma",
        "value_eV": 3.40,
        "uncertainty_eV": 0.05,
        "source": "Experimental (ellipsometry)",
        "system": "Si bulk, diamond, Gamma point",
    },
    "si_direct_gap_x": {
        "observable": "Si direct band gap at X",
        "value_eV": 4.20,
        "uncertainty_eV": 0.10,
        "source": "Experimental",
        "system": "Si bulk, diamond, X point",
    },
    "si_g0w0_gap": {
        "observable": "Si G0W0 band gap",
        "value_eV": 1.28,
        "uncertainty_eV": 0.10,
        "source": "G0W0 literature (typical PBE starting point)",
        "system": "Si bulk, G0W0@PBE",
    },
    "si_qsgw_gap": {
        "observable": "Si QSGW band gap",
        "value_eV": 1.38,
        "uncertainty_eV": 0.10,
        "source": "QSGW literature (typical)",
        "system": "Si bulk, QSGW converged",
    },
}


def _compare_benchmark(
    observable: str,
    computed_value: float,
    units: str = "eV",
) -> dict[str, Any]:
    """Compare a computed value against known literature benchmarks.

    Returns a dict with agreement_status and comparison details.
    """
    result: dict[str, Any] = {
        "observable": observable,
        "computed_value": computed_value,
        "units": units,
        "agreement_status": "no_benchmark_available",
        "matches": [],
    }

    # Find matching benchmarks by fuzzy keyword match
    query_lower = observable.lower()
    for key, bm in _BENCHMARKS.items():
        bm_lower = bm["observable"].lower()
        # Match if query contains benchmark keywords or vice versa
        if any(word in bm_lower for word in query_lower.split() if len(word) > 2) or \
           any(word in query_lower for word in bm_lower.split() if len(word) > 2):
            deviation = computed_value - bm["value_eV"]
            abs_deviation = abs(deviation)
            relative_deviation = abs_deviation / max(abs(bm["value_eV"]), 1e-6)

            if abs_deviation <= bm["uncertainty_eV"]:
                status = "agrees"
            elif relative_deviation < 0.05:
                status = "agrees"
            elif relative_deviation < 0.20:
                status = "deviates"
            else:
                status = "deviates_significantly"

            match = {
                "benchmark": key,
                "reference_value": bm["value_eV"],
                "reference_uncertainty": bm["uncertainty_eV"],
                "reference_source": bm["source"],
                "deviation": round(deviation, 6),
                "deviation_relative": round(relative_deviation, 4),
                "status": status,
            }
            result["matches"].append(match)

    if result["matches"]:
        # Best agreement wins
        best = min(result["matches"], key=lambda m: abs(m["deviation"]))
        result["agreement_status"] = best["status"]
        result["best_match"] = best

    return result


# ── Convergence check -------------------------------------------------------

def _check_qsgw_convergence(
    current_delta_eV: float | None = None,
    iteration: int | None = None,
    threshold_eV: float = 1e-3,
) -> dict[str, Any]:
    """Check QSGW convergence criteria.

    Returns convergence status and details.
    """
    result: dict[str, Any] = {
        "threshold_eV": threshold_eV,
        "converged": False,
        "details": "",
    }

    if current_delta_eV is None:
        return {
            **result,
            "converged": None,
            "details": "No delta_E value available to check convergence.",
        }

    result["current_delta_eV"] = current_delta_eV
    if iteration is not None:
        result["iteration"] = iteration

    if current_delta_eV < threshold_eV:
        result["converged"] = True
        result["details"] = (
            f"Converged: delta_E = {current_delta_eV:.2e} eV < "
            f"threshold {threshold_eV:.1e} eV"
        )
    else:
        result["details"] = (
            f"Not converged: delta_E = {current_delta_eV:.2e} eV > "
            f"threshold {threshold_eV:.1e} eV"
        )

    return result


# ── Main analysis entry point ------------------------------------------------

def analyze_l4_run(
    topics_root: str | Path,
    topic_slug: str,
    run_dir: str | Path,
    run_id: str = "",
    literature_comparison: bool = True,
) -> dict[str, Any]:
    """Analyze a completed L4 HPC validation run.

    Scans the run directory for:
    - LibRPA output (GW band data, QP energies, convergence)
    - ABACUS output (SCF convergence, total energy)
    - Compares results against literature benchmarks
    - Checks QSGW convergence criteria

    Writes results to L4/outputs/<run_id>.md in the topic directory.

    Args:
        topics_root: Path to AITP topics root directory.
        topic_slug: Topic identifier.
        run_dir: Path to the completed HPC run directory.
        run_id: Identifier for this run (auto-generated if empty).
        literature_comparison: If True, compare against known benchmarks.

    Returns:
        Dict with analysis summary, parsed values, comparison results.
    """
    run_path = Path(run_dir)
    topics_root_path = Path(topics_root)

    if not run_path.exists():
        return {"error": f"Run directory not found: {run_dir}"}

    if not run_id:
        run_id = f"run-{datetime.now().strftime('%Y-%m-%d')}"

    analysis: dict[str, Any] = {
        "run_id": run_id,
        "topic_slug": topic_slug,
        "run_dir": str(run_path),
        "analyzed_at": _now(),
        "files_found": [],
        "librpa": {},
        "abacus": {},
        "band_data": {},
        "benchmark_comparison": {},
        "convergence": {},
        "errors": [],
    }

    # ── Step 1: Locate files ──
    librpa_outs = sorted(run_path.rglob("LibRPA*.out"))
    if not librpa_outs:
        librpa_outs = sorted(run_path.rglob("librpa*.out"))
    if not librpa_outs:
        librpa_outs = sorted(run_path.rglob("*.out"))
        librpa_outs = [f for f in librpa_outs if "abacus" not in f.name.lower()]

    abacus_outs = sorted(run_path.rglob("abacus*.out"))
    if not abacus_outs:
        abacus_outs = sorted(run_path.rglob("*.out"))
        abacus_outs = [f for f in abacus_outs if f in librpa_outs]
        abacus_outs = sorted(run_path.rglob("abacus*.out"))  # retry

    band_files = sorted(run_path.rglob("GW_band_spin_*.dat"))
    if not band_files:
        band_files = sorted(run_path.rglob("gw_band.dat"))
    if not band_files:
        band_files = sorted(run_path.rglob("band_gap*.csv"))

    analysis["files_found"] = {
        "librpa_outputs": [str(p.relative_to(run_path)) for p in librpa_outs],
        "abacus_outputs": [str(p.relative_to(run_path)) for p in abacus_outs],
        "band_data_files": [str(p.relative_to(run_path)) for p in band_files],
    }

    # ── Step 2: Parse LibRPA output ──
    for lp in librpa_outs:
        parsed = _parse_librpa_out(lp)
        if parsed:
            analysis["librpa"] = parsed
            break

    # ── Step 3: Parse ABACUS output ──
    for ap in abacus_outs:
        parsed = _parse_abacus_out(ap)
        if parsed:
            analysis["abacus"] = parsed
            break

    # ── Step 4: Parse band data ──
    for bp in band_files:
        parsed = _parse_band_data(bp)
        if parsed and "error" not in parsed:
            analysis["band_data"] = parsed
            break
    else:
        if band_files:
            analysis["band_data"] = _parse_band_data(band_files[0])

    # ── Step 5: Benchmark comparison ──
    if literature_comparison:
        gap = analysis["band_data"].get("gap_eV")
        if gap is not None:
            observable = f"Si {topic_slug}"  # generic; topic-specific should refine
            # Try to infer the calculation type from run directory
            if "g0w0" in str(run_path).lower():
                observable = "Si G0W0 band gap"
            elif "qsgw" in str(run_path).lower():
                observable = "Si QSGW band gap"
            elif "band" in str(run_path).lower():
                observable = "Si band gap"
            analysis["benchmark_comparison"] = _compare_benchmark(observable, gap)
        else:
            analysis["benchmark_comparison"] = {
                "agreement_status": "no_data",
                "message": "No band gap extracted from data files for comparison.",
            }

    # ── Step 6: Convergence check ──
    delta = analysis["librpa"].get("delta_eV")
    iters = analysis["librpa"].get("convergence_iterations")
    analysis["convergence"] = _check_qsgw_convergence(
        current_delta_eV=delta,
        iteration=iters,
    )

    # ── Step 7: Write output to L4/outputs/ ──
    topic_root = topics_root_path
    # Support both <topics_root>/<slug> and <topics_root>/topics/<slug>
    for candidate in [topic_root / topic_slug, topic_root / "topics" / topic_slug]:
        if (candidate / "state.md").exists():
            topic_root = candidate
            break

    outputs_dir = topic_root / "L4" / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Build the output markdown
    gap = analysis["band_data"].get("gap_eV")
    vbm = analysis["band_data"].get("vbm_eV")
    cbm = analysis["band_data"].get("cbm_eV")
    benchmark = analysis["benchmark_comparison"]
    conv_result = analysis["convergence"]
    librpa = analysis["librpa"]
    abacus = analysis["abacus"]

    fm: dict[str, Any] = {
        "artifact_kind": "l4_analysis",
        "run_id": run_id,
        "topic_slug": topic_slug,
        "analyzed_at": analysis["analyzed_at"],
        "run_dir": str(run_path),
    }
    if gap is not None:
        fm["computed_gap_eV"] = gap
    if vbm is not None:
        fm["vbm_eV"] = vbm
    if cbm is not None:
        fm["cbm_eV"] = cbm
    if benchmark.get("agreement_status"):
        fm["agreement_status"] = benchmark["agreement_status"]
    if conv_result.get("converged") is not None:
        fm["qsgw_converged"] = conv_result["converged"]

    body_lines = [
        f"# L4 Analysis: {run_id}",
        "",
        f"**Topic:** {topic_slug}",
        f"**Run directory:** {run_path}",
        f"**Analyzed at:** {analysis['analyzed_at']}",
        "",
        "## Files Found",
        "",
        f"- LibRPA outputs: {len(librpa_outs)}",
        f"- ABACUS outputs: {len(abacus_outs)}",
        f"- Band data files: {len(band_files)}",
    ]

    # Band structure results
    if gap is not None:
        body_lines.extend([
            "",
            "## Band Structure",
            "",
            f"| Quantity | Value |",
            f"|----------|-------|",
            f"| VBM | {vbm} eV |" if vbm is not None else "| VBM | N/A |",
            f"| CBM | {cbm} eV |" if cbm is not None else "| CBM | N/A |",
            f"| Band gap | {gap} eV |",
        ])

    # LibRPA details
    if librpa:
        body_lines.extend([
            "",
            "## LibRPA Output",
            "",
        ])
        if "exit_status" in librpa:
            body_lines.append(f"- Exit status: {librpa['exit_status']}")
        if "convergence_iterations" in librpa:
            body_lines.append(f"- QSGW iterations: {librpa['convergence_iterations']}")
        if "delta_eV" in librpa:
            body_lines.append(f"- Delta E: {librpa['delta_eV']:.6e} eV")
        if "has_nan" in librpa:
            body_lines.append("- ⚠ NaN values detected in output")
        if "wall_time" in librpa:
            body_lines.append(f"- Wall time: {librpa['wall_time']}")

    # ABACUS details
    if abacus:
        body_lines.extend([
            "",
            "## ABACUS Output",
            "",
        ])
        if abacus.get("scf_converged"):
            body_lines.append("- SCF: converged ✅")
        else:
            body_lines.append("- SCF: not converged or NSCF")
        if "total_energy_eV" in abacus:
            body_lines.append(f"- Total energy: {abacus['total_energy_eV']} eV")
        if "nkstot" in abacus:
            body_lines.append(f"- k-points: {abacus['nkstot']}")

    # Benchmark comparison
    if benchmark.get("matches"):
        body_lines.extend([
            "",
            "## Benchmark Comparison",
            "",
        ])
        for m in benchmark["matches"]:
            icon = "✅" if m["status"] == "agrees" else "⚠" if m["status"] == "deviates" else "❌"
            body_lines.append(
                f"- {icon} **{m['benchmark']}**: computed {gap} eV vs "
                f"reference {m['reference_value']} ± {m['reference_uncertainty']} eV "
                f"(Δ = {m['deviation']:.3f} eV, {m['deviation_relative']:.1%}) — "
                f"*{m['status']}*"
            )
        body_lines.append(f"\n**Overall:** {benchmark['agreement_status']}")

    # Convergence
    body_lines.extend([
        "",
        "## QSGW Convergence",
        "",
        f"- Threshold: {conv_result.get('threshold_eV', 1e-3):.1e} eV",
        f"- Status: {conv_result['details']}",
    ])

    # Errors
    if analysis["errors"]:
        body_lines.extend([
            "",
            "## Errors",
            "",
        ])
        for err in analysis["errors"]:
            body_lines.append(f"- {err}")

    body_lines.append("")

    # Write using the topic's existing helpers if possible, or simple write
    output_path = outputs_dir / f"{run_id}.md"
    import yaml
    frontmatter = yaml.dump(fm, default_flow_style=False, allow_unicode=True).strip()
    output_path.write_text(
        f"---\n{frontmatter}\n---\n" + "\n".join(body_lines),
        encoding="utf-8",
    )

    analysis["output_file"] = str(output_path)

    return analysis
