#!/usr/bin/env python3
"""Finite algebra controls for hartree-derivation.md; no production code called."""
import numpy as np


RNG = np.random.default_rng(20261028)
RESULTS = []


def check(name, actual, expected, tol=2e-11):
    residual = float(np.max(np.abs(np.asarray(actual) - np.asarray(expected))))
    if not np.isfinite(residual) or residual > tol:
        raise AssertionError(f"{name}: residual={residual:.6e}, tolerance={tol:.2e}")
    RESULTS.append((name, residual))


def witness(name, actual, wrong, minimum=1e-5):
    gap = float(np.max(np.abs(np.asarray(actual) - np.asarray(wrong))))
    if not np.isfinite(gap) or gap < minimum:
        raise AssertionError(f"{name}: undetected error, gap={gap:.6e}")
    print(f"WITNESS {name}: gap={gap:.6e}")


def complex_random(shape):
    return RNG.normal(size=shape) + 1j * RNG.normal(size=shape)


def hermitian_random(n):
    a = complex_random((n, n))
    return (a + a.conj().T) / 2


def inverse_sqrt(a):
    vals, vecs = np.linalg.eigh(a)
    return (vecs / np.sqrt(vals)) @ vecs.conj().T


def grid_model():
    # A finite quadrature with a softened positive interaction; not a 3D material.
    x = np.linspace(-2, 2, 9)
    weights = np.full(len(x), 0.5)
    phi = np.stack((np.exp(-(x + 0.55) ** 2), np.exp(-(x - 0.7) ** 2)), axis=1)
    overlap = phi.T @ (weights[:, None] * phi)
    kernel = 1 / np.sqrt((x[:, None] - x[None, :]) ** 2 + 0.8 ** 2)
    coulomb_grid = weights[:, None] * kernel * weights[None, :]
    aux = np.stack((phi[:, 0] ** 2, phi[:, 0] * phi[:, 1], phi[:, 1] ** 2), axis=1)
    full_c = np.zeros((3, 2, 2))
    full_c[0, 0, 0] = full_c[1, 0, 1] = full_c[1, 1, 0] = full_c[2, 1, 1] = 1
    metric = aux.T @ coulomb_grid @ aux
    # AO-major spinor order (i, alpha); normalize with S tensor I_spin.
    q, _ = np.linalg.qr(complex_random((4, 4)))
    coeff = inverse_sqrt(np.kron(overlap, np.eye(2))) @ q
    spin_density = (coeff * np.array([0.95, 0.7, 0.2, 0.05])) @ coeff.conj().T
    density = np.trace(spin_density.reshape(2, 2, 2, 2), axis1=1, axis2=3)
    n_grid = np.einsum("xi,ij,xj->x", phi, density, phi)
    rho = np.einsum("pij,ji->p", full_c, density)
    potential_aux = metric @ rho
    j_fit = np.einsum("pij,p->ij", full_c, potential_aux)
    v_grid = kernel @ (weights * n_grid)
    j_grid = phi.T @ ((weights * v_grid)[:, None] * phi)
    e_grid = 0.5 * n_grid @ coulomb_grid @ n_grid
    e_fit = 0.5 * rho @ metric @ rho
    check("grid density = exact auxiliary product density", aux @ rho, n_grid)
    check("direct grid Hartree = CVC Hartree (exact product space)", j_fit, j_grid)
    check("grid energy = auxiliary energy", e_grid, e_fit)
    check("AO trace energy", 0.5 * np.trace(density @ j_fit), e_grid)
    check("electron number = Tr(S D)", weights @ n_grid, np.trace(overlap @ density))
    check("projected density recovery", np.linalg.solve(overlap, overlap @ density @ overlap)
          @ np.linalg.inv(overlap), density)
    perturb = hermitian_random(2)

    def energy(d):
        n = np.einsum("xi,ij,xj->x", phi, d, phi)
        return 0.5 * n @ coulomb_grid @ n

    step = 1e-5
    fd = (energy(density + step * perturb) - energy(density - step * perturb)) / (2 * step)
    check("grid energy derivative = Tr(J deltaD)", fd, np.trace(j_fit @ perturb), 2e-9)
    u, _ = np.linalg.qr(complex_random((2, 2)))
    spin_rotation = np.kron(np.eye(2), u)
    rotated = spin_rotation @ spin_density @ spin_rotation.conj().T
    rotated_charge = np.trace(rotated.reshape(2, 2, 2, 2), axis1=1, axis2=3)
    check("global spin rotation preserves charge source", rotated_charge, density)
    gauge = 0.37
    gauge_grid = phi.T @ ((weights * gauge)[:, None] * phi)
    check("constant potential projects to v0 S", gauge_grid, gauge * overlap)
    witness("v0 I is not v0 S", gauge_grid, gauge * np.eye(2))
    neutral = perturb - np.trace(overlap @ perturb) / np.trace(overlap @ density) * density
    check("constant potential decouples from neutral density change",
          np.trace(gauge_grid @ neutral), 0)
    delta = 0.1 * perturb
    delta_rho = np.einsum("pij,ji->p", full_c, delta)
    cross = rho @ metric @ delta_rho
    check("density-difference energy includes reference cross term",
          energy(density + delta) - energy(density), cross + energy(delta))
    witness("E[deltaD] alone omits cross term", energy(density + delta) - energy(density), energy(delta))
    # One AO and one ABF: endpoints each contain half the complete product.
    occupation, interaction = 1.4, 2.3
    j_correct = (0.5 + 0.5) * interaction * (0.5 + 0.5) * occupation
    j_doubled = (1 + 1) * interaction * (1 + 1) * occupation
    check("same-center half coefficients", j_correct, interaction * occupation)
    check("double full coefficients give fourfold potential", j_doubled, 4 * j_correct)
    witness("same-center coefficient misuse", j_correct, j_doubled)


def local_fit_projection_boundary():
    # Two restricted pair spaces in a common auxiliary space, with exact products
    # chosen inside that common space. Local normal equations do not imply b=VC.
    metric = np.array([[2.0, 0.45], [0.45, 1.3]])
    exact_products = np.array([[1.0, 0.4], [0.25, 0.9]])  # aux, pair
    b = metric @ exact_products
    local_c = np.diag(np.diag(b) / np.diag(metric))
    pair_density = np.array([0.8, 0.3])
    rho = local_c @ pair_density
    exact_output = b.T @ rho
    cvc_output = local_c.T @ metric @ rho
    check("restricted pair normal equations", np.diag(metric @ local_c), np.diag(b))
    witness("local CVC differs from exact output projection", cvc_output, exact_output)
    global_c = np.linalg.solve(metric, b)
    check("global fit restores exact output projection", global_c.T @ metric @ rho, exact_output)
    perturb = np.array([0.3, -0.2])
    step = 1e-5

    def energy(d):
        fitted = local_c @ d
        return 0.5 * fitted @ metric @ fitted

    derivative = (energy(pair_density + step * perturb) - energy(pair_density - step * perturb)) / (2 * step)
    check("local CVC retains its own energy derivative", derivative, cvc_output @ perturb, 2e-9)


def periodic_model():
    # Three cells, two atoms with one AO and one ABF each. Complete tensor sums
    # below are independent of the momentum-space factorization being tested.
    nk, nao, naux = 3, 2, 2
    momenta = 2 * np.pi * np.arange(nk) / nk
    phase = np.exp(1j * momenta[:, None] * np.arange(nk)[None, :])
    raw_c = np.zeros((nk, naux, nao, nao))
    for r in range(nk):
        for i in range(nao):
            raw_c[r, i, i, :] = RNG.normal(size=nao) * (0.4 if r else 1.0)
    raw_c[0, 0, 0, 0] = raw_c[0, 1, 1, 1] = 0.5
    v_r = np.empty((nk, naux, naux))
    v_r[0] = np.array([[4.0, 0.2], [0.2, 3.5]])
    v_r[1] = np.array([[0.1, 0.13], [-0.04, 0.15]])
    v_r[2] = v_r[1].T
    density_k = np.empty((nk, nao, nao), dtype=complex)
    for k in range(nk):
        a = complex_random((nao, nao))
        density_k[k] = a @ a.conj().T / 4
    d_r = np.einsum("kr,kij->rij", phase.conj(), density_k) / nk
    full_c = np.zeros((nk * naux, nk * nao, nk * nao))
    full_v = np.zeros((nk * naux, nk * naux))
    full_d = np.zeros((nk * nao, nk * nao), dtype=complex)
    for ta in range(nk):
        for tb in range(nk):
            r = (tb - ta) % nk
            full_d[ta * nao:(ta + 1) * nao, tb * nao:(tb + 1) * nao] = d_r[r]
            full_v[ta * naux:(ta + 1) * naux, tb * naux:(tb + 1) * naux] = v_r[r]
            for i in range(nao):
                for j in range(nao):
                    a, b = ta * nao + i, tb * nao + j
                    for mu in range(naux):
                        full_c[ta * naux + mu, a, b] += raw_c[r, mu, i, j]
                        full_c[tb * naux + mu, a, b] += raw_c[(-r) % nk, mu, j, i]
    check("finite supercell density is Hermitian", full_d, full_d.conj().T)
    if np.linalg.eigvalsh(full_v).min() <= 0:
        raise AssertionError("finite metric must be positive")
    rho_full = np.einsum("pab,ba->p", full_c, full_d)
    j_full = np.einsum("pab,pq,q->ab", full_c, full_v, rho_full)
    c_k = np.einsum("kr,rmij->kmij", phase, raw_c)
    vertex = c_k + c_k.conj().swapaxes(-1, -2)
    rho_k = np.einsum("kmij,kji->m", vertex, density_k) / nk
    reverse_density = d_r[(-np.arange(nk)) % nk].swapaxes(-1, -2)
    rho_r = np.einsum("rmij,rij->m", raw_c, d_r + reverse_density)
    check("real-space endpoint density = full supercell density",
          rho_full, np.tile(rho_r, nk))
    check("momentum density = real-space endpoint density", rho_k, rho_r)
    check("auxiliary density is real", rho_k.imag, 0)
    potential = v_r.sum(axis=0) @ rho_k
    j_k = np.einsum("kmij,m->kij", vertex, potential)
    j_r_from_full = np.stack([j_full[:nao, r * nao:(r + 1) * nao] for r in range(nk)])
    check("full supercell Hartree = reciprocal Hartree",
          np.einsum("kr,rij->kij", phase, j_r_from_full), j_k)
    energy_cell = 0.5 * rho_k @ potential
    check("supercell energy / Nk = auxiliary energy per cell",
          0.5 * np.trace(full_d @ j_full) / nk, energy_cell)
    check("momentum trace energy per cell",
          0.5 * np.einsum("kij,kji->", density_k, j_k) / nk, energy_cell)
    perturb = np.stack([hermitian_random(nao) for _ in range(nk)])

    def energy(d):
        rho = np.einsum("kmij,kji->m", vertex, d) / nk
        return 0.5 * rho @ v_r.sum(axis=0) @ rho

    step = 1e-5
    derivative = (energy(density_k + step * perturb) - energy(density_k - step * perturb)) / (2 * step)
    check("periodic energy gradient", derivative, np.einsum("kij,kji->", j_k, perturb) / nk, 2e-9)
    weighted = density_k / nk
    libri_input = nk * weighted
    m_code = np.einsum("kmij,kji->m", vertex, libri_input)
    check("adapter weighting and kernel division", v_r.sum(axis=0) @ m_code / nk, potential)
    wrong_weight = v_r.sum(axis=0) @ np.einsum("kmij,kji->m", vertex, weighted) / nk
    witness("double mesh division", potential, wrong_weight)
    wrong_vertex = c_k + c_k.swapaxes(-1, -2)
    wrong_rho = np.einsum("kmij,kji->m", wrong_vertex, density_k) / nk
    witness("missing reverse-endpoint conjugation", rho_k, wrong_rho)


def shifted_mesh_folding():
    nk, shift = 3, 0.37
    cells = np.arange(-4, 6)
    raw = RNG.normal(size=(len(cells), 2, 2, 2))
    reduced_k = 2 * np.pi * np.arange(nk) / nk
    direct = np.einsum("kr,rmij->kmij",
                       np.exp(1j * (reduced_k[:, None] + shift) * cells), raw)
    folded = np.zeros((nk, 2, 2, 2), dtype=complex)
    wrongly_folded = np.zeros_like(folded)
    for r, tensor in zip(cells, raw):
        folded[r % nk] += np.exp(1j * shift * r) * tensor
        wrongly_folded[r % nk] += tensor
    reduced_phase = np.exp(1j * reduced_k[:, None] * np.arange(nk))
    reconstructed = np.einsum("kr,rmij->kmij", reduced_phase, folded)
    check("shifted-mesh prephase and folding preserve physical vertex", reconstructed, direct)
    witness("folding a shifted mesh without prephase", direct,
            np.einsum("kr,rmij->kmij", reduced_phase, wrongly_folded))


if __name__ == "__main__":
    grid_model()
    local_fit_projection_boundary()
    periodic_model()
    shifted_mesh_folding()
    for name, residual in RESULTS:
        print(f"PASS {name}: residual={residual:.6e}")
    print(f"Passed {len(RESULTS)} finite algebra checks; no LibRI/LibRPA call or material calculation.")
