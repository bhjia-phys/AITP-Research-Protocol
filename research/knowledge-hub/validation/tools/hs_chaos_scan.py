#!/usr/bin/env python3
"""Small-system chaos diagnostics for HS-style Heisenberg and public TFIM/Ising baselines."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.linalg import eigh, expm
from scipy import sparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to a JSON config file.")
    return parser


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def chord_distance(length: int, i: int, j: int) -> float:
    separation = abs(i - j)
    return (length / math.pi) * abs(math.sin(math.pi * separation / length))


def build_basis(length: int, magnetization_sector: int | None) -> list[int]:
    if magnetization_sector is None:
        return list(range(1 << length))
    return [state for state in range(1 << length) if state.bit_count() == magnetization_sector]


def translate_state(state: int, length: int, shift: int) -> int:
    shift %= length
    if shift == 0:
        return state
    mask = (1 << length) - 1
    return ((state << shift) & mask) | (state >> (length - shift))


def reflect_state(state: int, length: int) -> int:
    reflected = 0
    for site in range(length):
        bit = (state >> site) & 1
        reflected |= bit << (length - 1 - site)
    return reflected


def build_heisenberg_hamiltonian(
    length: int,
    alpha: float,
    coupling: float,
    basis: list[int],
    periodic: bool,
) -> np.ndarray:
    dim = len(basis)
    index = {state: idx for idx, state in enumerate(basis)}
    hamiltonian = np.zeros((dim, dim), dtype=np.complex128)

    for row, state in enumerate(basis):
        for i in range(length):
            for j in range(i + 1, length):
                distance = chord_distance(length, i, j) if periodic else abs(i - j)
                interaction = coupling if alpha == 0 else coupling / (distance**alpha)
                bit_i = (state >> i) & 1
                bit_j = (state >> j) & 1
                hamiltonian[row, row] += interaction * (0.25 if bit_i == bit_j else -0.25)
                if bit_i != bit_j:
                    flipped = state ^ ((1 << i) | (1 << j))
                    col = index[flipped]
                    hamiltonian[row, col] += 0.5 * interaction
    return hamiltonian


def build_heisenberg_hamiltonian_sparse(
    length: int,
    alpha: float,
    coupling: float,
    basis: list[int],
    periodic: bool,
) -> sparse.csr_matrix:
    dim = len(basis)
    index = {state: idx for idx, state in enumerate(basis)}
    diagonal = np.zeros(dim, dtype=np.float64)
    rows: list[int] = []
    cols: list[int] = []
    data: list[complex] = []

    for row, state in enumerate(basis):
        for i in range(length):
            for j in range(i + 1, length):
                distance = chord_distance(length, i, j) if periodic else abs(i - j)
                interaction = coupling if alpha == 0 else coupling / (distance**alpha)
                bit_i = (state >> i) & 1
                bit_j = (state >> j) & 1
                diagonal[row] += interaction * (0.25 if bit_i == bit_j else -0.25)
                if bit_i != bit_j:
                    flipped = state ^ ((1 << i) | (1 << j))
                    col = index[flipped]
                    rows.append(row)
                    cols.append(col)
                    data.append(0.5 * interaction)

    rows.extend(range(dim))
    cols.extend(range(dim))
    data.extend(diagonal.tolist())
    return sparse.csr_matrix((data, (rows, cols)), shape=(dim, dim), dtype=np.complex128)


def build_tfim_hamiltonian(
    length: int,
    g_field: float,
    h_field: float,
    basis: list[int],
    periodic: bool,
) -> np.ndarray:
    dim = len(basis)
    index = {state: idx for idx, state in enumerate(basis)}
    hamiltonian = np.zeros((dim, dim), dtype=np.complex128)

    bond_sites = range(length) if periodic else range(length - 1)
    for row, state in enumerate(basis):
        for site in bond_sites:
            neighbor = (site + 1) % length
            bit_i = (state >> site) & 1
            bit_j = (state >> neighbor) & 1
            sigma_i = 1.0 if bit_i else -1.0
            sigma_j = 1.0 if bit_j else -1.0
            hamiltonian[row, row] += -sigma_i * sigma_j

        for site in range(length):
            bit = (state >> site) & 1
            sigma_z = 1.0 if bit else -1.0
            hamiltonian[row, row] += -h_field * sigma_z
            flipped = state ^ (1 << site)
            col = index.get(flipped)
            if col is not None:
                hamiltonian[row, col] += -g_field

    return hamiltonian


def build_tfim_hamiltonian_sparse(
    length: int,
    g_field: float,
    h_field: float,
    basis: list[int],
    periodic: bool,
) -> sparse.csr_matrix:
    dim = len(basis)
    index = {state: idx for idx, state in enumerate(basis)}
    diagonal = np.zeros(dim, dtype=np.float64)
    rows: list[int] = []
    cols: list[int] = []
    data: list[complex] = []

    bond_sites = range(length) if periodic else range(length - 1)
    for row, state in enumerate(basis):
        for site in bond_sites:
            neighbor = (site + 1) % length
            bit_i = (state >> site) & 1
            bit_j = (state >> neighbor) & 1
            sigma_i = 1.0 if bit_i else -1.0
            sigma_j = 1.0 if bit_j else -1.0
            diagonal[row] += -sigma_i * sigma_j

        for site in range(length):
            bit = (state >> site) & 1
            sigma_z = 1.0 if bit else -1.0
            diagonal[row] += -h_field * sigma_z
            flipped = state ^ (1 << site)
            col = index.get(flipped)
            if col is not None:
                rows.append(row)
                cols.append(col)
                data.append(-g_field)

    rows.extend(range(dim))
    cols.extend(range(dim))
    data.extend(diagonal.tolist())
    return sparse.csr_matrix((data, (rows, cols)), shape=(dim, dim), dtype=np.complex128)


def build_local_sz(length: int, site: int, basis: list[int]) -> np.ndarray:
    dim = len(basis)
    operator = np.zeros((dim, dim), dtype=np.complex128)
    for idx, state in enumerate(basis):
        bit = (state >> site) & 1
        operator[idx, idx] = 0.5 if bit else -0.5
    return operator


def build_local_sz_sparse(length: int, site: int, basis: list[int]) -> sparse.csr_matrix:
    diagonal = np.array([0.5 if (state >> site) & 1 else -0.5 for state in basis], dtype=np.float64)
    return sparse.diags(diagonal, offsets=0, dtype=np.complex128, format="csr")


def build_local_sigma_z(length: int, site: int, basis: list[int]) -> np.ndarray:
    dim = len(basis)
    operator = np.zeros((dim, dim), dtype=np.complex128)
    for idx, state in enumerate(basis):
        bit = (state >> site) & 1
        operator[idx, idx] = 1.0 if bit else -1.0
    return operator


def build_local_sigma_z_sparse(length: int, site: int, basis: list[int]) -> sparse.csr_matrix:
    diagonal = np.array([1.0 if (state >> site) & 1 else -1.0 for state in basis], dtype=np.float64)
    return sparse.diags(diagonal, offsets=0, dtype=np.complex128, format="csr")


def build_local_sigma_x(length: int, site: int, basis: list[int]) -> np.ndarray:
    dim = len(basis)
    index = {state: idx for idx, state in enumerate(basis)}
    operator = np.zeros((dim, dim), dtype=np.complex128)
    for row, state in enumerate(basis):
        flipped = state ^ (1 << site)
        col = index.get(flipped)
        if col is not None:
            operator[row, col] = 1.0
    return operator


def build_local_sigma_x_sparse(length: int, site: int, basis: list[int]) -> sparse.csr_matrix:
    index = {state: idx for idx, state in enumerate(basis)}
    rows: list[int] = []
    cols: list[int] = []
    data: list[complex] = []
    for row, state in enumerate(basis):
        flipped = state ^ (1 << site)
        col = index.get(flipped)
        if col is not None:
            rows.append(row)
            cols.append(col)
            data.append(1.0)
    dim = len(basis)
    return sparse.csr_matrix((data, (rows, cols)), shape=(dim, dim), dtype=np.complex128)


def build_bond_zz(length: int, site: int, basis: list[int]) -> np.ndarray:
    dim = len(basis)
    operator = np.zeros((dim, dim), dtype=np.complex128)
    neighbor = (site + 1) % length
    for idx, state in enumerate(basis):
        bit_i = (state >> site) & 1
        bit_j = (state >> neighbor) & 1
        sz_i = 0.5 if bit_i else -0.5
        sz_j = 0.5 if bit_j else -0.5
        operator[idx, idx] = sz_i * sz_j
    return operator


def build_bond_zz_sparse(length: int, site: int, basis: list[int]) -> sparse.csr_matrix:
    neighbor = (site + 1) % length
    diagonal = np.zeros(len(basis), dtype=np.float64)
    for idx, state in enumerate(basis):
        bit_i = (state >> site) & 1
        bit_j = (state >> neighbor) & 1
        sz_i = 0.5 if bit_i else -0.5
        sz_j = 0.5 if bit_j else -0.5
        diagonal[idx] = sz_i * sz_j
    return sparse.diags(diagonal, offsets=0, dtype=np.complex128, format="csr")


def build_bond_heisenberg(length: int, site: int, basis: list[int]) -> np.ndarray:
    dim = len(basis)
    index = {state: idx for idx, state in enumerate(basis)}
    operator = np.zeros((dim, dim), dtype=np.complex128)
    neighbor = (site + 1) % length
    for row, state in enumerate(basis):
        bit_i = (state >> site) & 1
        bit_j = (state >> neighbor) & 1
        operator[row, row] += 0.25 if bit_i == bit_j else -0.25
        if bit_i != bit_j:
            flipped = state ^ ((1 << site) | (1 << neighbor))
            col = index[flipped]
            operator[row, col] += 0.5
    return operator


def build_bond_heisenberg_sparse(length: int, site: int, basis: list[int]) -> sparse.csr_matrix:
    dim = len(basis)
    index = {state: idx for idx, state in enumerate(basis)}
    diagonal = np.zeros(dim, dtype=np.float64)
    rows: list[int] = []
    cols: list[int] = []
    data: list[complex] = []
    neighbor = (site + 1) % length

    for row, state in enumerate(basis):
        bit_i = (state >> site) & 1
        bit_j = (state >> neighbor) & 1
        diagonal[row] += 0.25 if bit_i == bit_j else -0.25
        if bit_i != bit_j:
            flipped = state ^ ((1 << site) | (1 << neighbor))
            col = index[flipped]
            rows.append(row)
            cols.append(col)
            data.append(0.5)

    rows.extend(range(dim))
    cols.extend(range(dim))
    data.extend(diagonal.tolist())
    return sparse.csr_matrix((data, (rows, cols)), shape=(dim, dim), dtype=np.complex128)


def build_parity_operator(length: int, basis: list[int]) -> np.ndarray:
    dim = len(basis)
    index = {state: idx for idx, state in enumerate(basis)}
    operator = np.zeros((dim, dim), dtype=np.complex128)
    for col, state in enumerate(basis):
        row = index[reflect_state(state, length)]
        operator[row, col] = 1.0
    return operator


def build_parity_operator_sparse(length: int, basis: list[int]) -> sparse.csr_matrix:
    index = {state: idx for idx, state in enumerate(basis)}
    rows: list[int] = []
    cols: list[int] = []
    data: list[complex] = []
    for col, state in enumerate(basis):
        rows.append(index[reflect_state(state, length)])
        cols.append(col)
        data.append(1.0)
    dim = len(basis)
    return sparse.csr_matrix((data, (rows, cols)), shape=(dim, dim), dtype=np.complex128)


def build_total_spin_squared(length: int, basis: list[int]) -> np.ndarray:
    pair_sum = build_heisenberg_hamiltonian(
        length=length,
        alpha=0.0,
        coupling=1.0,
        basis=basis,
        periodic=True,
    )
    identity = np.eye(len(basis), dtype=np.complex128)
    return 0.75 * length * identity + 2.0 * pair_sum


def build_total_spin_squared_sparse(length: int, basis: list[int]) -> sparse.csr_matrix:
    pair_sum = build_heisenberg_hamiltonian_sparse(
        length=length,
        alpha=0.0,
        coupling=1.0,
        basis=basis,
        periodic=True,
    )
    identity = sparse.eye(len(basis), dtype=np.complex128, format="csr")
    return 0.75 * length * identity + 2.0 * pair_sum


def build_requested_operator(
    length: int,
    basis: list[int],
    operator_kind: str,
    site: int,
    matrix_backend: str = "dense",
) -> np.ndarray:
    if matrix_backend == "sparse":
        if operator_kind == "sz":
            return build_local_sz_sparse(length, site, basis)
        if operator_kind == "sigma_z":
            return build_local_sigma_z_sparse(length, site, basis)
        if operator_kind == "sigma_x":
            return build_local_sigma_x_sparse(length, site, basis)
        if operator_kind == "bond_zz":
            return build_bond_zz_sparse(length, site, basis)
        if operator_kind == "bond_heisenberg":
            return build_bond_heisenberg_sparse(length, site, basis)
        raise ValueError(f"Unsupported operator kind: {operator_kind}")

    if operator_kind == "sz":
        return build_local_sz(length, site, basis)
    if operator_kind == "sigma_z":
        return build_local_sigma_z(length, site, basis)
    if operator_kind == "sigma_x":
        return build_local_sigma_x(length, site, basis)
    if operator_kind == "bond_zz":
        return build_bond_zz(length, site, basis)
    if operator_kind == "bond_heisenberg":
        return build_bond_heisenberg(length, site, basis)
    raise ValueError(f"Unsupported operator kind: {operator_kind}")


def build_model_cases(model: dict) -> list[dict]:
    family = model["family"]
    if family == "power_law_heisenberg_pbc":
        return [
            {
                "label": f"alpha_{float(alpha):.2f}",
                "family": family,
                "alpha": float(alpha),
            }
            for alpha in model["alphas"]
        ]
    if family == "tfim":
        if "cases" in model:
            cases = []
            for raw_case in model["cases"]:
                g_field = float(raw_case["g"])
                h_field = float(raw_case.get("h", 0.0))
                cases.append(
                    {
                        "label": raw_case.get("label", f"g_{g_field:.2f}_h_{h_field:.2f}"),
                        "family": family,
                        "g": g_field,
                        "h": h_field,
                    }
                )
            return cases

        g_field = float(model["g"])
        h_field = float(model.get("h", 0.0))
        return [
            {
                "label": model.get("label", f"g_{g_field:.2f}_h_{h_field:.2f}"),
                "family": family,
                "g": g_field,
                "h": h_field,
            }
        ]
    raise ValueError(f"Unsupported model family: {family}")


def build_hamiltonian_for_case(
    model: dict,
    case: dict,
    basis: list[int],
    matrix_backend: str = "dense",
) -> np.ndarray:
    family = case["family"]
    length = int(model["length"])
    periodic = bool(model.get("periodic", True))
    if family == "power_law_heisenberg_pbc":
        if matrix_backend == "sparse":
            return build_heisenberg_hamiltonian_sparse(
                length=length,
                alpha=float(case["alpha"]),
                coupling=float(model.get("coupling", 1.0)),
                basis=basis,
                periodic=periodic,
            )
        return build_heisenberg_hamiltonian(
            length=length,
            alpha=float(case["alpha"]),
            coupling=float(model.get("coupling", 1.0)),
            basis=basis,
            periodic=periodic,
        )
    if family == "tfim":
        if matrix_backend == "sparse":
            return build_tfim_hamiltonian_sparse(
                length=length,
                g_field=float(case["g"]),
                h_field=float(case.get("h", 0.0)),
                basis=basis,
                periodic=periodic,
            )
        return build_tfim_hamiltonian(
            length=length,
            g_field=float(case["g"]),
            h_field=float(case.get("h", 0.0)),
            basis=basis,
            periodic=periodic,
        )
    raise ValueError(f"Unsupported model family: {family}")


def build_translation_basis(length: int, basis: list[int], momentum_sector: int) -> np.ndarray:
    dim = len(basis)
    index = {state: idx for idx, state in enumerate(basis)}
    visited: set[int] = set()
    columns: list[np.ndarray] = []
    phase_unit = np.exp(-2j * np.pi * momentum_sector / length)

    for state in basis:
        if state in visited:
            continue
        orbit: list[int] = []
        current = state
        while current not in orbit:
            orbit.append(current)
            current = translate_state(current, length, 1)
        visited.update(orbit)

        period = len(orbit)
        if not np.isclose(phase_unit**period, 1.0, atol=1e-10):
            continue

        vector = np.zeros(dim, dtype=np.complex128)
        norm = math.sqrt(period)
        for shift, orbit_state in enumerate(orbit):
            vector[index[orbit_state]] = np.exp(-2j * np.pi * momentum_sector * shift / length) / norm
        columns.append(vector)

    if not columns:
        raise ValueError(f"No states survive translation sector k={momentum_sector}.")
    return np.column_stack(columns)


def build_parity_basis(
    parity_operator: np.ndarray,
    parity_sector: int,
    tol: float,
) -> np.ndarray:
    if sparse.issparse(parity_operator):
        parity_operator = parity_operator.toarray()
    eigenvalues, eigenvectors = eigh(parity_operator)
    mask = np.abs(eigenvalues - parity_sector) <= tol
    if not np.any(mask):
        raise ValueError(f"No states survive parity sector {parity_sector:+d}.")
    return eigenvectors[:, mask]


def build_total_spin_basis(
    total_spin_operator: np.ndarray,
    total_spin_sector: float,
    tol: float,
) -> np.ndarray:
    if sparse.issparse(total_spin_operator):
        total_spin_operator = total_spin_operator.toarray()
    eigenvalues, eigenvectors = eigh(total_spin_operator)
    target = total_spin_sector * (total_spin_sector + 1.0)
    mask = np.abs(eigenvalues - target) <= tol
    if not np.any(mask):
        raise ValueError(f"No states survive total-spin sector S={total_spin_sector:g}.")
    return eigenvectors[:, mask]


def project_matrix(matrix: np.ndarray, transform: np.ndarray) -> np.ndarray:
    return transform.conj().T @ matrix @ transform


def apply_symmetry_projection(
    length: int,
    basis: list[int],
    hamiltonian: np.ndarray,
    operators: dict[str, np.ndarray],
    translation_sector: int | None,
    parity_sector: int | None,
    total_spin_sector: float | None,
    matrix_backend: str,
    tol: float,
) -> tuple[np.ndarray, dict[str, np.ndarray], dict]:
    sector_label_parts = []
    limitations = []
    current_hamiltonian = hamiltonian
    current_operators = dict(operators)
    translation_basis: np.ndarray | None = None
    parity_basis: np.ndarray | None = None

    if translation_sector is not None:
        if translation_sector < 0 or translation_sector >= length:
            raise ValueError(f"translation_sector must lie between 0 and {length - 1}.")
        translation_basis = build_translation_basis(length, basis, translation_sector)
        current_hamiltonian = project_matrix(current_hamiltonian, translation_basis)
        current_operators = {
            name: project_matrix(operator, translation_basis)
            for name, operator in current_operators.items()
        }
        sector_label_parts.append(f"k={translation_sector}")
    else:
        limitations.append("translation sectors not resolved")

    if parity_sector is not None:
        if parity_sector not in (-1, 1):
            raise ValueError("parity_sector must be either -1 or +1.")
        if translation_sector is not None:
            compatible_pi = length % 2 == 0 and translation_sector == length // 2
            if translation_sector not in (0,) and not compatible_pi:
                raise ValueError(
                    "Parity can be combined with translation only for k=0 or k=pi sectors."
                )
        parity_operator = (
            build_parity_operator_sparse(length, basis)
            if matrix_backend == "sparse"
            else build_parity_operator(length, basis)
        )
        if translation_basis is not None:
            parity_operator = project_matrix(parity_operator, translation_basis)
        parity_basis = build_parity_basis(parity_operator, parity_sector, tol=tol)
        current_hamiltonian = project_matrix(current_hamiltonian, parity_basis)
        current_operators = {
            name: project_matrix(operator, parity_basis)
            for name, operator in current_operators.items()
        }
        sector_label_parts.append(f"parity={parity_sector:+d}")
    else:
        limitations.append("parity sectors not resolved")

    if total_spin_sector is not None:
        total_spin_operator = (
            build_total_spin_squared_sparse(length, basis)
            if matrix_backend == "sparse"
            else build_total_spin_squared(length, basis)
        )
        if translation_basis is not None:
            total_spin_operator = project_matrix(total_spin_operator, translation_basis)
        if parity_basis is not None:
            total_spin_operator = project_matrix(total_spin_operator, parity_basis)
        total_spin_basis = build_total_spin_basis(
            total_spin_operator,
            total_spin_sector=total_spin_sector,
            tol=tol,
        )
        current_hamiltonian = project_matrix(current_hamiltonian, total_spin_basis)
        current_operators = {
            name: project_matrix(operator, total_spin_basis)
            for name, operator in current_operators.items()
        }
        sector_label_parts.append(f"S={total_spin_sector:g}")
    else:
        limitations.append("full SU(2) multiplet structure not resolved")

    limitations.append("small-system exact diagonalization pilot")
    symmetry_label = ", ".join(sector_label_parts) if sector_label_parts else "fixed Sz only"

    return (
        current_hamiltonian,
        current_operators,
        {
            "symmetry_label": symmetry_label,
            "translation_sector": translation_sector,
            "parity_sector": parity_sector,
            "total_spin_sector": total_spin_sector,
            "sector_dimension": int(current_hamiltonian.shape[0]),
            "limitations": limitations,
        },
    )


def compute_gap_ratio(eigenvalues: np.ndarray, middle_fraction: float) -> float:
    values = np.sort(np.real(eigenvalues))
    trim = max(int(len(values) * (1.0 - middle_fraction) / 2.0), 0)
    if trim > 0:
        values = values[trim:-trim]
    gaps = np.diff(values)
    if len(gaps) < 2:
        return float("nan")
    ratios = np.minimum(gaps[1:], gaps[:-1]) / np.maximum(gaps[1:], gaps[:-1])
    return float(np.mean(ratios))


def compute_otoc_curve(
    hamiltonian: np.ndarray,
    op_w: np.ndarray,
    op_v: np.ndarray,
    times: np.ndarray,
) -> np.ndarray:
    eigenvalues, eigenvectors = eigh(hamiltonian)
    op_w_eig = eigenvectors.conj().T @ op_w @ eigenvectors
    op_v_eig = eigenvectors.conj().T @ op_v @ eigenvectors
    energy_differences = eigenvalues[:, None] - eigenvalues[None, :]
    dim = hamiltonian.shape[0]
    values = []
    for time in times:
        phase = np.exp(1j * energy_differences * time)
        op_w_t = phase * op_w_eig
        commutator = op_w_t @ op_v_eig - op_v_eig @ op_w_t
        value = np.trace(commutator.conj().T @ commutator).real / dim
        values.append(float(value))
    return np.asarray(values, dtype=float)


def hs_inner_product(left: np.ndarray, right: np.ndarray) -> complex:
    dim = left.shape[0]
    return np.trace(left.conj().T @ right) / dim


def liouvillian_action(hamiltonian: np.ndarray, operator: np.ndarray) -> np.ndarray:
    return 1j * (hamiltonian @ operator - operator @ hamiltonian)


def orthonormalize_operator_family(
    operators: list[tuple[str, np.ndarray]],
    tol: float,
) -> list[dict]:
    orthonormal_family: list[dict] = []
    for name, operator in operators:
        candidate = np.array(operator, dtype=np.complex128, copy=True)
        for previous in orthonormal_family:
            candidate = candidate - hs_inner_product(previous["operator"], candidate) * previous["operator"]
        norm_sq = max(hs_inner_product(candidate, candidate).real, 0.0)
        if norm_sq <= tol:
            continue
        norm = math.sqrt(norm_sq)
        orthonormal_family.append({"name": name, "operator": candidate / norm})
    return orthonormal_family


def clean_operator_against_conserved_subspace(
    operator: np.ndarray,
    reference_operators: list[tuple[str, np.ndarray]],
    tol: float,
) -> tuple[np.ndarray, dict]:
    raw_norm_sq = max(hs_inner_product(operator, operator).real, 0.0)
    raw_norm = math.sqrt(raw_norm_sq)
    if raw_norm <= tol:
        raise ValueError("Seed operator has vanishing norm before cleanup.")

    orthonormal_family = orthonormalize_operator_family(reference_operators, tol=tol)
    cleaned_operator = np.array(operator, dtype=np.complex128, copy=True)
    component_rows: list[dict] = []
    removed_weight = 0.0

    for component in orthonormal_family:
        coefficient = hs_inner_product(component["operator"], cleaned_operator)
        component_weight = float(abs(coefficient) ** 2 / raw_norm_sq)
        cleaned_operator = cleaned_operator - coefficient * component["operator"]
        component_rows.append(
            {
                "name": component["name"],
                "coefficient_real": float(coefficient.real),
                "coefficient_imag": float(coefficient.imag),
                "removed_weight": component_weight,
            }
        )
        removed_weight += component_weight

    cleaned_norm_sq = max(hs_inner_product(cleaned_operator, cleaned_operator).real, 0.0)
    cleaned_norm = math.sqrt(cleaned_norm_sq)
    return cleaned_operator, {
        "requested_components": [name for name, _ in reference_operators],
        "effective_components": [component["name"] for component in orthonormal_family],
        "raw_norm": raw_norm,
        "cleaned_norm": cleaned_norm,
        "cleaned_fraction": float(cleaned_norm_sq / raw_norm_sq),
        "removed_weight": float(removed_weight),
        "components": component_rows,
    }


def lanczos_operator_chain(
    hamiltonian: np.ndarray,
    operator: np.ndarray,
    max_steps: int,
    tol: float,
) -> tuple[list[float], list[float]]:
    norm = math.sqrt(max(hs_inner_product(operator, operator).real, 0.0))
    if norm <= tol:
        raise ValueError("Seed operator has vanishing norm.")

    basis = [operator / norm]
    alphas: list[float] = []
    betas: list[float] = []

    for step in range(max_steps):
        vector = liouvillian_action(hamiltonian, basis[-1])
        if step > 0:
            vector = vector - betas[-1] * basis[-2]
        alpha = float(hs_inner_product(basis[-1], vector).real)
        vector = vector - alpha * basis[-1]

        for prior in basis[:-1]:
            vector = vector - hs_inner_product(prior, vector) * prior

        beta_sq = max(hs_inner_product(vector, vector).real, 0.0)
        beta = math.sqrt(beta_sq)
        alphas.append(alpha)
        if beta <= tol:
            break
        betas.append(float(beta))
        basis.append(vector / beta)
    return alphas, betas


def compute_krylov_complexity(
    hamiltonian: np.ndarray,
    operator: np.ndarray,
    times: np.ndarray,
    max_steps: int,
    tol: float,
) -> tuple[np.ndarray, list[float], list[float]]:
    alphas, betas = lanczos_operator_chain(hamiltonian, operator, max_steps=max_steps, tol=tol)
    dimension = len(alphas)
    tridiagonal = np.zeros((dimension, dimension), dtype=np.complex128)
    for idx, alpha in enumerate(alphas):
        tridiagonal[idx, idx] = alpha
    for idx, beta in enumerate(betas[: max(dimension - 1, 0)]):
        tridiagonal[idx, idx + 1] = beta
        tridiagonal[idx + 1, idx] = beta

    seed = np.zeros(dimension, dtype=np.complex128)
    seed[0] = 1.0
    values = []
    indices = np.arange(dimension, dtype=float)
    for time in times:
        amplitudes = expm(-1j * tridiagonal * time) @ seed
        probabilities = np.abs(amplitudes) ** 2
        values.append(float(np.sum(indices * probabilities)))
    return np.asarray(values, dtype=float), alphas, betas


def write_curve_csv(path: Path, times: np.ndarray, series: dict[str, np.ndarray]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time", *series.keys()])
        for idx, time in enumerate(times):
            writer.writerow([f"{time:.8f}", *[f"{series[key][idx]:.12f}" for key in series]])


def write_metrics_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> int:
    args = build_parser().parse_args()
    config_path = Path(args.config).resolve()
    config = load_config(config_path)

    model = config["model"]
    observables = config["observables"]
    time_grid = config["time_grid"]
    numerics = config["numerics"]
    outputs = config["outputs"]

    results_dir = Path(outputs["results_dir"])
    results_dir.mkdir(parents=True, exist_ok=True)

    length = int(model["length"])
    family = model["family"]
    periodic = bool(model.get("periodic", True))
    magnetization_sector = model.get("magnetization_sector")
    translation_sector = model.get("translation_sector")
    parity_sector = model.get("parity_sector")
    total_spin_sector = model.get("total_spin_sector")
    matrix_backend = str(model.get("matrix_backend", "dense"))
    model_cases = build_model_cases(model)
    basis = build_basis(length, magnetization_sector)

    otoc_site_i, otoc_site_j = observables["otoc_sites"]
    krylov_site = int(observables["krylov_site"])
    otoc_operator = observables.get("otoc_operator", "sz")
    krylov_operator = observables.get("krylov_operator", "sz")

    times = np.linspace(
        float(time_grid["t_min"]),
        float(time_grid["t_max"]),
        int(time_grid["num_points"]),
        dtype=float,
    )
    middle_fraction = float(numerics.get("middle_fraction", 0.5))
    lanczos_steps = int(numerics.get("lanczos_steps", 20))
    lanczos_tol = float(numerics.get("lanczos_tol", 1e-10))
    symmetry_tol = float(numerics.get("symmetry_tol", 1e-8))
    krylov_cleanup = numerics.get("krylov_cleanup", {})
    subtract_identity = bool(krylov_cleanup.get("subtract_identity", False))
    subtract_hamiltonian = bool(krylov_cleanup.get("subtract_hamiltonian", False))
    report_raw_krylov = bool(krylov_cleanup.get("report_raw", False))
    krylov_cleanup_requested = subtract_identity or subtract_hamiltonian

    otoc_series: dict[str, np.ndarray] = {}
    krylov_series: dict[str, np.ndarray] = {}
    raw_krylov_series: dict[str, np.ndarray] = {}
    metrics_rows: list[dict] = []
    last_sector_info: dict | None = None

    for case in model_cases:
        label = case["label"]
        full_hamiltonian = build_hamiltonian_for_case(
            model=model,
            case=case,
            basis=basis,
            matrix_backend=matrix_backend,
        )
        operators = {
            "otoc_w": build_requested_operator(
                length, basis, otoc_operator, int(otoc_site_i), matrix_backend=matrix_backend
            ),
            "otoc_v": build_requested_operator(
                length, basis, otoc_operator, int(otoc_site_j), matrix_backend=matrix_backend
            ),
            "krylov": build_requested_operator(
                length, basis, krylov_operator, krylov_site, matrix_backend=matrix_backend
            ),
        }
        hamiltonian, projected_operators, sector_info = apply_symmetry_projection(
            length=length,
            basis=basis,
            hamiltonian=full_hamiltonian,
            operators=operators,
            translation_sector=translation_sector,
            parity_sector=parity_sector,
            total_spin_sector=total_spin_sector,
            matrix_backend=matrix_backend,
            tol=symmetry_tol,
        )
        last_sector_info = sector_info

        if sparse.issparse(hamiltonian):
            hamiltonian = hamiltonian.toarray()
        projected_operators = {
            name: operator.toarray() if sparse.issparse(operator) else operator
            for name, operator in projected_operators.items()
        }

        eigenvalues, _ = eigh(hamiltonian)
        gap_ratio = compute_gap_ratio(eigenvalues, middle_fraction=middle_fraction)
        otoc = compute_otoc_curve(
            hamiltonian,
            projected_operators["otoc_w"],
            projected_operators["otoc_v"],
            times,
        )
        raw_krylov, raw_lanczos_alphas, raw_lanczos_betas = compute_krylov_complexity(
            hamiltonian,
            projected_operators["krylov"],
            times,
            max_steps=lanczos_steps,
            tol=lanczos_tol,
        )
        krylov = raw_krylov
        lanczos_alphas = raw_lanczos_alphas
        lanczos_betas = raw_lanczos_betas
        cleanup_metadata: dict | None = None
        if krylov_cleanup_requested:
            cleanup_components: list[tuple[str, np.ndarray]] = []
            if subtract_identity:
                cleanup_components.append(
                    ("identity", np.eye(hamiltonian.shape[0], dtype=np.complex128))
                )
            if subtract_hamiltonian:
                cleanup_components.append(("hamiltonian_orth_to_previous", hamiltonian))
            cleaned_operator, cleanup_metadata = clean_operator_against_conserved_subspace(
                projected_operators["krylov"],
                cleanup_components,
                tol=lanczos_tol,
            )
            krylov, lanczos_alphas, lanczos_betas = compute_krylov_complexity(
                hamiltonian,
                cleaned_operator,
                times,
                max_steps=lanczos_steps,
                tol=lanczos_tol,
            )
        otoc_series[label] = otoc
        krylov_series[label] = krylov
        if krylov_cleanup_requested and report_raw_krylov:
            raw_krylov_series[label] = raw_krylov
        metric_row = {
            "label": label,
            "family": family,
            "sector_dimension": sector_info["sector_dimension"],
            "symmetry_label": sector_info["symmetry_label"],
            "translation_sector": translation_sector,
            "parity_sector": parity_sector,
            "total_spin_sector": total_spin_sector,
            "gap_ratio": gap_ratio,
            "otoc_initial": float(otoc[0]),
            "otoc_peak": float(np.max(otoc)),
            "otoc_final": float(otoc[-1]),
            "krylov_peak": float(np.max(krylov)),
            "krylov_final": float(krylov[-1]),
            "lanczos_depth": len(lanczos_alphas),
            "lanczos_betas": [float(beta) for beta in lanczos_betas],
            "limitations": sector_info["limitations"],
        }
        if krylov_cleanup_requested:
            metric_row["krylov_raw_peak"] = float(np.max(raw_krylov))
            metric_row["krylov_raw_final"] = float(raw_krylov[-1])
            metric_row["krylov_raw_lanczos_depth"] = len(raw_lanczos_alphas)
            metric_row["krylov_cleanup"] = cleanup_metadata
        if "alpha" in case:
            metric_row["alpha"] = float(case["alpha"])
        if "g" in case:
            metric_row["g"] = float(case["g"])
        if "h" in case:
            metric_row["h"] = float(case.get("h", 0.0))
        metrics_rows.append(metric_row)

    if last_sector_info is None:
        raise SystemExit("No sector information was produced.")

    write_curve_csv(results_dir / f"{outputs['prefix']}_otoc.csv", times, otoc_series)
    write_curve_csv(results_dir / f"{outputs['prefix']}_krylov.csv", times, krylov_series)
    if raw_krylov_series:
        write_curve_csv(results_dir / f"{outputs['prefix']}_krylov_raw.csv", times, raw_krylov_series)
    write_metrics_jsonl(results_dir / f"{outputs['prefix']}_metrics.jsonl", metrics_rows)

    summary = {
        "config": str(config_path),
        "family": family,
        "sector_dimension": last_sector_info["sector_dimension"],
        "symmetry_label": last_sector_info["symmetry_label"],
        "translation_sector": translation_sector,
        "parity_sector": parity_sector,
        "total_spin_sector": total_spin_sector,
        "cases": model_cases,
        "results_files": {
            "otoc_csv": str(results_dir / f"{outputs['prefix']}_otoc.csv"),
            "krylov_csv": str(results_dir / f"{outputs['prefix']}_krylov.csv"),
            "metrics_jsonl": str(results_dir / f"{outputs['prefix']}_metrics.jsonl"),
        },
    }
    if raw_krylov_series:
        summary["results_files"]["krylov_raw_csv"] = str(
            results_dir / f"{outputs['prefix']}_krylov_raw.csv"
        )
    (results_dir / f"{outputs['prefix']}_summary.json").write_text(
        json.dumps(summary, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Chaos diagnostics pilot summary",
        "",
        f"- Chain length: `{length}`",
        f"- Model family: `{family}`",
        f"- Magnetization sector: `{magnetization_sector}`",
        f"- Symmetry sector: `{last_sector_info['symmetry_label']}`",
        f"- Sector dimension: `{last_sector_info['sector_dimension']}`",
        f"- Cases: `{', '.join(case['label'] for case in model_cases)}`",
        "",
        "| case | gap ratio | OTOC peak | OTOC final | Krylov peak | Krylov final | Lanczos depth |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in metrics_rows:
        lines.append(
            f"| {row['label']} | {row['gap_ratio']:.4f} | {row['otoc_peak']:.4f} | {row['otoc_final']:.4f} | {row['krylov_peak']:.4f} | {row['krylov_final']:.4f} | {row['lanczos_depth']} |"
        )
    lines.append("")
    lines.append("## Limitations")
    for limitation in last_sector_info["limitations"]:
        lines.append(f"- {limitation}")
    if krylov_cleanup_requested:
        lines.append(f"- Krylov columns above use the cleaned seed after subtracting `{', '.join(name for name in (['identity'] if subtract_identity else []) + (['hamiltonian'] if subtract_hamiltonian else []))}`.")
        if raw_krylov_series:
            lines.append("- Raw Krylov curves before cleanup are saved in the companion `_krylov_raw.csv` artifact.")
        lines.append("")
        lines.append("## Krylov cleanup")
        lines.append("| case | raw peak | cleaned peak | removed weight | cleaned fraction |")
        lines.append("|---|---:|---:|---:|---:|")
        for row in metrics_rows:
            cleanup_row = row["krylov_cleanup"]
            lines.append(
                f"| {row['label']} | {row['krylov_raw_peak']:.4f} | {row['krylov_peak']:.4f} | {cleanup_row['removed_weight']:.4f} | {cleanup_row['cleaned_fraction']:.4f} |"
            )
    (results_dir / f"{outputs['prefix']}_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
