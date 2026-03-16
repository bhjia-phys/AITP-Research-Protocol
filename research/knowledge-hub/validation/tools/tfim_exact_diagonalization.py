#!/usr/bin/env python3
"""Run a tiny public TFIM exact-diagonalization benchmark."""

from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime
from pathlib import Path

import numpy as np


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def spin_z(state: int, site: int) -> float:
    return 1.0 if ((state >> site) & 1) == 0 else -1.0


def build_tfim_hamiltonian(*, sites: int, coupling_j: float, field_h: float, boundary: str) -> np.ndarray:
    dim = 1 << sites
    hamiltonian = np.zeros((dim, dim), dtype=float)
    bond_count = sites if boundary == "periodic" else sites - 1

    for state in range(dim):
        diagonal_term = 0.0
        for site in range(bond_count):
            neighbor = (site + 1) % sites
            diagonal_term += -coupling_j * spin_z(state, site) * spin_z(state, neighbor)
        hamiltonian[state, state] += diagonal_term

        for site in range(sites):
            flipped_state = state ^ (1 << site)
            hamiltonian[state, flipped_state] += -field_h

    return hamiltonian


def validate_config(payload: dict) -> None:
    if payload.get("model") != "transverse_field_ising_chain":
        raise ValueError("Only `transverse_field_ising_chain` is supported by this starter.")
    sites = int(payload.get("sites") or 0)
    if sites < 2 or sites > 8:
        raise ValueError("The public starter supports `sites` between 2 and 8.")
    boundary = str(payload.get("boundary") or "").strip()
    if boundary not in {"open", "periodic"}:
        raise ValueError("`boundary` must be `open` or `periodic`.")


def build_summary_markdown(payload: dict) -> str:
    parameters = payload["parameters"]
    metrics = payload["metrics"]
    lines = [
        f"# {payload['summary_title']}",
        "",
        f"- Created at: `{payload['created_at']}`",
        f"- Tool: `{payload['tool_name']}`",
        f"- Config path: `{payload['config_path']}`",
        f"- Result path: `{payload['result_path']}`",
        "",
        "## Model definition",
        "",
        f"- Model: `{payload['model']}`",
        f"- Sites: `{parameters['sites']}`",
        f"- Coupling J: `{parameters['coupling_j']}`",
        f"- Field h: `{parameters['field_h']}`",
        f"- Boundary: `{parameters['boundary']}`",
        "",
        "## Metrics",
        "",
        f"- Ground-state energy: `{metrics['ground_state_energy']}`",
        f"- Ground-state energy density: `{metrics['ground_state_energy_density']}`",
        f"- Spectral gap: `{metrics['spectral_gap']}`",
        f"- Lowest eigenvalues: `{', '.join(str(value) for value in payload['eigenvalues_lowest'])}`",
        "",
        "## Limitations",
        "",
    ]
    for item in payload["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Non-conclusions", ""])
    for item in payload["non_conclusions"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary-note")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config_path = Path(args.config).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    summary_note_path = Path(args.summary_note).expanduser().resolve() if args.summary_note else None

    config = read_json(config_path)
    validate_config(config)

    sites = int(config["sites"])
    coupling_j = float(config["coupling_j"])
    field_h = float(config["field_h"])
    boundary = str(config["boundary"])

    hamiltonian = build_tfim_hamiltonian(
        sites=sites,
        coupling_j=coupling_j,
        field_h=field_h,
        boundary=boundary,
    )
    eigenvalues = np.linalg.eigvalsh(hamiltonian)
    lowest = [round(float(value), 10) for value in eigenvalues[: min(6, len(eigenvalues))]]
    ground_state_energy = float(eigenvalues[0])
    first_excited_energy = float(eigenvalues[1])
    spectral_gap = first_excited_energy - ground_state_energy

    payload = {
        "tool_name": "tfim_exact_diagonalization",
        "status": "success",
        "created_at": now_iso(),
        "config_path": str(config_path),
        "result_path": str(output_path),
        "summary_title": str(config.get("summary_title") or "TFIM finite-size gap benchmark"),
        "model": "transverse_field_ising_chain",
        "observable": str(config.get("observable") or "spectral_gap"),
        "parameters": {
            "sites": sites,
            "coupling_j": coupling_j,
            "field_h": field_h,
            "boundary": boundary,
        },
        "metrics": {
            "ground_state_energy": round(ground_state_energy, 10),
            "ground_state_energy_density": round(ground_state_energy / sites, 10),
            "spectral_gap": round(spectral_gap, 10),
        },
        "eigenvalues_lowest": lowest,
        "limitations": [
            "This starter uses dense exact diagonalization and is only intended for very small systems.",
            "No symmetry-sector reduction or finite-size scaling is included by default.",
            "The result is a bounded toy-model benchmark, not a full-theory claim.",
        ],
        "non_conclusions": [
            "This does not establish thermodynamic-limit behavior.",
            "This does not justify transferring the observed signal directly to a different model.",
            "This does not replace a baseline or understanding gate for stronger claims.",
        ],
        "runtime": {
            "python": platform.python_version(),
            "numpy": str(np.__version__),
        },
        "notes": str(config.get("notes") or ""),
    }
    write_json(output_path, payload)
    if summary_note_path is not None:
        write_text(summary_note_path, build_summary_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
