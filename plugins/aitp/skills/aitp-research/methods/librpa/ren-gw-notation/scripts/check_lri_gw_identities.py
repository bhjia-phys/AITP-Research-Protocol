#!/usr/bin/env python3
"""Finite algebra controls for the linked LRI/GW derivations; no LibRPA run.

Requires NumPy. All inputs are deterministic synthetic matrices, in atomic units.
The reference routes include spectral vertices, finite-difference density response,
and an explicitly assembled BvK supercell, rather than LibRI implementation calls.
"""
import json
import numpy as np


rng = np.random.default_rng(20261028)
results = {}


def error(name, actual, expected, tol=3e-11):
    value = float(np.max(np.abs(np.asarray(actual) - np.asarray(expected))))
    results[name] = value
    if not np.isfinite(value) or value > tol:
        raise AssertionError(f"{name}: {value} > {tol}")


def witness(name, wrong, correct, minimum=1e-6):
    value = float(np.max(np.abs(np.asarray(wrong) - np.asarray(correct))))
    results[name] = value
    if not np.isfinite(value) or value < minimum:
        raise AssertionError(f"{name}: control did not discriminate ({value})")


def unitary(n):
    return np.linalg.qr(rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n)))[0]


def gs(e, f, tau):
    return np.exp(-e * tau) * (-(1 - f) if tau > 0 else f)


# Coulomb fitting: a local normal equation is not a truncated global inverse.
x = rng.normal(size=(5, 5))
v = x @ x.T + np.eye(5)
b = rng.normal(size=5)
local_c = np.linalg.solve(v[:3, :3], b[:3])
error("local_fit_normal_equation", v[:3, :3] @ local_c, b[:3])
witness("truncated_global_fit_is_different", np.linalg.solve(v, b)[:3], local_c)

# Nonorthogonal AO kernel versus projected matrix elements.
q = unitary(4)
s = q @ np.diag([0.7, 1.1, 1.6, 2.2]) @ q.conj().T
sinvh = q @ np.diag(np.array([0.7, 1.1, 1.6, 2.2]) ** -0.5) @ q.conj().T
c = sinvh @ unitary(4)
energies = np.array([-1.1, -0.4, 0.6, 1.3])
h = s @ c @ np.diag(energies) @ c.conj().T @ s
z = 0.17 + 0.71j
g_spectral = c @ np.diag(1 / (z - energies)) @ c.conj().T
error("nonorthogonal_resolvent", np.linalg.inv(z * s - h), g_spectral)
error("nonorthogonal_completeness", c @ c.conj().T, np.linalg.inv(s))
witness("projected_G_is_not_kernel_coefficients", s @ g_spectral @ s, g_spectral)
sx = np.array([[0., 1.], [1., 0.]])
witness("projected_operator_product_needs_projector", (sx @ sx)[0,0], sx[0,0]**2)

# Two centers, three spatial AOs, four ABFs, and genuinely complex SOC states.
nao, naux, nspin = 3, 4, 2
ao_atoms = np.array([0, 0, 1])
aux_atoms = np.array([0, 0, 1, 1])
endpoint = rng.normal(size=(naux, nao, nao))
endpoint *= (aux_atoms[:, None, None] == ao_atoms[None, :, None])
full = endpoint + endpoint.transpose(0, 2, 1)
u = unitary(nao * nspin)
e = np.array([-1.4, -1.0, -0.6, 0.7, 1.1, 1.6])
f = (e < 0).astype(float)
operators = np.array([np.kron(np.eye(nspin), t) for t in full])
vertices = np.array([u.conj().T @ t @ u for t in operators])


def spin_g(tau):
    return (u @ np.diag(gs(e, f, tau)) @ u.conj().T).reshape(nspin, nao, nspin, nao)


def bubble_four(gp, gm):
    return sum([
        np.einsum("uik,vjl,sitj,tlsk->uv", endpoint, endpoint, gp, gm),
        np.einsum("uik,vjl,sitl,tjsk->uv", endpoint, endpoint, gp, gm),
        np.einsum("uik,vjl,sktl,tjsi->uv", endpoint, endpoint, gp, gm),
        np.einsum("uik,vjl,sktj,tlsi->uv", endpoint, endpoint, gp, gm),
    ])


tau = 0.83
gp, gm = spin_g(tau), spin_g(-tau)
chi_dense = np.einsum("uik,vjl,sitj,tlsk->uv", full, full, gp, gm)
chi_spectral = np.einsum("umn,vmn,n,m->uv", vertices, vertices.conj(),
                         gs(e, f, tau), gs(e, f, -tau))
error("bubble_four_vs_full_fit", bubble_four(gp, gm), chi_dense)
error("bubble_four_vs_spectral_vertices", bubble_four(gp, gm), chi_spectral)


def libri_patterns(positive, negative_input):
    # Same AO direction in both supplied two-index tensors. Spin pair (s,t)
    # is fixed within one call, then all pairs are accumulated by the consumer.
    return sum([
        np.einsum("uik,vjl,sitj,sktl->uv", endpoint, endpoint, positive, negative_input),
        np.einsum("uik,vjl,sitl,sktj->uv", endpoint, endpoint, positive, negative_input),
        np.einsum("uik,vjl,sitj,sktl->uv", endpoint, endpoint, negative_input, positive),
        np.einsum("uik,vjl,sitl,sktj->uv", endpoint, endpoint, negative_input, positive),
    ])


error("libri_same_direction_negative_input", libri_patterns(gp, gm.conj()), chi_dense)
witness("missing_negative_input_conjugation", libri_patterns(gp, gm), chi_dense)
diag_spin_only = sum(np.einsum("uik,vjl,ij,lk->uv", full, full,
                               gp[st, :, st, :], gm[st, :, st, :])
                     for st in range(nspin))
witness("dropping_offdiagonal_spin_blocks", diag_spin_only, chi_dense)

# Fourier integration of the time bubble versus the spectral denominator.
omega = 0.37
delta = e[:, None] - e[None, :]
weight = (f[:, None] - f[None, :]) / (1j * omega + delta)
chi_freq = np.einsum("umn,vmn,mn->uv", vertices, vertices.conj(), weight)
nodes, weights = np.polynomial.legendre.leggauss(280)
times = (nodes + 1) * 18
weights = weights * 18
integrated = np.zeros((naux, naux), complex)
cosine_only = np.zeros((naux, naux), complex)
for t, w in zip(times, weights):
    for sign in [1, -1]:
        vals = np.einsum("umn,vmn,n,m->uv", vertices, vertices.conj(),
                         gs(e, f, sign * t), gs(e, f, -sign * t))
        integrated += w * np.exp(1j * omega * sign * t) * vals
        if sign == 1:
            cosine_only += 2*w*np.cos(omega*t)*vals
error("time_bubble_vs_adler_wiser", integrated, chi_freq)
witness("unjustified_cosine_only_response", cosine_only, chi_freq)

# Finite differences for an abstract AO source O_nu=C_full^nu. This is not
# the literal spatial potential P_nu; that would include ABF-overlap factors.
h_soc = u @ np.diag(e) @ u.conj().T
ratio = np.divide(f[:, None] - f[None, :], delta,
                  out=np.zeros_like(delta), where=np.abs(delta) > 1e-12)
chi_static = np.einsum("umn,vmn,mn->uv", vertices, vertices.conj(), ratio)
fd = np.empty_like(chi_static)
step = 2e-5
for nu in range(naux):
    samples = []
    for sign in [1, -1]:
        values, vectors = np.linalg.eigh(h_soc + sign * step * operators[nu])
        density = vectors[:, values < 0] @ vectors[:, values < 0].conj().T
        samples.append(np.einsum("ij,uji->u", density, operators))
    fd[:, nu] = (samples[0] - samples[1]) / (2 * step)
error("static_response_vs_density_finite_difference", fd, chi_static, 2e-7)

# The four LRI endpoint terms of Sigma versus full tensors and band projection.
x = rng.normal(size=(naux, naux))
wc = -x @ x.T
sigma_full = -np.einsum("uik,vjl,uv,sktl->sitj", full, full, wc, gp)
sigma_terms = []
for left in [endpoint, endpoint.transpose(0, 2, 1)]:
    for right in [endpoint, endpoint.transpose(0, 2, 1)]:
        sigma_terms.append(-np.einsum("uik,vjl,uv,sktl->sitj", left, right, wc, gp))
error("sigma_four_vs_full_fit", sum(sigma_terms), sigma_full)
sigma_band = u.conj().T @ sigma_full.reshape(nao * nspin, nao * nspin) @ u
sigma_band_reference = -np.einsum("unm,m,uv,vmp->np", vertices, gs(e, f, tau), wc, vertices)
error("sigma_AO_vs_band_vertices", sigma_band, sigma_band_reference)
error("code_opposite_G_sign", np.einsum("uik,vjl,uv,sktl->sitj", full, full, wc, -gp), sigma_full)
error("same_center_half_coefficient", 4 * 0.5**2, 1.0)
witness("same_center_double_count", 4 * 1.0**2, 1.0)

# Screening in a noncommuting metric and its covariance under a basis change.
eig, vec = np.linalg.eigh(v)
vh = (vec * np.sqrt(eig)) @ vec.T
x = rng.normal(size=(5, 5))
chi = -x @ x.T
w = np.linalg.solve(np.eye(5) - v @ chi, v)
error("screening_symmetrized", vh @ np.linalg.solve(np.eye(5) - vh @ chi @ vh, vh), w)
error("screening_Dyson_residual", w, v + v @ chi @ w)
witness("wrong_dielectric_order", np.linalg.solve(np.eye(5) - chi @ v, v), w)
a = rng.normal(size=(5, 5)) + 3 * np.eye(5)
ai = np.linalg.inv(a)
vn, chin = a.T @ v @ a, ai @ chi @ ai.T
wn = np.linalg.solve(np.eye(5) - vn @ chin, vn)
error("auxiliary_basis_covariance", wn, a.T @ w @ a, 2e-10)
old_log = np.linalg.slogdet(np.eye(5) - v @ chi)[1] + np.trace(v @ chi)
new_log = np.linalg.slogdet(np.eye(5) - vn @ chin)[1] + np.trace(vn @ chin)
error("trace_log_basis_invariance", new_log, old_log, 2e-10)
lnodes, lweights = np.polynomial.legendre.leggauss(180)
coupling_result = 0.0
for lam, weight_lam in zip((lnodes+1)/2, lweights/2):
    reducible = np.linalg.solve(np.eye(5)-lam*chi@v, chi)
    coupling_result -= weight_lam*np.trace(v@(reducible-chi))
error("RPA_coupling_integral_vs_trace_log", coupling_result, old_log, 2e-10)

# A three-cell BvK construction independently fixes vertex phases and 1/N.
nc, no, npaux = 3, 2, 2
ks = 2 * np.pi * np.arange(nc) / nc
ck = [unitary(no) for _ in ks]
ek = np.array([[-1.2, 0.6], [-0.9, 0.8], [-1.0, 1.1]])
raw = rng.normal(size=(npaux, no, no, nc))
for mu in range(npaux):
    raw[mu, 1 - mu, :, :] = 0  # auxiliary center equals first AO center
end_sc = np.zeros((nc * npaux, nc * no, nc * no))
for r in range(nc):
    for mu in range(npaux):
        for i in range(no):
            for j in range(no):
                for dr in range(nc):
                    end_sc[r*npaux+mu, r*no+i, ((r+dr)%nc)*no+j] += raw[mu, i, j, dr]
full_sc = end_sc + end_sc.transpose(0, 2, 1)
psi = np.zeros((nc * no, nc * no), complex)
for ik, k in enumerate(ks):
    for r in range(nc):
        psi[r*no:(r+1)*no, ik*no:(ik+1)*no] = np.exp(1j*k*r) * ck[ik] / np.sqrt(nc)
d_sc = np.array([psi.conj().T @ t @ psi for t in full_sc])
ep = ek.ravel()
fp = (ep < 0).astype(float)
factor = (fp[:, None] - fp[None, :]) / (1j * omega + ep[:, None] - ep[None, :])
chi_sc = np.einsum("umn,vmn,mn->uv", d_sc, d_sc.conj(), factor)
phase_error = 0.0
normalization_error = 0.0
for iq, q in enumerate(ks):
    chi_q = np.zeros((npaux, npaux), complex)
    for ik, k in enumerate(ks):
        jk = (ik + iq) % nc
        for m in range(no):
            for n in range(no):
                vertex = np.zeros(npaux, complex)
                for mu in range(npaux):
                    for i in range(no):
                        for j in range(no):
                            for dr in range(nc):
                                vertex[mu] += raw[mu, i, j, dr] * (
                                    ck[ik][i,m].conj()*ck[jk][j,n]*np.exp(1j*(k+q)*dr)
                                    + ck[ik][j,m].conj()*ck[jk][i,n]*np.exp(-1j*k*dr))
                phase_error = max(phase_error, np.max(np.abs(vertex - nc*d_sc[:npaux, ik*no+m, jk*no+n])))
                coeff = ((ek[ik,m] < 0)*1.0 - (ek[jk,n] < 0)*1.0) / (1j*omega + ek[ik,m] - ek[jk,n])
                chi_q += coeff * np.outer(vertex, vertex.conj()) / nc
    from_realspace = sum(np.exp(1j*q*r) * chi_sc[:npaux, r*npaux:(r+1)*npaux] for r in range(nc))
    normalization_error = max(normalization_error, np.max(np.abs(chi_q - from_realspace)))
error("periodic_vertex_vs_explicit_BvK", phase_error, 0.0)
error("periodic_response_normalization", normalization_error, 0.0)

# Restore every lattice displacement explicitly, independently of full tensors.
gp_sc = psi @ np.diag(gs(ep, fp, tau)) @ psi.conj().T
gm_sc = psi @ np.diag(gs(ep, fp, -tau)) @ psi.conj().T
gpr = np.array([gp_sc[:no, r*no:(r+1)*no] for r in range(nc)])
gmr = np.array([gm_sc[:no, r*no:(r+1)*no] for r in range(nc)])
chi_tau_sc = np.einsum("uik,vjl,ij,lk->uv", full_sc, full_sc, gp_sc, gm_sc)
chi_translated = np.zeros((nc, npaux, npaux), complex)
for r in range(nc):
    for mu in range(npaux):
        for nu in range(npaux):
            i, j = mu, nu  # one AO and one ABF on each primitive-cell atom
            for r1 in range(nc):
                for r2 in range(nc):
                    for k in range(no):
                        for l in range(no):
                            chi_translated[r,mu,nu] += raw[mu,i,k,r1]*raw[nu,j,l,(r2-r)%nc]*(
                                gpr[r,i,j]*gmr[(r1-r2)%nc,l,k]
                                +gpr[r2,i,l]*gmr[(r1-r)%nc,j,k]
                                +gpr[(r2-r1)%nc,k,l]*gmr[-r%nc,j,i]
                                +gpr[(r-r1)%nc,k,j]*gmr[-r2%nc,l,i])
error("translated_response_four_terms", chi_translated,
      np.array([chi_tau_sc[:npaux,r*npaux:(r+1)*npaux] for r in range(nc)]))

x = rng.normal(size=(npaux,npaux))
wq0 = -x @ x.T
x = rng.normal(size=(npaux,npaux)) + 1j*rng.normal(size=(npaux,npaux))
wq1 = -x @ x.conj().T
wq = np.array([wq0, wq1, wq1.conj()])
wr = np.array([sum(np.exp(-1j*q*r)*wq[iq] for iq,q in enumerate(ks))/nc for r in range(nc)])
w_sc = np.block([[wr[(rb-ra)%nc] for rb in range(nc)] for ra in range(nc)])
sigma_sc = -np.einsum("uik,vjl,uv,kl->ij", full_sc, full_sc, w_sc, gp_sc)
sigma_translated = np.zeros((nc,no,no),complex)
for r in range(nc):
    for i in range(no):
        for j in range(no):
            for r1 in range(nc):
                for r2 in range(nc):
                    for k in range(no):
                        for l in range(no):
                            ci = raw[:,i,k,r1]
                            ck_rev = raw[:,k,i,-r1%nc]
                            cj = raw[:,j,l,(r2-r)%nc]
                            cl_rev = raw[:,l,j,(r-r2)%nc]
                            bracket = (ci @ wr[r] @ cj + ci @ wr[r2] @ cl_rev
                                       + ck_rev @ wr[(r-r1)%nc] @ cj
                                       + ck_rev @ wr[(r2-r1)%nc] @ cl_rev)
                            sigma_translated[r,i,j] -= gpr[(r2-r1)%nc,k,l]*bracket
error("translated_sigma_four_terms", sigma_translated,
      np.array([sigma_sc[:no,r*no:(r+1)*no] for r in range(nc)]))

# Periodic band self-energy at fixed tau checks G25's spatial convolution.
sigma_band_sc = np.diag(psi.conj().T @ sigma_sc @ psi)
sigma_band_q = np.zeros(nc*no,complex)
for ik in range(nc):
    for n in range(no):
        for iq in range(nc):
            internal_k = (ik-iq)%nc
            for m in range(no):
                vertex = nc*d_sc[:npaux,internal_k*no+m,ik*no+n]
                sigma_band_q[ik*no+n] -= (gs(ek[internal_k],(ek[internal_k]<0).astype(float),tau)[m]
                                         * (vertex.conj() @ wq[iq] @ vertex) / nc)
error("periodic_sigma_band_convolution", sigma_band_q, sigma_band_sc)

# A one-pole retarded model distinguishes nonlinear and linearized QP energies.
epsilon, chemical, constant, strength, pole = 0.1, 0.3, 0.02, 0.04, 1.2
roots = np.roots([1, -(epsilon + constant + chemical + pole),
                  (epsilon + constant)*(chemical + pole) - strength])
qp = roots[np.argmin(abs(roots - epsilon))]  # selection specific to this toy
residual = qp - epsilon - constant - strength/(qp - chemical - pole)
error("nonlinear_QP_residual", residual, 0.0)
zfactor = 1/(1 + strength/(epsilon - chemical - pole)**2)
linear = epsilon + zfactor*(constant + strength/(epsilon - chemical - pole))
witness("QP_linearization_is_an_approximation", linear, qp, 1e-7)
witness("QP_wrong_energy_zero", qp-epsilon-constant-strength/(qp-pole), 0.0)

print(json.dumps({"scope": "finite algebra controls; synthetic inputs; no LibRI/LibRPA execution",
                  "results": results}, indent=2))
